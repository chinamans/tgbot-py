# 标准库
from enum import auto

# 第三方库
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
)

# 自定义模块
from config.config import MY_TGID
from libs.inline_buttons import Method, InlineButton, inline_button_callback
from filters.custom_filters import CallbackDataFromFilter


SITE_NAME = "BASIC"
ACTION = "start"
MESSAGE = "基础设置"


class Basic(Method):
    auto_restart = (auto(), "自动重启", "toggle")


inline_button = InlineButton(SITE_NAME, ACTION, MESSAGE)


async def main_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                await inline_button.create_button(Basic.auto_restart),
            ],
            [inline_button.close_button()],
        ]
    )


inline_button.set_main_keyboard(main_keyboard)


@Client.on_message(filters.chat(MY_TGID) & filters.command(ACTION))
async def basic_set(_, message: Message):
    await message.reply(
        inline_button.main_message(), reply_markup=await main_keyboard()
    )


@Client.on_callback_query(CallbackDataFromFilter(ACTION))
async def basic_set_callback(client: Client, callback_query: CallbackQuery):
    return await inline_button_callback(client, callback_query, inline_button, Basic)
