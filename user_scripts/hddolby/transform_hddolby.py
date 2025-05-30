from decimal import Decimal
from pyrogram import filters, Client
from pyrogram.types import Message
from filters import custom_filters
from libs.transform_dispatch import transform
from libs.state import state_manager

TARGET = [-1002131053667]
SITE_NAME = "hddolby"
BONUS_NAME = "鲸币"



###################收到他人的鲸币转入##################################
@Client.on_message(
        filters.chat(TARGET)
        & filters.regex(r"成功转账(\d+)")
        & custom_filters.hddobly_bot
        & custom_filters.command_to_me        
    )
async def hddolby_transform_get(client:Client, message:Message):    
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


###################转出鲸币给他人##################################
@Client.on_message(
        filters.chat(TARGET)
        & filters.regex(r"成功转账(\d+)")
        & custom_filters.hddobly_bot
        & custom_filters.reply_to_me        
    )
async def hddolby_transform_pay(client:Client, message:Message):
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
             
