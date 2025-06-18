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
    # autochangename = (auto(), "自动修改报时昵称", "toggle")
    # autofire = (auto(), "朱雀自动释放技能", "toggle")
    # lotterysw = (auto(), "小菜自动抽奖", "toggle")


inline_button = InlineButton(SITE_NAME, ACTION, MESSAGE)


def main_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                inline_button.create_button(Basic.auto_restart),
                # inline_button.create_button(Basic.autochangename),
            ],
            # [
            #     inline_button.create_button(Basic.autofire),
            #     inline_button.create_button(Basic.lotterysw),
            # ],
            [inline_button.close_button()],
        ]
    )


inline_button.set_main_keyboard(main_keyboard)


@Client.on_message(filters.chat(MY_TGID) & filters.command(ACTION))
async def basic_set(_, message: Message):
    await message.reply(inline_button.main_message(), reply_markup=main_keyboard())


@Client.on_callback_query(CallbackDataFromFilter(ACTION))
async def basic_set_callback(client: Client, callback_query: CallbackQuery):
    return await inline_button_callback(client, callback_query, inline_button, Basic)
