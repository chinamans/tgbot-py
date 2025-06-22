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

SITE_NAME = "ZHUQUE"
ACTION = "ydx"
MESSAGE = "朱雀运动鞋设置"


class Ydx(Method):
    ydx_dice_reveal = (auto(), "结果记录开关", "toggle")
    ydx_dice_bet = (auto(), "自动下注开关", "toggle")
    ydx_start_count = (
        auto(),
        "几连开始下注",
        "select",
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    )
    ydx_stop_count = (
        auto(),
        "最大追投次数",
        "select",
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    )
    ydx_start_bouns = (
        auto(),
        "起手金额",
        "input",
        {
            "description": "请输入任意整数500-50000000",
            "valid_int": [500, 50000000],
        },  # valid_init\length_str
    )
    ydx_bet_model = (auto(), "下注模式", "select", list(bet_models.keys()))


inline_button = InlineButton(SITE_NAME, ACTION, MESSAGE)


async def main_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                await inline_button.create_button(Ydx.ydx_dice_reveal),
                await inline_button.create_button(Ydx.ydx_dice_bet),
            ],
            [
                await inline_button.create_button(Ydx.ydx_start_count),
                await inline_button.create_button(Ydx.ydx_stop_count),
            ],
            [
                await inline_button.create_button(Ydx.ydx_start_bouns),
                await inline_button.create_button(Ydx.ydx_bet_model),
            ],
            [inline_button.close_button()],
        ]
    )


inline_button.set_main_keyboard(main_keyboard)


@Client.on_message(filters.chat(MY_TGID) & filters.command(ACTION))
async def ydx_set(_, message: Message):
    await message.reply(inline_button.main_message(), reply_markup = await main_keyboard())


@Client.on_callback_query(CallbackDataFromFilter(ACTION))
async def ydx_set_callback(client: Client, callback_query: CallbackQuery):
    return await inline_button_callback(client, callback_query, inline_button, Ydx)
