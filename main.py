# 标准库
import asyncio

#自定义模块
from app import start_app


if __name__ == "__main__":
    asyncio.run(start_app())
    print('Connected..', flush=True)