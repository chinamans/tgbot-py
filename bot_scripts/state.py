from pyrogram import filters, Client
from pyrogram.types import Message
from config.config import MY_TGID
from libs.state import state_manager


# 监听来自指定TG用户的 /state 命令
@Client.on_message(filters.chat(MY_TGID) & filters.command("state"))
async def state(client: Client, message: Message):
    await message.reply(str(state_manager.state))
