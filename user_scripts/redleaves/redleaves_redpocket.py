# 标准库
import asyncio
from random import randint

# 第三方库
from pyrogram import filters, Client
from pyrogram.types import Message

# 自定义模块
from filters import custom_filters
from libs.log import logger



TARGET = [-1001788987573, -1001873711923]
SITE_NAME = "redleaves"
BONUS_NAME = "魔力"

###################红叶抢红包##################################
@Client.on_message(
        filters.chat(TARGET)
        & filters.regex(r"红包(\d+)号")
        & filters.inline_keyboard
        & custom_filters.yyz_bot
    )
async def redleaves_redpocket(client: Client, message: Message):

    redpocket_nuber = message.matches[0].group(1)
    callback_data = f'open_packet_{redpocket_nuber}'
    callback_data = message.reply_markup.inline_keyboard[0][0].callback_data
    logger.info("redleaves:参与红叶第{redpocket_nuber}号红包")
    try:
        await asyncio.sleep(randint(2, 10))
        result_message = await client.request_callback_answer(message.chat.id, message.id,callback_data)
    except:
        logger.info(f"redleaves:红叶第{redpocket_nuber}号红包参与失败")
        pass
