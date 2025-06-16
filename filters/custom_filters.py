# 系统库
import json

# 第三方库
from pyrogram.types import CallbackQuery
from pyrogram.types.messages_and_media import Message
from pyrogram.filters import create
from pyrogram.filters import Filter


async def reply_to_me_filter(_, __, m: Message):
    return bool(
        m.reply_to_message
        and m.reply_to_message.from_user
        and m.reply_to_message.from_user.is_self
    )


reply_to_me = create(reply_to_me_filter)


async def command_to_me_filter(_, __, m: Message):
    return bool(
        m.reply_to_message
        and m.reply_to_message.reply_to_message
        and m.reply_to_message.reply_to_message.from_user
        and m.reply_to_message.reply_to_message.from_user.is_self
    )


command_to_me = create(command_to_me_filter)


async def auth_filter(_, __, m: Message):
    return bool(m.from_user and m.from_user.id == 5848633300)


auth = create(auth_filter)


async def test_filter(_, __, m: Message):
    return bool(m.from_user and m.from_user.id == 6138413603)


test = create(test_filter)


async def cmct_pay_keyword_filter(_, __, m: Message):
    exclude_keywords = ["转账金额过大", "余额不足", "转账失败"]
    if m.reply_to_message and "+" in m.reply_to_message.text:
        for keyword in exclude_keywords:
            if keyword in m.text:
                return False
        return True
    return False


cmct_pay_keyword = create(cmct_pay_keyword_filter)


def create_bot_filter(bot_id):
    async def bot_filter(_, __, m: Message):
        return bool(m.from_user and m.from_user.is_bot and m.from_user.id == bot_id)

    return create(bot_filter)


cms_bot = create_bot_filter(6091424371)
choujiang_bot = create_bot_filter(6461022460)
zhuque_bot = create_bot_filter(5697370563)
hddobly_bot = create_bot_filter(6474948384)
yyz_bot = create_bot_filter(6296776523)
audiences_bot = create_bot_filter(2053736484)
cmct_bot = create_bot_filter(752250569)


class CallbackDataFromFilter(Filter):
    def __init__(self, from_value):
        self.from_value = from_value

    async def __call__(self, client, callback_query: CallbackQuery):
        try:
            data = json.loads(callback_query.data)
        except Exception:
            return False
        return data.get("a") == self.from_value
