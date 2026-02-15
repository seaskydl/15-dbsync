import sys
import time

def print_progress(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    # 使用 \r 将光标移回行首，实现原地刷新
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()

total_items = 100
print("开始处理...")
for i in range(total_items):
    # 打印第一行进度条
    print_progress(i + 1, total_items, prefix='任务A:', suffix='完成', length=30)
    time.sleep(0.05)
    # 打印第二行日志（需要手动换行）
    if (i + 1) % 20 == 0:
        sys.stdout.write('\n') # 换行到新行
        print(f"  ---> 打印了第 {(i+1)//20} 条日志")
        # 注意：在新行打印内容后，你可能需要重新打印第一行进度条，或者让其在下一轮循环中覆盖
print("\n处理完成！")
