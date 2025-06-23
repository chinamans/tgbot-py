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
    ydx_auto_switch = (auto(), "自动切换AB模型", "toggle")
    ydx_switch_interval = (
        auto(),
        "切换间隔(分钟)",
        "input",
        {"description": "请输入切换间隔(分钟)", "valid_int": [1, 1440]},
    )
    ydx_dice_reveal = (auto(), "结果记录开关", "toggle")
    ydx_dice_bet = (auto(), "自动下注开关", "toggle")
    ydx_start_count = (
        auto(),
        "几连开始下注",
        "select",
        [0,1, 2, 3, 4, 5, 6, 7, 8, 9],
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
            [
                await inline_button.create_button(Ydx.ydx_auto_switch),
                await inline_button.create_button(Ydx.ydx_switch_interval),
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
    # 处理自动切换设置
    if data == Ydx.ydx_auto_switch.name:
        new_value = "on" if current_value == "off" else "off"
        state_manager.set_section(SITE_NAME, {data: new_value})
        
        # 启停定时任务
        if new_value == "on":
            interval = int(state_manager.get_item(SITE_NAME, Ydx.ydx_switch_interval.name, 30))
            schedule_model_switch(interval)
        else:
            stop_model_switch()
    
    # 处理间隔设置
    elif data == Ydx.ydx_switch_interval.name:
        # ... 输入处理逻辑 ...
        interval = int(user_input)
        state_manager.set_section(SITE_NAME, {data: str(interval)})
        
        # 如果自动切换已开启，更新任务
        if state_manager.get_item(SITE_NAME, Ydx.ydx_auto_switch.name, "off") == "on":
            schedule_model_switch(interval)
    return await inline_button_callback(client, callback_query, inline_button, Ydx)
