from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

geolocator = Nominatim(user_agent="tz_lookup")
tf = TimezoneFinder()

def get_timezone(country: str, city: str) -> str | None:
    # 拼接成完整地址
    query = f"{city}, {country}"

    # 1. 地理编码：获取经纬度
    location = geolocator.geocode(query)
    if not location:
        return None

    # 2. 经纬度 → 时区
    tz = tf.timezone_at(lng=location.longitude, lat=location.latitude)
    return tz