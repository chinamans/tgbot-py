# 第三方库
from pyrogram import filters, Client
from pyrogram.types import Message

# 自定义模块
from config.config import MY_TGID
from libs.state import state_manager


@Client.on_message(filters.chat(MY_TGID) & filters.command(["cookie", "xcsrf"]))
async def notification_switch(client: Client, message: Message):
    """
    控制调度任务的开关（如自动释放技能、自动更改昵称）。
    用法: /cookie website str  /xcsrf website str 
    """

    if len(message.command) < 3:
        await message.reply(
            "❌ 参数不足。\n用法：\n"
            "/cookie website str"
            "/xcsrf website str "
        )
        return

    command = message.command[0].lower().lstrip('/')
    website = message.command[1].lower()
    action = message.command[2]

    valid_websites = {"zhuque", "audiences", "ptvicomo", "hddolby", "redleaves", "springsunday", "u2dmhy"}

    # 检查网站名是否合法
    if website not in valid_websites:
        site_list = ', '.join(sorted(valid_websites))
        await message.reply(f"❌ 参数非法。\n有效网站：`{site_list}`")
        return

    # 应用设置

    header = website.upper()
    state_manager.set_section(header, {command: action})
    await message.reply(f"`{website} 站点的 {command}` 已设定为 {action}")
       