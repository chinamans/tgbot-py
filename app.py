# 标准库
import asyncio
import os
import json
from pathlib import Path
import sys
import traceback

# 第三方库
from pyrogram import Client as _Client, idle
from pyrogram.errors import (
    RPCError,
    FloodWait,
    Unauthorized,
    AuthKeyInvalid,
)
from pyrogram.raw.core import TLObject

# 自定义模块
from config.config import API_HASH, API_ID, BOT_TOKEN, PT_GROUP_ID, proxy_set
from libs.log import logger
from libs.sys_info import system_version_get
from models import create_all, async_engine
from models.alter_tables import alter_columns
from schedulers import scheduler, start_scheduler


class Client(_Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def invoke(self, query: TLObject, *args, max_retries: int = 3, **kwargs):
        """
        重写 invoke 方法，捕获特定错误并触发 Supervisor 重启。
        """
        retries = 0
        while retries < max_retries:
            try:
                logger.debug(
                    f"Invoking {query.__class__.__name__} (Attempt {retries + 1}/{max_retries})"
                )
                response = await super().invoke(query, *args, **kwargs)
                logger.info(f"Request {query.__class__.__name__} succeeded")
                return response
            except FloodWait as e:
                wait_time = e.value
                logger.warning(
                    f"FloodWait: Waiting {wait_time} seconds for {query.__class__.__name__}"
                )
                await asyncio.sleep(wait_time)
                retries += 1
            except TimeoutError as e:
                logger.error(
                    f"TimeoutError for {query.__class__.__name__}: {traceback.format_exc()}"
                )
                await asyncio.sleep(1)  # 避免快速重试
                retries += 1
            except RPCError as e:
                logger.error(
                    f"RPCError for {query.__class__.__name__}: {traceback.format_exc()}"
                )
                # 某些错误不应重试，直接抛出
                if isinstance(e, (Unauthorized, AuthKeyInvalid)):
                    raise
                await asyncio.sleep(1)
                retries += 1
            except Exception as e:
                logger.error(
                    f"Unexpected error for {query.__class__.__name__}: {traceback.format_exc()}"
                )
                raise  # 不重试未知错误

        logger.critical(
            f"Max retries ({max_retries}) exceeded for {query.__class__.__name__}. Triggering Supervisor restart."
        )
        try:
            # 尝试关闭会话
            await self.stop()
        except Exception as e:
            logger.error(f"Failed to stop session: {traceback.format_exc()}")
        sys.exit(1)  # 触发 Supervisor 重启


user_app_terminated = False
user_app: Client = None
bot_app: Client = None

if proxy_set["proxy_enable"] == True:
    proxy = proxy_set["proxy"]
else:
    proxy = None


async def start_app():
    db_flag_path = Path("db_file/dbflag/dbflag.json")
    db_flag_path.parent.mkdir(parents=True, exist_ok=True)
    workdir_path = Path("sessions")
    workdir_path.mkdir(parents=True, exist_ok=True)

    global user_app, bot_app

    user_app = Client(
        "user_account",
        api_id=API_ID,
        api_hash=API_HASH,
        workdir=str(workdir_path.resolve()),
        proxy=proxy,
        plugins=dict(root="user_scripts"),
    )
    bot_app = Client(
        "bot_account",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        workdir=str(workdir_path.resolve()),
        proxy=proxy,
        plugins=dict(root="bot_scripts"),
    )

    project_name, tgbot_sate = await system_version_get()
    logger.info(f"开始尝试启动 {project_name} 监听程序")

    try:
        await user_app.start()
    except Exception as e:
        logger.critical("user_app 启动失败: %s", e)
        return
    try:
        from bot_scripts.setup import setup_commands

        await bot_app.start()
        await setup_commands()
    except Exception as e:
        logger.critical("bot_app 启动失败: %s", e)
        return
    db_flag_data = None
    if os.path.exists(db_flag_path):
        try:
            with open(db_flag_path, "r", encoding="utf-8") as f:
                db_flag_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"读取 dbflag.json 失败，将重新初始化数据库：{e}")

    if not db_flag_data or db_flag_data.get("db_flag") != True:
        logger.info("首次运行，初始化数据库...")
        await create_all()
        with open(db_flag_path, "w", encoding="utf-8") as f:
            json.dump(
                {"db_flag": True, "alter_tables": False},
                f,
                indent=4,
                ensure_ascii=False,
            )
    else:
        logger.info("数据库已初始化，跳过初始化。")

    if db_flag_data and db_flag_data.get("alter_tables") == True:
        await alter_columns()

        with open(db_flag_path, "w", encoding="utf-8") as f:
            json.dump(
                {"db_flag": True, "alter_tables": False},
                f,
                indent=4,
                ensure_ascii=False,
            )

    # 启动任务调度和保活任务
    scheduler.start()
    await start_scheduler()
    logger.info(f"{project_name} 监听程序启动成功")

    # 发送版本信息
    re_msg = f"您的{project_name} 项目已登录 状态如下:\n\n" + tgbot_sate
    await bot_app.send_message(PT_GROUP_ID["BOT_MESSAGE_CHAT"], re_msg)
    await idle()  # 等待直到退出
    logger.info(f"开始关闭 {project_name} 监听程序...")
    await async_engine.dispose()
    await user_app.stop()
    logger.info(f"{project_name} 监听程序关闭完成")


def get_user_app():
    global user_app
    return user_app


def get_bot_app():
    global bot_app
    return bot_app
