# 标准库
import asyncio
import sys
import traceback

# 第三方库
from pyrogram import Client as _Client
from pyrogram.errors import (
    RPCError,
    FloodWait,
    Unauthorized,
    AuthKeyInvalid,
)

# 自定义模块
from libs.log import logger


class Client(_Client):
    async def start(self, *args, invoke_retries: int = 5, max_pool: int = 10, **kargs):
        """
        重写 start 方法，在会话认证后设置 CustomSession。
        """
        await super().start(*args, **kargs)
        self._invoke_retries = invoke_retries
        self._pool_semaphore = asyncio.Semaphore(max_pool)
        self._session_invoke = self.session.invoke
        self.session.invoke = self._custom_invoke

    async def _custom_invoke(self, query, *args, **kwargs):
        retries = 0
        while retries < self._invoke_retries:
            async with self._pool_semaphore:
                try:
                    logger.debug(
                        f"调用 {query.__class__.__name__} (尝试 {retries + 1}/{self._invoke_retries})"
                    )
                    response = await self._session_invoke(query, *args, **kwargs)
                    logger.debug(f"请求 {query.__class__.__name__} 成功")
                    return response
                except FloodWait as e:
                    wait_time = e.value
                    logger.warning(
                        f"FloodWait: 为 {query.__class__.__name__} 等待 {wait_time} 秒"
                    )
                    await asyncio.sleep(wait_time)
                    retries += 1

                except asyncio.TimeoutError as e:
                    logger.error(f"TimeoutError for {query.__class__.__name__}")
                    traceback.print_exc()
                    await asyncio.sleep(1)
                    retries += 1
                    if retries == self._invoke_retries:
                        raise

                except RPCError as e:
                    logger.error(f"RPCError for {query.__class__.__name__}")
                    traceback.print_exc()
                    if isinstance(e, (Unauthorized, AuthKeyInvalid)):
                        raise
                    await asyncio.sleep(1)
                    retries += 1

                except Exception as e:
                    logger.error(f"意外错误 for {query.__class__.__name__}")
                    traceback.print_exc()
                    raise

        logger.critical(
            f"超过最大重试次数 ({self._invoke_retries}) for {query.__class__.__name__}。触发 Supervisor 重启。"
        )
        sys.exit(1)
