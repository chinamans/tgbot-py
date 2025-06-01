#标准库
from decimal import Decimal

#第三方库
from pyrogram import filters, Client
from pyrogram.types import Message

#自定模块
from libs.state import state_manager
from filters import custom_filters
from libs.transform_dispatch import transform




TARGET = [-1001833464786, -1002262543959]
SITE_NAME = "zhuque"
BONUS_NAME = "灵石"


###################收到他人的灵石转入##################################
@Client.on_message(
    filters.chat(TARGET)
    & custom_filters.zhuque_bot
    & custom_filters.command_to_me
    & filters.regex(r"转账成功, 信息如下: \n.+ 转出 (\d+)\n")
)
async def zhuque_transform_get(client: Client, message: Message):
    bonus = message.matches[0].group(1)
    transform_message = message.reply_to_message
    leaderboard = state_manager.get_item(SITE_NAME.upper(),"leaderboard","off")   
    notification = state_manager.get_item(SITE_NAME.upper(),"notification","off")
   
    await transform(
        transform_message,
        Decimal(f"{bonus}"),
        SITE_NAME, BONUS_NAME,
        "get",
        leaderboard,
        "off",
        notification
    )

###################转出灵石给他人##################################
@Client.on_message(
    filters.chat(TARGET)
    & custom_filters.zhuque_bot
    & custom_filters.reply_to_me
    & filters.regex(r"转账成功, 信息如下: \n.+ 转出 (\d+)\n")
)
async def zhuque_transform_pay(client: Client, message: Message):
    bonus = message.matches[0].group(1)
    transform_message = message.reply_to_message.reply_to_message
    payleaderboard = state_manager.get_item(SITE_NAME.upper(),"payleaderboard","off")
    notification = state_manager.get_item(SITE_NAME.upper(),"notification","off")

    await transform(
        transform_message,
        Decimal(f"-{bonus}"),
        SITE_NAME, BONUS_NAME,
        "pay",
        "off",
        payleaderboard,
        notification
    )
