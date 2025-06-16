# 系统库
from enum import auto
import json

# 第三方库
from pyrogram import filters, Client
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
)
from pyrogram.filters import Filter

# 自定义模块
from config.config import MY_TGID
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
        "连续下注几次",
        "select",
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    )
    ydx_start_bouns = (auto(), "起手金额", "input")
    ydx_bet_model = (auto(), "下注模式", "select", bet_models.keys())


gmethod: Ydx = None
gcb: CallbackQuery = None

inline_button = InlineButton(SITE_NAME, ACTION, MESSAGE)


def main_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                inline_button.create_button(Ydx.ydx_dice_reveal),
                inline_button.create_button(Ydx.ydx_dice_bet),
            ],
            [
                inline_button.create_button(Ydx.ydx_start_count),
                inline_button.create_button(Ydx.ydx_stop_count),
            ],
            [
                inline_button.create_button(Ydx.ydx_start_bouns),
                inline_button.create_button(Ydx.ydx_bet_model),
            ],
        ]
    )


inline_button.set_global("main", main_keyboard)


@Client.on_message(filters.chat(MY_TGID) & filters.command(ACTION))
async def ydx(client: Client, message: Message):
    await message.reply(inline_button.main_message(), reply_markup=main_keyboard())


class CallbackDataFromFilter(Filter):
    def __init__(self, from_value):
        self.from_value = from_value

    async def __call__(self, client, callback_query: CallbackQuery):
        try:
            data = json.loads(callback_query.data)
        except Exception:
            return False
        return data.get("a") == self.from_value


@Client.on_callback_query(CallbackDataFromFilter(ACTION))
async def ydx_toggle_callback(client: Client, callback_query: CallbackQuery):
    return await inline_button_callback(client, callback_query, inline_button, Ydx)
