from pathlib import Path
from pyrogram import filters, Client
from pyrogram.types import Message
from config.config import MY_TGID
from libs.state import state_manager
from libs.toml_images import toml_file_to_image


# 监听来自指定TG用户的 /state 命令
@Client.on_message(filters.chat(MY_TGID) & filters.command("state"))
async def state(client: Client, message: Message):
    image = await toml_file_to_image("config/state.toml")
    await message.reply_photo(image)
    Path(image).unlink() 
