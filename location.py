"""
location_utils.py

提供 国家 + 城市 → 时区 的可靠查询能力。
支持：
- 本地 SQLite 缓存（避免 geopy 网络依赖）
- 城市别名库（台北市→Taipei、广州→Guangzhou…）
- 城市模糊匹配（NYC、LA、SF…）
- 国家别名库（中国大陆→China、UK→United Kingdom…）
- 国家码支持（CN、US、AU…）
- 地名纠错（Shangahi → Shanghai）
- 经纬度 → IANA 时区
"""

from __future__ import annotations
import sqlite3
import os
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from functools import lru_cache
from difflib import get_close_matches

from zoneinfo import ZoneInfo
from datetime import datetime, timezone

# -----------------------------
# 1. SQLite 缓存
# -----------------------------
DB_PATH = "location_cache.db"

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE cache (
                country TEXT,
                city TEXT,
                lat REAL,
                lng REAL,
                PRIMARY KEY (country, city)
            )
        """)
        conn.commit()
        conn.close()

init_db()


def db_get(country: str, city: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT lat, lng FROM cache WHERE country=? AND city=?", (country, city))
    row = c.fetchone()
    conn.close()
    return row


def db_set(country: str, city: str, lat: float, lng: float):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO cache VALUES (?, ?, ?, ?)", (country, city, lat, lng))
    conn.commit()
    conn.close()


# -----------------------------
# 2. 国家别名库
# -----------------------------
COUNTRY_ALIASES = {
    "中国": "China",
    "中國": "China",
    "中国大陆": "China",
    "大陆": "China",
    "香港": "Hong Kong",
    "澳门": "Macau",
    "台湾": "Taiwan",

    "uk": "United Kingdom",
    "uae": "United Arab Emirates",
    "usa": "United States",
    "us": "United States",

    "cn": "China",
    "tw": "Taiwan",
    "hk": "Hong Kong",
    "mo": "Macau",
    "au": "Australia",
    "jp": "Japan",
    "kr": "South Korea",
    "sg": "Singapore",

    "chn": "China",
    "twn": "Taiwan",
    "hkg": "Hong Kong",
    "mac": "Macau",
    "usa": "United States",
    "aus": "Australia",
    "jpn": "Japan",
    "kor": "South Korea",
    "sgp": "Singapore",
}


# -----------------------------
# 3. 城市别名库
# -----------------------------
CITY_ALIASES = {
    "台北市": "Taipei",
    "臺北市": "Taipei",
    "台北": "Taipei",
    "臺北": "Taipei",
    "广州": "Guangzhou",
    "廣州": "Guangzhou",
    "纽约": "New York",
    "紐約": "New York",
    "洛杉矶": "Los Angeles",
    "洛杉磯": "Los Angeles",
    "旧金山": "San Francisco",
    "舊金山": "San Francisco",

    "nyc": "New York",
    "la": "Los Angeles",
    "sf": "San Francisco",
    "ldn": "London",
    "ams": "Amsterdam",
    "sg": "Singapore",
}


# -----------------------------
# 4. 模糊匹配词典
# -----------------------------
FUZZY_DICT = {
    "ny": "New York",
    "la": "Los Angeles",
    "sf": "San Francisco",
    "tokyo": "Tokyo",
    "osaka": "Osaka",
}


# -----------------------------
# 5. 地名纠错词典（可扩展）
# -----------------------------
CITY_DICTIONARY = [
    "Shanghai", "Beijing", "Guangzhou", "Shenzhen",
    "New York", "Los Angeles", "San Francisco",
    "London", "Paris", "Tokyo", "Osaka", "Singapore",
    "Sydney", "Melbourne"
]


def correct_spelling(city: str) -> str:
    matches = get_close_matches(city, CITY_DICTIONARY, n=1, cutoff=0.75)
    return matches[0] if matches else city


# -----------------------------
# 国家默认城市（可扩展）
# -----------------------------
COUNTRY_DEFAULT_CITY = {
    "China": "Beijing",
    "United States": "Washington",
    "United Kingdom": "London",
    "Australia": "Sydney",
    "Japan": "Tokyo",
    "South Korea": "Seoul",
    "Singapore": "Singapore",
    "Canada": "Ottawa",
    "Germany": "Berlin",
    "France": "Paris",
}


# -----------------------------
# 6. 主类
# -----------------------------
class LocationUtils:
    def __init__(self, user_agent: str = "location_utils"):
        self.geolocator = Nominatim(user_agent=user_agent)
        self.tz_finder = TimezoneFinder()

    def normalize_country(self, country: str) -> str:
        c = country.strip().lower()
        return COUNTRY_ALIASES.get(c, country.title())

    def normalize_city(self, city: str) -> str:
        c = city.strip().lower()

        if c in CITY_ALIASES:
            return CITY_ALIASES[c]

        if c in FUZZY_DICT:
            return FUZZY_DICT[c]

        # 自动纠错
        corrected = correct_spelling(city.title())
        return corrected

    @lru_cache(maxsize=512)
    def geocode(self, country: str, city: str):
        country_norm = self.normalize_country(country)
        city_norm = self.normalize_city(city)

        # 1. 尝试本地缓存
        cached = db_get(country_norm, city_norm)
        if cached:
            lat, lng = cached
            return lat, lng

        # 2. geopy 查询
        query = f"{city_norm}, {country_norm}"
        try:
            loc = self.geolocator.geocode(query)
        except Exception:
            return None

        if not loc:
            return None

        # 自动学习 geopy 返回的城市名
        if hasattr(loc, "raw") and "display_name" in loc.raw:
            # geopy 的 display_name 通常格式： "Shanghai, China"
            geopy_city = loc.raw["display_name"].split(",")[0]
            self.learn_city_name(city_norm, geopy_city)

        # 3. 写入缓存
        db_set(country_norm, city_norm, loc.latitude, loc.longitude)
        return loc.latitude, loc.longitude

    '''
    def get_timezone(self, country: str, city: str) -> str | None:
        result = self.geocode(country, city)
        if not result:
            return None

        lat, lng = result
        return self.tz_finder.timezone_at(lat=lat, lng=lng)
    '''

    def get_timezone(self, country: str, city: str | None = None) -> str | None:
        country_norm = self.normalize_country(country)

        # 国家级 fallback：只输入国家时自动使用默认城市
        if not city:
            if country_norm in COUNTRY_DEFAULT_CITY:
                city = COUNTRY_DEFAULT_CITY[country_norm]
            else:
                return None  # 没有默认城市就返回 None

        result = self.geocode(country_norm, city)
        if not result:
            return None

        lat, lng = result
        return self.tz_finder.timezone_at(lat=lat, lng=lng)

    def get_timezone_by_coord(self, lat: float, lng: float) -> str | None:
        return self.tz_finder.timezone_at(lat=lat, lng=lng)


    def learn_city_name(self, raw_city: str, geopy_city: str):
        """
        自动学习 geopy 返回的标准城市名
        """
        raw = raw_city.strip().title()
        std = geopy_city.strip().title()

        if std not in CITY_DICTIONARY:
            CITY_DICTIONARY.append(std)

        # 也把用户输入加入映射（避免下次重复纠错）
        if raw not in CITY_DICTIONARY:
            CITY_DICTIONARY.append(raw)

    def get_offset_by_timezone(self, tz_name: str, dt: datetime | None = None) -> str | None:
        if dt is None:
            dt = datetime.now(timezone.utc)

        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            return None

        local_dt = dt.astimezone(tz)
        offset = local_dt.utcoffset()
        if offset is None:
            return None

        minutes = int(offset.total_seconds() // 60)
        sign = "+" if minutes >= 0 else "-"
        minutes = abs(minutes)
        h = minutes // 60
        m = minutes % 60
        return f"{sign}{h:02d}:{m:02d}"

    def get_offset_from_utc_and_tz(utc_str: str, tz_name: str) -> str:
        """
        根据 UTC 时间字符串和时区名，返回该时区在该时间点的 offset（如 +08:00 或 -04:00）
        自动处理夏令时。
        """
        # 1. 解析 UTC 字符串
        if utc_str.endswith("Z"):
            utc_str = utc_str[:-1] + "+00:00"
        dt_utc = datetime.fromisoformat(utc_str)

        # 2. 转换到目标时区
        tz = ZoneInfo(tz_name)
        dt_local = dt_utc.astimezone(tz)

        # 3. 获取 offset
        offset = dt_local.utcoffset()
        total_minutes = int(offset.total_seconds() // 60)

        # 4. 格式化
        sign = "+" if total_minutes >= 0 else "-"
        total_minutes = abs(total_minutes)
        h = total_minutes // 60
        m = total_minutes % 60
        return f"{sign}{h:02d}:{m:02d}"


location_utils = LocationUtils()
