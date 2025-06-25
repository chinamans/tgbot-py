# 标准库
import json
import subprocess
from enum import auto

# 第三方库
from pyrogram import filters, Client
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


# 自定义模块
from config.config import MY_TGID
from libs.inline_buttons import InlineButton, Method
from libs.log import logger
from libs.async_bash import bash
from filters.custom_filters import CallbackDataFromFilter


# # 监听来自指定TG用户的 /update 命令
# @Client.on_message(filters.chat(MY_TGID) & filters.command("update"))
# async def update_tg_bot(client: Client, message: Message):
#     # 回复用户，提示正在检测更新
#     reply_message = await message.reply("开始更新...")

#     try:
#         # 执行 bash update 脚本，捕获输出
#         result = subprocess.run(["bash", "update"], capture_output=True, text=True)
#     except Exception as e:
#         # 捕获异常并记录日志
#         await reply_message.edit(f"执行更新脚本时出错: {e}")
#         logger.error(f"执行更新脚本时出错: {e}")
#         return

#     if result.returncode == 0:
#         # 更新成功，输出脚本标准输出内容
#         await reply_message.edit(result.stdout)
#         try:
#             # 重启 supervisor 管理的 main 服务
#             subprocess.run(["supervisorctl", "restart", "main"])
#         except Exception as e:
#             await message.reply(f"重启服务时出错: {e}")
#             logger.error(f"重启服务时出错: {e}")
#     else:
#         # 更新失败，输出脚本标准输出内容，并记录标准错误
#         await reply_message.edit(result.stdout)
#         logger.error(f"更新失败: {result.stderr}")


@Client.on_message(filters.chat(MY_TGID) & filters.command("restart"))
async def restart_tg_bot(client: Client, message: Message):
    # 回复用户，提示正在检测更新
    reply_message = await message.reply("开始重启")

    try:
        # 重启 supervisor 管理的 main 服务
        subprocess.run(["supervisorctl", "restart", "main"])
    except Exception as e:
        await message.reply(f"重启服务时出错: {e}")
        logger.error(f"重启服务时出错: {e}")


tags = None


@Client.on_message(filters.chat(MY_TGID) & filters.command("update"))
async def update_tg_bot(client: Client, message: Message):
    global tags
    await bash("git reset --hard")
    await bash("git fetch --prune --prune-tags origin")
    tags = ["origin/main"] + (await bash("git tag --sort=-creatordate")).split("\n")
    tags = tags[:6]
    one_line_count = 2
    keyboard = [
        [
            InlineKeyboardButton(
                tags[i + j], json.dumps({"f": "s", "c": i + j, "a": "update"})
            )
            for j in range(one_line_count)
            if i + j < len(tags)
        ]
        for i in range(0, len(tags), one_line_count)
    ]
    keyboard.append(
        [
            InlineKeyboardButton(
                "关闭",
                callback_data=json.dumps({"f": "close", "a": "update"}),
            )
        ]
    )
    await message.reply("请选择版本", reply_markup=InlineKeyboardMarkup(keyboard))


@Client.on_callback_query(CallbackDataFromFilter("update"))
async def ydx_set_callback(client: Client, callback_query: CallbackQuery):
    global tags
    data: dict = json.loads(callback_query.data)
    count = data.get("c", None)
    ret = "开始更新..."
    await callback_query.message.edit(ret)
    stdout = await bash(f"git checkout {tags[count]}")
    if stdout.startswith("Previous HEAD"):
        ret += f"\n✅ 更新到新版本：{tags[count]}"
        await callback_query.message.edit(ret)
        await bash("pip install -r requirements.txt")
        ret += f"\n✅ 依赖安装成功\n⏱️ 等待重启..."
        await callback_query.message.edit(ret)
        await bash("supervisorctl restart main")
    else:
        ret += f"\n✅ 您的版本未变化"
        await callback_query.message.edit(ret)
