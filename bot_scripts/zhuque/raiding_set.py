# 第三方库
from pyrogram import filters, Client
from pyrogram.types import Message

# 自定义模块
from config.config import MY_TGID
from libs import others
from libs.state import state_manager


@Client.on_message(filters.chat(MY_TGID) & filters.command("fanda"))
async def zhuque_fanda_switch(client: Client, message: Message):

    """
    自动反打开关监听
    用法：/fanda lose | win | all | off
    """
    if len(message.command) < 2:
        await message.reply("❌ 参数不足。\n用法：`/fanda lose|win|all|off`")
        return
    action = message.command[1].lower()
    valid_modes = {"lose", "win", "all", "off"}

    if action not in valid_modes:
        await message.reply("❌ 参数非法。\n有效选项：`lose` `win` `all` `off`")
        return
    state_manager.set_section("ZHUQUE", {"fanda": action})
    if action == "off":
        await message.reply("🛑 自动反打已关闭")
    else:
        await message.reply(f"✅ 自动反打模式 `{action}` 已开启")
        



@Client.on_message(filters.chat(MY_TGID) & filters.command("fanxian"))
async def zhuque_dajiefanxian_switch(client: Client, message: Message):
    """
    自动返现开关监听
    """
    if len(message.command) < 2:
        await message.reply("参数不足。用法：`/fanxian on/off`")
        return
    action = message.command[1].lower()
    if action not in ("on", "off"):
        await message.reply("无效参数。请使用 `on` 或 `off`")
        return
    enable = action == "on"
    status = "启动" if enable else "停止"
    state_manager.set_section("ZHUQUE",{"fanxian": action})
    
    await message.reply(f"打劫返现功能已 {status}！")
