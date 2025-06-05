# 标准库
import subprocess

# 第三方库
from pyrogram import filters, Client
from pyrogram.types import Message

# 自定义模块
from config.config import MY_TGID
from libs.log import logger



# 监听来自指定TG用户的 /update 命令
@Client.on_message(filters.chat(MY_TGID) & filters.command("update"))
async def update_tg_bot(client: Client, message: Message):
    # 回复用户，提示正在检测更新
    reply_message = await message.reply("开始更新...")

    try:
        # 执行 bash update 脚本，捕获输出
        result = subprocess.run(["bash", "update"], capture_output=True, text=True)
    except Exception as e:
        # 捕获异常并记录日志
        await reply_message.edit(f"执行更新脚本时出错: {e}")
        logger.error(f"执行更新脚本时出错: {e}")
        return

    if result.returncode == 0:
        # 更新成功，输出脚本标准输出内容
        await reply_message.edit(result.stdout)
        try:
            # 重启 supervisor 管理的 main 服务
            subprocess.run(["supervisorctl", "restart", "main"])
        except Exception as e:
            await message.reply(f"重启服务时出错: {e}")
            logger.error(f"重启服务时出错: {e}")
    else:
        # 更新失败，输出脚本标准输出内容，并记录标准错误
        await reply_message.edit(result.stdout)
        logger.error(f"更新失败: {result.stderr}")


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