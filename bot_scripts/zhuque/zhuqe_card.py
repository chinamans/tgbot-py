
# 标准库
import aiohttp
import asyncio
import json
import time

# 第三方库
import aiohttp
from pyrogram import filters, Client
from pyrogram.types import Message

# 自定义模块
from libs import others
from libs.log import logger
from libs.state import state_manager
# 系统库

from enum import auto

# 第三方库
from pyrogram import filters, Client
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
)

# 自定义模块
from config.config import MY_TGID
from filters.custom_filters import CallbackDataFromFilter
from libs.inline_buttons import Method, InlineButton, inline_button_callback
from libs.ydx_betmodel import models as bet_models

ACTION = "card"
SITE_NAME = "zhuque"
msg = "朱雀道具卡片回收"


class Backpack(Method):
    card_id_1 = (
        auto(),
        "改名卡",
        "input_card",
        {
            "description": "请输入任意整数",
            "valid_int": [1, 50000000],
        },  # valid_init\length_str
    )
    card_id_2 = (
        auto(),
        "神佑7天卡",
        "input_card",
        {
            "description": "请输入任意整数",
            "valid_int": [1, 50000000],
        },  # valid_init\length_str
    )
    card_id_3 = (
        auto(),
        "邀请卡",
        "input_card",
        {
            "description": "请输入任意整数",
            "valid_int": [1, 50000000],
        },  # valid_init\length_str
    )
    card_id_4 = (
        auto(),
        "释放7天卡",
        "input_card",
        {
            "description": "请输入任意整数",
            "valid_int": [1, 50000000],
        },  # valid_init\length_str
    )



inline_button = InlineButton(SITE_NAME, ACTION, msg)


async def main_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                await inline_button.create_button(Backpack.card_id_1),
                await inline_button.create_button(Backpack.card_id_2),
            ],
            [
                await inline_button.create_button(Backpack.card_id_3),
                await inline_button.create_button(Backpack.card_id_4),
            ],
            [inline_button.close_button()],
        ]
    )


inline_button.set_main_keyboard(main_keyboard)


@Client.on_message(filters.chat(MY_TGID) & filters.command(ACTION))
async def backpack_card(_, message: Message):
    await message.reply(inline_button.main_message(), reply_markup=await main_keyboard())


@Client.on_callback_query(CallbackDataFromFilter(ACTION))
async def backpack_card_count(client: Client, callback_query: CallbackQuery):
    return await inline_button_callback(client, callback_query, inline_button, Backpack)
