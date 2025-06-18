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

# 自定义模块
from app import get_bot_app
from config.config import MY_TGID
from libs.state import state_manager


class Method(Enum):
    def __init__(self, code, message, func_type, options=None):
        self.code = code
        self.message = message
        self.func_type = func_type
        self.options = options

    @classmethod
    def from_code(cls, code):
        if not code:
            return None
        if not isinstance(code, int):
            raise ValueError("Code must be an integer.")
        for method in cls:
            if method.code == code:
                return method
        return None


class InlineButton:
    g = {}

    def __init__(self, section: str, action: str, message: str):
        self.section = section
        self.action = action
        self.message = message
        self.state_section = state_manager.get_section(section, {})

    def set_main_keyboard(self, keyboard):
        self.main_keyboard = keyboard

    def create_button(self, method: Method, default_state=None):
        if method.func_type not in ["toggle", "select", "input"]:
            raise ValueError(f"Unsupported function type: {method.func_type}")
        return getattr(self, f"{method.func_type}_button")(method, default_state)

    def _create_button(self, method: Method, string_state=None):
        return InlineKeyboardButton(
            f"{method.message}：{string_state}",
            callback_data=json.dumps(
                {"f": method.func_type, "c": method.code, "a": self.action}
            ),
        )

    def toggle_button(self, method: Method, default_state="off"):
        state_dict = {"on": "开", "off": "关"}
        current_state = state_manager.get_item(self.section, method.name, default_state)
        string_state = state_dict.get(current_state, current_state)
        return self._create_button(method, string_state)

    def select_button(self, method: Method, default_state=None):
        default_state = default_state or method.options[0]
        current_state = state_manager.get_item(self.section, method.name, default_state)
        string_state = current_state
        return self._create_button(method, string_state)

    def input_button(self, method: Method, default_state=None):
        default_state = default_state or "未设置"
        current_state = state_manager.get_item(self.section, method.name, default_state)
        string_state = current_state if current_state else default_state
        return self._create_button(method, string_state)

    def back_button(self):
        return InlineKeyboardButton(
            "返回",
            callback_data=json.dumps({"f": "back", "a": self.action}),
        )

    def close_button(self):
        return InlineKeyboardButton(
            "关闭",
            callback_data=json.dumps({"f": "close", "a": self.action}),
        )

    def select_value_button(self, method: Method, value: str):
        return InlineKeyboardButton(
            value,
            callback_data=json.dumps(
                {"f": "sv", "c": method.code, "v": value, "a": self.action}
            ),
        )

    def select_keyboard(self, method: Method, one_line_count=5):
        if method.options:
            options = list(method.options)
            keyboard = []
            for i in range(0, len(options), one_line_count):
                row = []
                for j in range(one_line_count):
                    if i + j < len(options):
                        row.append(
                            self.select_value_button(method, str(options[i + j]))
                        )
                keyboard.append(row)
            keyboard.append([self.back_button(), self.close_button()])
            return InlineKeyboardMarkup(keyboard)
        return None

    def input_keyboard(self):
        keyboard = [[self.back_button(), self.close_button()]]
        return InlineKeyboardMarkup(keyboard)

    def set_global(self, key, value):
        self.g[key] = value

    def get_global(self, key):
        return self.g.get(key, None)

    async def input(self, client: Client, message: Message):
        if not message.text or not message.text.strip():
            return
        method: Method = self.get_global("method")
        cb: CallbackQuery = self.get_global("cb")
        if not method or not cb:
            self.remove_handler()
            return
        options = method.options
        value = message.text.strip()
        if "valid_int" in options:
            min_int, max_int = options["valid_int"]
            try:
                v_int = int(value)
                if v_int > max_int or v_int < min_int:
                    raise ValueError(f"请输入{min_int}-{max_int}之间的数字")
            except Exception as e:
                return await message.reply(str(e))
        if "length_str" in options:
            length_str = options["length_str"]
            try:
                if len(value) > length_str:
                    raise ValueError(f"请输入{length_str}个字符以内的字符串")
            except Exception as e:
                return await message.reply(str(e))
        state_manager.set_section(self.section, {method.name: value})
        await cb.edit_message_text(
            self.main_message(),
            reply_markup=self.main_keyboard(),
        )
        self.remove_handler()

    def input_message(self, method: Method, timeout=30):
        return f"{self.message}：\n {method.message} 请在{timeout}秒内输入值：\n{method.options.get("description","") if method.options else ""}"

    def select_message(self, method: Method):
        return f"{self.message}：\n {method.message} 请选择："

    def main_message(self):
        return f"{self.message}："

    async def add_handler(self, timeout=30):
        bot_app = get_bot_app()
        self.handler = bot_app.add_handler(
            MessageHandler(self.input, filters.chat(MY_TGID) & filters.text)
        )
        await asyncio.sleep(timeout)
        self.remove_handler()

    def remove_handler(self):
        if "method" in self.g:
            del self.g["method"]
        if "cb" in self.g:
            del self.g["cb"]
        bot_app = get_bot_app()
        try:
            if self.handler:
                bot_app.remove_handler(*self.handler)
                self.handler = None
        except Exception as e:
            pass


async def inline_button_callback(
    client: Client,
    callback_query: CallbackQuery,
    inline_button=InlineButton,
    Method_class=Method,
):
    # try:
    data: dict = json.loads(callback_query.data)
    code = data.get("c", None)
    function_type = data.get("f")
    method = Method_class.from_code(code)
    match function_type:
        case "toggle":
            state_manager.toggle_item(inline_button.section, method.name)
            await callback_query.edit_message_reply_markup(
                reply_markup=inline_button.main_keyboard()
            )
        case "select":
            await callback_query.edit_message_text(
                inline_button.select_message(method),
                reply_markup=inline_button.select_keyboard(method),
            )
        case "input":
            inline_button.set_global("method", method)
            inline_button.set_global("cb", callback_query)
            timeout = 30
            await callback_query.edit_message_text(
                inline_button.input_message(method, timeout),
                reply_markup=inline_button.input_keyboard(),
            )
            asyncio.create_task(inline_button.add_handler(timeout))
        case "back":
            await callback_query.edit_message_text(
                inline_button.main_message(),
                reply_markup=inline_button.main_keyboard(),
            )
        case "close":
            await callback_query.message.delete()
        case "sv":
            value = data.get("v")
            if method:
                state_manager.set_section(inline_button.section, {method.name: value})
            await callback_query.edit_message_text(
                inline_button.main_message(),
                reply_markup=inline_button.main_keyboard(),
            )
