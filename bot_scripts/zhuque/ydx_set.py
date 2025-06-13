# 系统库
import asyncio
from enum import Enum
import json

# 第三方库
from pyrogram import filters, Client
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from pyrogram.handlers import MessageHandler
from pyrogram.filters import Filter

# 自定义模块
from config.config import MY_TGID
from libs import others
from libs.state import state_manager
from libs.ydx_betmodel import models as bet_models


# @Client.on_message(filters.chat(MY_TGID) & filters.command("ydx"))
# async def zhuque_fanda_switch(client: Client, message: Message):
#     """
#     设置朱雀相关功能模块的开关或模式
#     用法：/ydx <command> <action>
#     示例：/ydx dice_bet a
#     """
#     if len(message.command) < 3:
#         await message.reply(
#             f"❌ 参数不足。\n"
#             f"用法："
#             f"\n/ydx dice_reveal on|off 结果记录开关"
#             f"\n/ydx dice_bet on|off    自动下注开关"
#             f"\n/ydx start_count num    设置第几连开始下注"
#             f"\n/ydx stop_count num     设置连续下注几局没赢停止本次倍投"
#             f"\n/ydx start_bouns num    起手倍投金额"
#             f"\n/ydx bet_model {"|".join(bet_models.keys())}     下注模式 a:返投 模式 b:跟投 c:大 d:小 e:首投随机连续两输再次随机"
#         )
#         return

#     command = message.command[1].lower()
#     action = message.command[2].lower()

#     command_modes = {
#         "dice_reveal": {"on", "off"},
#         "dice_bet": {"on", "off"},
#         "start_count": "number",
#         "stop_count": "number",
#         "start_bouns": "number",
#         "bet_model": bet_models.keys(),
#     }

#     if command not in command_modes:
#         valid_cmds = ", ".join(sorted(command_modes))
#         await message.reply(f"❌ 无效命令。\n有效命令有：`{valid_cmds}`")
#         return

#     valid_actions = command_modes[command]
#     if valid_actions == "number":
#         if not action.isdigit():
#             await message.reply(f"❌ 非法参数。`{command}` 命令要求参数为数字")
#             return
#     elif action not in valid_actions:
#         opts = ", ".join(valid_actions)
#         await message.reply(f"❌ 非法参数。`{command}` 命令有效选项为：{opts}")
#         return

#     state_manager.set_section("ZHUQUE", {f"ydx_{command}": action})
#     await message.reply(f"`{command}` 已设置为 `{action}` ✅")


class Method(Enum):
    DICE_REVEAL = ("ydx_dice_reveal", "结果记录开关", "toggle")
    DICE_BET = ("ydx_dice_bet", "自动下注开关", "toggle")
    START_COUNT = (
        "ydx_start_count",
        "几连开始下注",
        "select",
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    )
    STOP_COUNT = (
        "ydx_stop_count",
        "连续下注几次",
        "select",
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    )
    START_BOUNS = ("ydx_start_bouns", "起手金额", "input")
    BET_MODEL = ("ydx_bet_model", "下注模式", "select", bet_models.keys())

    def __init__(self, code, message, func_type, options=None):
        self.code = code
        self.message = message
        self.func_type = func_type
        self.options = options

    @classmethod
    def from_key(cls, key):
        for method in cls:
            if method.value[0] == key:
                return method
        return None


gmethod: Method = None
gcb: CallbackQuery = None


def init_inline_button(method: Method, default_state="off"):
    current_state = state_manager.get_item("ZHUQUE", method.code, default_state)
    string_state = "开" if current_state == "on" else "关"
    if current_state == "on":
        string_state = "开"
    elif current_state == "off":
        string_state = "关"
    else:
        string_state = current_state

    return InlineKeyboardButton(
        f"{method.message}：{string_state}",
        callback_data=json.dumps({"f": method.func_type, "k": method.code, "a": "ydx"}),
    )


def init_select_button(method: Method, value):
    return InlineKeyboardButton(
        value,
        callback_data=json.dumps(
            {
                "f": "sv",
                "k": method.code,
                "v": value,
                "a": "ydx",
            }
        ),
    )


def back_button():
    return InlineKeyboardButton(
        "返回",
        callback_data=json.dumps({"f": "back", "a": "ydx"}),
    )


def init_select_inline_keyboard(method: Method, one_line_count=5):
    if method.options:
        options = list(method.options)
        keyboard = []
        for i in range(0, len(options), one_line_count):
            row = []
            for j in range(one_line_count):
                if i + j < len(options):
                    row.append(init_select_button(method, str(options[i + j])))
            keyboard.append(row)
        keyboard.append(
            [
                back_button(),
            ]
        )
        return InlineKeyboardMarkup(keyboard)


def init_inline_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                init_inline_button(Method.DICE_REVEAL),
                init_inline_button(Method.DICE_BET),
            ],
            [
                init_inline_button(Method.START_COUNT, 0),
                init_inline_button(Method.STOP_COUNT, 0),
            ],
            [
                init_inline_button(Method.START_BOUNS, 0),
                init_inline_button(Method.BET_MODEL, "a"),
            ],
        ]
    )


async def input(client: Client, message: Message):
    global gmethod
    global gcb
    value = message.text.strip()
    state_manager.set_section("ZHUQUE", {gmethod.code: value})
    await message.delete()
    await gcb.edit_message_text("朱雀运动鞋设置：", reply_markup=init_inline_keyboard())


async def add_handler(client: Client, handler_func, timeout=30):
    # 删除输入处理器
    handler = client.add_handler(
        MessageHandler(handler_func, filters.chat(MY_TGID) & filters.text)
    )
    await asyncio.sleep(timeout)
    client.remove_handler(*handler)


@Client.on_message(filters.chat(MY_TGID) & filters.command("ydx"))
async def ydxb(client: Client, message: Message):
    await message.reply("朱雀运动鞋设置：", reply_markup=init_inline_keyboard())


class CallbackDataFromFilter(Filter):
    def __init__(self, from_value):
        self.from_value = from_value

    async def __call__(self, client, callback_query: CallbackQuery):
        try:
            data = json.loads(callback_query.data)
        except Exception:
            return False
        return data.get("a") == self.from_value


@Client.on_callback_query(CallbackDataFromFilter("ydx"))
async def ydxb_toggle_callback(client: Client, callback_query: CallbackQuery):
    try:
        data: dict = json.loads(callback_query.data)
        key = data.get("k")
        function_type = data.get("f")
        match function_type:
            case "toggle":
                # 切换开关状态
                current = state_manager.get_item("ZHUQUE", key, "off")
                new_state = "off" if current == "on" else "on"

                # 更新状态
                state_manager.set_section("ZHUQUE", {key: new_state})
                await callback_query.answer(
                    f"{'已开启' if new_state == 'on' else '已关闭'}", show_alert=False
                )
                await callback_query.edit_message_reply_markup(
                    reply_markup=init_inline_keyboard()
                )
            case "select":
                # 选择模式
                method = Method.from_key(key)
                await callback_query.edit_message_text(
                    f"朱雀运动鞋设置：\n{method.message} 请选择：",
                    reply_markup=init_select_inline_keyboard(method),
                )
            case "input":
                global gmethod, gcb
                gcb = callback_query
                gmethod = Method.from_key(key)
                timeout = 30
                await callback_query.edit_message_text(
                    f"朱雀运动鞋设置：\n{data.get('k')} 请在{timeout}秒内输入值：",
                    reply_markup=InlineKeyboardMarkup([[back_button()]]),
                )
                asyncio.create_task(add_handler(client, input, timeout))
            case "back":
                # 返回主菜单
                await callback_query.edit_message_text(
                    "朱雀运动鞋设置：", reply_markup=init_inline_keyboard()
                )
            case "sv":
                # 选择值
                value = data.get("v")
                method = Method.from_key(data.get("k"))
                if method:
                    state_manager.set_section("ZHUQUE", {method.code: value})
                    await callback_query.answer(f"已设置为：{value}", show_alert=False)
                else:
                    await callback_query.answer("无效操作", show_alert=True)
                await callback_query.edit_message_text(
                    "朱雀运动鞋设置：", reply_markup=init_inline_keyboard()
                )
    except Exception as e:
        await callback_query.answer("操作失败", show_alert=True)
