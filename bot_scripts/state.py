# 标准库
from pathlib import Path

# 第三方库
from pyrogram import filters, Client
from pyrogram.types import Message

# 自定义模块
from config.config import MY_TGID
from libs.state import state_manager
from libs.toml_images import toml_file_to_image
from libs.sys_info import system_version_get


# 监听来自指定TG用户的 /state 命令
@Client.on_message(filters.chat(MY_TGID) & filters.command("configstate"))
async def configstate(client: Client, message: Message):
    image = await toml_file_to_image("config/state.toml")
    await message.reply_photo(image)
    Path(image).unlink()


# 监听来自指定TG用户的 /state 命令
@Client.on_message(filters.chat(MY_TGID) & filters.command("sysstate"))
async def sysstate(client: Client, message: Message):
    project_name, tgbot_sate = await system_version_get()
    await message.reply(tgbot_sate)


@Client.on_message(filters.chat(MY_TGID) & filters.command("err"))
async def sysstate(client: Client, message: Message):
    await client.send_message(-999999999999, "测试 custom_invoke 错误捕获")
