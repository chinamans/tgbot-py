# 标准库
import re

# 第三方库
from pyrogram import filters, Client
from pyrogram.types import Message

# 自定义模块
from config.config import MY_TGID
from libs import others
from libs.state import state_manager



@Client.on_message(filters.chat(MY_TGID) & filters.command("ssd_click"))
async def ssd_click_switch(client: Client, message: Message):
    """
    ssd 转账确认按钮自动点击
    用法：/ssd_click once | 5min | off
    """
    if len(message.command) < 2:
        await message.reply("❌ 参数不足。\n用法：`/ssd_click once | 5min | off`")
        return

    action = message.command[1].lower()
    valid_modes = {
        "once": "✅ 转账一次确认按钮启动",
        "5min": "✅ 转账5分钟按钮确认启动",
        "off": "🛑 转账自动确认已关闭"
    }

    if action not in valid_modes:
        await message.reply("❌ 参数非法。\n有效选项：once, 5min, off")
        return

    state_manager.set_section("SPRINGSUNDAY", {"ssd_click": action})
    await message.reply(valid_modes[action])

        