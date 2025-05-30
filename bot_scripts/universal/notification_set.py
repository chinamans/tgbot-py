import re
from pyrogram import filters, Client
from pyrogram.types import Message

from config.config import MY_TGID
from libs import others
from libs.state import state_manager

@Client.on_message(filters.chat(MY_TGID) & filters.command(["leaderboard", "payleaderboard","notification"]))
async def notification_switch(client: Client, message: Message):
    """
    控制调度任务的开关（如自动释放技能、自动更改昵称）。
    用法: /leaderboard website|all on|off 或 /payleaderboard website|all on|off 或 /notification website|all on|off
    """

    if len(message.command) < 3:
        await message.reply(
            "❌ 参数不足。\n用法：\n"
            "/leaderboard website|all on|off"
            "/payleaderboard website|all on|off"
            "/notification website|all on|off"
        )
        return

    command = message.command[0].lower().lstrip('/')
    website = message.command[1].lower()
    action = message.command[2].lower()

    valid_modes = {"on", "off"}
    valid_websites = {"zhuque", "audiences", "ptvicomo", "hddolby", "redleaves", "springsunday"}

    # 检查开关是否合法
    if action not in valid_modes:
        await message.reply("❌ 参数非法。\n有效选项：`on` 或 `off`")
        return

    # 检查网站名是否合法
    if website != "all" and website not in valid_websites:
        site_list = ', '.join(sorted(valid_websites))
        await message.reply(f"❌ 参数非法。\n有效网站：`{site_list}` 或 `all`")
        return

    # 应用设置
    targets = valid_websites if website == "all" else [website]
    for site in targets:
        header = site.upper()
        state_manager.set_section(header, {command: action})

    # 回复确认
    action_text = "已开启 ✅" if action == "on" else "已关闭 🛑"
    site_text = "所有站点" if website == "all" else f"{website}站点"
    await message.reply(f"`{site_text} {command}` 模式 {action_text}")
       