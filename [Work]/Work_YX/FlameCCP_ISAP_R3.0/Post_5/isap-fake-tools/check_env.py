import os
import sys

# 直接检查环境变量
print("环境变量中的POSTGRES_SERVER值:", os.environ.get("POSTGRES_SERVER"))

# 检查是否有其他环境变量被设置
print("\n所有以POSTGRES_开头的环境变量:")
for key, value in os.environ.items():
    if key.startswith("POSTGRES_"):
        print(f"{key}: {value}")

# 检查当前进程的环境变量来源
print("\n当前Python进程的环境变量检查完成")