# 系统库
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
from pyrogram.filters import Filter

# 自定义模块
from config.config import MY_TGID
from libs import others
from libs.state import state_manager
from libs.ydx_betmodel import models as bet_models


class Method(Enum):
    DICE_REVEAL = ("ydx_dice_reveal", "结果记录开关")
    DICE_BET = ("ydx_dice_bet", "自动下注开关")
    START_COUNT = ("ydx_start_count", "几连开始下注")
    STOP_COUNT = ("ydx_stop_count", "连续下注几次")
    START_BOUNS = ("ydx_start_bouns", "起手倍投金额")
    BET_MODEL = ("ydx_bet_model", "下注模式")

    def __init__(self, code, message):
        self.code = code
        self.message = message


@Client.on_message(filters.chat(MY_TGID) & filters.command("ydx"))
async def zhuque_fanda_switch(client: Client, message: Message):
    """
    设置朱雀相关功能模块的开关或模式
    用法：/ydx <command> <action>
    示例：/ydx dice_bet a
    """
    if len(message.command) < 3:
        await message.reply(
            f"❌ 参数不足。\n"
            f"用法："
            f"\n/ydx dice_reveal on|off 结果记录开关"
            f"\n/ydx dice_bet on|off    自动下注开关"
            f"\n/ydx start_count num    设置第几连开始下注"
            f"\n/ydx stop_count num     设置连续下注几局没赢停止本次倍投"
            f"\n/ydx start_bouns num    起手倍投金额"
            f"\n/ydx bet_model {"|".join(bet_models.keys())}     下注模式 a:返投 模式 b:跟投 c:大 d:小 e:首投随机连续两输再次随机"
        )
        return

    command = message.command[1].lower()
    action = message.command[2].lower()

    command_modes = {
        "dice_reveal": {"on", "off"},
        "dice_bet": {"on", "off"},
        "start_count": "number",
        "stop_count": "number",
        "start_bouns": "number",
        "bet_model": bet_models.keys(),
    }

    if command not in command_modes:
        valid_cmds = ", ".join(sorted(command_modes))
        await message.reply(f"❌ 无效命令。\n有效命令有：`{valid_cmds}`")
        return

    valid_actions = command_modes[command]
    if valid_actions == "number":
        if not action.isdigit():
            await message.reply(f"❌ 非法参数。`{command}` 命令要求参数为数字")
            return
    elif action not in valid_actions:
        opts = ", ".join(valid_actions)
        await message.reply(f"❌ 非法参数。`{command}` 命令有效选项为：{opts}")
        return

    state_manager.set_section("ZHUQUE", {f"ydx_{command}": action})
    await message.reply(f"`{command}` 已设置为 `{action}` ✅")


def init_inline_button(method: Method, default_state="off"):
    """
    初始化内联按钮
    :param method: Method 枚举成员
    :return: InlineKeyboardButton 实例
    """
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
        callback_data=json.dumps({"toggle": method.code, "action": "ydxb"}),
    )


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


@Client.on_message(filters.chat(MY_TGID) & filters.command("ydxb"))
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
        return data.get("action") == self.from_value


@Client.on_callback_query(CallbackDataFromFilter("ydxb"))
async def ydxb_toggle_callback(client: Client, callback_query: CallbackQuery):
    try:
        data = json.loads(callback_query.data)
        toggle_key = data.get("toggle")
        if toggle_key not in ("dice_reveal", "dice_bet"):
            await callback_query.answer("无效操作", show_alert=True)
            return

        # 获取当前状态
        section = state_manager.get_section("ZHUQUE")
        state_key = f"ydx_{toggle_key}"
        current = section.get(state_key, "off")
        new_state = "off" if current == "on" else "on"

        # 更新状态
        state_manager.set_section("ZHUQUE", {state_key: new_state})
        await callback_query.answer(
            f"{'已开启' if new_state == 'on' else '已关闭'}", show_alert=False
        )
        await callback_query.edit_message_reply_markup(
            reply_markup=init_inline_keyboard()
        )

    except Exception as e:
        await callback_query.answer("操作失败", show_alert=True)
