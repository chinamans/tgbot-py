""" Module to automate message deletion. """

import traceback
import random
from libs.log import logger
from libs import others
from emoji import emojize
from libs.state import state_manager
from pyrogram import filters, Client
from pyrogram.types import Message
from datetime import datetime, timedelta, timezone
from schedulers import scheduler



auto_change_name_init = False

emojis = [chr(i) for i in range(0x1F600, 0x1F637 + 1)]  # 56个表情符号
async def auto_changename_action():
    from app import get_user_app
    user_app = get_user_app()
    try:
        time_cur = (
            datetime.now(timezone.utc)  # 使用 now 方法直接获取 UTC 时间
            .astimezone(timezone(timedelta(hours=8)))  # 转换为东八区时间
            .strftime("%H:%M:%S:%p:%a")  # 格式化输出   
        )

        hour, minu, seco, p, abbwn = time_cur.split(":")        
        # 生成动态后缀
        random_emoji = random.choice(emojis)
        _last_name = f"{random_emoji}{hour}:{minu}"
        await user_app.update_profile(last_name=_last_name)       
        # 验证更新结果
        me = await user_app.get_me()
        if me.last_name != _last_name:
            raise Exception("修改 last_name 失败")
    except Exception as e:
        trac = "\n".join(traceback.format_exception(e))
        logger.info(f"更新失败! \n{trac}")

async def auto_changename_temp():
    changename_switch = state_manager.get_item("SCHEDULER","autochangename","off")
    if changename_switch == 'on':
        if not scheduler.get_job("autochangename"):
            scheduler.add_job(auto_changename_action,"cron", second=0, id="autochangename")
        logger.info(f"自动报时昵称已启用")
    else:
        if scheduler.get_job("autochangename"):
            scheduler.remove_job("autochangename")        
        logger.info(f"自动报时昵称已关闭")