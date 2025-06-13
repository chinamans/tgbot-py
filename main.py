# 前置加速
import sys

if sys.platform != "win32":
    import uvloop

    uvloop.install()

# 标准库
import asyncio

# 自定义模块
from app import start_app


if __name__ == "__main__":
    asyncio.run(start_app())
    print("Connected..", flush=True)
