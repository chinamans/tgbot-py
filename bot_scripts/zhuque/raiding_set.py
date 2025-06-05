# 第三方库
from pyrogram import filters, Client
from pyrogram.types import Message

# 自定义模块
from config.config import MY_TGID
from libs import others
from libs.state import state_manager


header = "ZHUQUE"

@Client.on_message(filters.chat(MY_TGID) & filters.command("dajie"))
async def zhuque_fanda_switch(client: Client, message: Message):
    """
    设置朱雀相关功能模块的开关或模式
    用法：/dajie <command> <action>
    示例：/dajie fanda lose
    """
    if len(message.command) < 3:
        await message.reply(
            f"❌ 参数不足。\n"
            f"用法："
            f"\n/dajie fanda lose|win|all|off   自动反击启用及模式" 
            f"\n/dajie fanxian on|off    被打劫赢时给对方返现模式开关"
            f"\n/dajie probability 1~100    返现触发概率"
              
        )
        return
    command = message.command[1].lower()
    action = message.command[2].lower()
    command_modes = {
        "fanda": {"lose", "win", "all", "off"},
        "fanxian": {"on", "off"},
        "probability": "number",
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

    state_manager.set_section(header, {command: action})
    await message.reply(f"`{command}` 已设置为 `{action}` ✅")


@Client.on_message(filters.chat(MY_TGID) & filters.command("blacklist"))
async def blockyword_add_remove(client: Client, message: Message):
    """
    dajie blacklist TGID      不予返现黑名单"  
    """

    if len(message.command) < 3:
        await message.reply("参数不足。用法：`/blacklist add TGID` 或 `/blacklist remove TGID` ")
        return
    cmd_name = message.command[0].lower()
    action = message.command[1].lower()
    words = message.command[2] 

    if not words.isdigit():
        return
    words = int(words)

      
    fanxian_blacklist = state_manager.get_item(header,"blacklist",[])

    if action in "add" or "remove":
        if action == "add":        
            if words not in fanxian_blacklist:
                fanxian_blacklist.append(words)
        elif action == "remove":
            if words in fanxian_blacklist:
                fanxian_blacklist.remove(words)  

        state_manager.set_section(header, {"blacklist": fanxian_blacklist})

        re_mess=await message.reply(f'黑名单 {words}{action}成功\n当前当前黑名单以下：{fanxian_blacklist}')
    else:
        await message.reply("无效参数。请使用 `add` 或 `remove`")
   
    if re_mess:
        await others.delete_message(re_mess,15)