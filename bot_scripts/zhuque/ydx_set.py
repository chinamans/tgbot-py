# 第三方库
from pyrogram import filters, Client
from pyrogram.types import Message

# 自定义模块
from config.config import MY_TGID
from libs import others
from libs.state import state_manager

@Client.on_message(filters.chat(MY_TGID) & filters.command("ydx"))
async def zhuque_fanda_switch(client: Client, message: Message):
    """
    设置朱雀相关功能模块的开关或模式
    用法：/ydx <command> <action>
    示例：/ydx dice_bet a
    """
    if len(message.command) < 3:
        await message.reply(
            f"❌ 参数不足。\n"
            f"用法："
            f"\n/ydx dice_reveal on|off 结果记录开关" 
            f"\n/ydx dice_bet on|off    自动下注开关"
            f"\n/ydx start_count num    设置第几连开始下注"
            f"\n/ydx stop_count num     设置连续下注几局没赢停止本次倍投"
            f"\n/ydx start_bouns num    起手倍投金额"
            f"\n/ydx bet_model a|b      下注模式 a:返投模式 b:首投随机连续两输再次随机"
        )
        return

    command = message.command[1].lower()
    action = message.command[2].lower()

    command_modes = {
        "dice_reveal": {"on", "off"},
        "dice_bet": {"on", "off"},
        "start_count": "number",
        "stop_count": "number",
        "start_bouns": "number",
        "bet_model": {"a", "b"},
    }

    if command not in command_modes:
        valid_cmds = ', '.join(sorted(command_modes))
        await message.reply(f"❌ 无效命令。\n有效命令有：`{valid_cmds}`")
        return

    valid_actions = command_modes[command]
    if valid_actions == "number":
        if not action.isdigit():
            await message.reply(f"❌ 非法参数。`{command}` 命令要求参数为数字")
            return
    elif action not in valid_actions:
        opts = ', '.join(valid_actions)
        await message.reply(f"❌ 非法参数。`{command}` 命令有效选项为：{opts}")
        return

    state_manager.set_section("ZHUQUE", {f"ydx_{command}": action})
    await message.reply(f"`{command}` 已设置为 `{action}` ✅")
