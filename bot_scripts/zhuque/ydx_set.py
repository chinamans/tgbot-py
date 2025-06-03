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
            "❌ 参数不足。\n"
            "用法：`/ydx dice_reveal|dice_bet|start_count|stop_count|start_bouns|bet_model on|off|num|a|b`"
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
