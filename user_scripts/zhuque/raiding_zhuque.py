# 标准库
import re
from decimal import Decimal
from random import random
from datetime import datetime, timedelta

# 第三方库
from pyrogram import filters, Client
from pyrogram.types import Message

# 自定义模块
from config.reply_message import ZQ_REPLY_MESSAGE
from filters import custom_filters
from libs import others
from libs.log import logger
from libs.state import state_manager
from models.transform_db_modle import User, Raiding



TARGET = [-1001833464786, -1002262543959, -1002522450068]
SITE_NAME = "zhuque"
BONUS_NAME = "灵石"


def extract_lingshi_amount(text: str, pattern: str) -> Decimal | None:
    match = re.search(pattern, text)
    if match:
        return Decimal(match.group(2))
    return None


@Client.on_message(
    filters.chat(TARGET)
    & custom_filters.reply_to_me
    & filters.regex(r"(获得|亏损|你被反打劫|扣税)\s+([\d.]+)\s+灵石\s*$")
    & (custom_filters.zhuque_bot | custom_filters.test)
)
async def zhuque_dajie_Raiding(client: Client, message: Message):

    raiding_msg = message.reply_to_message
    raiding_msg_to = await client.get_messages(raiding_msg.chat.id, message_ids=raiding_msg.reply_to_message_id)
    raidcount_match = re.search(r"^/dajie[\s\S]*\s(\d+)", raiding_msg.text or "")
    raidcount = int(raidcount_match.group(1)) if raidcount_match else 1

    gain = extract_lingshi_amount(message.text, r"(获得) ([\d\.]+) 灵石\s*$")
    loss = extract_lingshi_amount(message.text, r"(亏损|你被反打劫) ([\d\.]+) 灵石\s*$")

    if "扣税" in message.text:
        loss = extract_lingshi_amount(message.text, r"(你被反打劫) ([\d\.]+) 灵石\s*$")
        gain = extract_lingshi_amount(message.text, r"(获得) ([\d\.]+) 灵石\s*$")
    if gain or loss:
        bonus = gain if gain else -loss
        await record_raiding("raiding", bonus, raidcount, raiding_msg_to)


@Client.on_message(
    filters.chat(TARGET)
    & custom_filters.command_to_me
    & (
        filters.regex(r"(获得|亏损|你被反打劫|扣税)\s+([\d.]+)\s+灵石\s*$")
        | filters.regex(r"(赢局总计|操作过于频繁|不能打劫|修为等阶)")
    )
    & (custom_filters.zhuque_bot | custom_filters.test)
)
async def zhuque_dajie_be_raided(client: Client, message: Message):
    """
    被打劫、被info监听
    """
    raiding_msg = message.reply_to_message
    text = message.text
    if "操作过于频繁" in text:
        reply = await raiding_msg.reply(ZQ_REPLY_MESSAGE["dajieCoolingDown"])
        await others.delete_message(reply, 20)
    elif "赢局总计" in text:
        reply_key = "dajieInfoLose" if "总计赢了" in text else "dajieInfoWin"
        reply = await raiding_msg.reply(ZQ_REPLY_MESSAGE[reply_key])
        await others.delete_message(reply, 20)
    elif "不能打劫" in text:
        if "对方灵石低于" in text:
            reply = await raiding_msg.reply(ZQ_REPLY_MESSAGE["meInsufficient"])
        else:
            tmp = await raiding_msg.reply("+1")
            await others.delete_message(tmp, 5)
            reply = await raiding_msg.reply(ZQ_REPLY_MESSAGE["othersInsufficient"])
        await others.delete_message(reply, 20)
    elif "修为等阶" in text:
        reply = await raiding_msg.reply(ZQ_REPLY_MESSAGE["infoBy"])
        await others.delete_message(reply, 20)
    else:
        raidcount_match = re.search(r"^/dajie[\s\S]*\s(\d+)", raiding_msg.text or "")
        raidcount = int(raidcount_match.group(1)) if raidcount_match else 1
        await zhuque_dajie_fanda(raidcount, message)


from random import random
from pyrogram.types import Message

async def zhuque_dajie_fanda(raidcount: int, message: Message):
    """
    自动反打程序（根据灵石输赢判断是否触发反打）
    """
    auto_fanda_switch = state_manager.get_item("ZHUQUE", "fanda", "off")
    fanxian_switch = state_manager.get_item("ZHUQUE", "fanxian", "off")
    fanxian_probability = float(state_manager.get_item("ZHUQUE", "probability", 1)) / 100
    fanxian_blacklist = state_manager.get_item(SITE_NAME.upper(),"blacklist",[])

    raiding_msg = message.reply_to_message
    if not raiding_msg:
        print("无法获取被回复的消息，跳过反打处理。")
        return

    # 默认提取格式
    win_amt = extract_lingshi_amount(message.text, r"(亏损|你被反打劫) ([\d\.]+) 灵石\s*$")
    lose_amt = extract_lingshi_amount(message.text, r"(获得) ([\d\.]+) 灵石\s*$")

    # 特殊扣税处理（覆盖默认提取结果）
    if "扣税" in message.text:
        win_amt = extract_lingshi_amount(message.text, r"你被反打劫 ([\d\.]+) 灵石\s*$")
        lose_amt = extract_lingshi_amount(message.text, r"获得 ([\d\.]+) 灵石\s*$")

    # 记录被劫结果
    if win_amt:
        await record_raiding("beraided", win_amt, raidcount, raiding_msg)
    elif lose_amt:
        await record_raiding("beraided", -lose_amt, raidcount, raiding_msg)

    # 计算打劫冷却
    cd_ready = await dajie_cdtime_Calculate()

    # 判断是否触发自动反打逻辑
    if win_amt or lose_amt:
        is_win = bool(win_amt)
        amount = float(win_amt if is_win else lose_amt)
        message_key = "robbedByWin" if is_win else "robbedByLose"
        fanda_off_key = "robbedwinfandaoff" if is_win else "robbedlosfandaoff"

        fanda_switch_valid = (
            auto_fanda_switch in ("win", "all") if is_win else auto_fanda_switch in ("lose", "all")
        )

        reply = None
        if fanda_switch_valid:
            if not cd_ready:
                reply = await raiding_msg.reply(ZQ_REPLY_MESSAGE["robbedByLoseCD"])
            elif amount >= 2000:
                reply = await raiding_msg.reply(
                    f"/dajie {raidcount} {ZQ_REPLY_MESSAGE[message_key]}"
                )
            else:
                reply = await raiding_msg.reply(ZQ_REPLY_MESSAGE["robbedBynosidepot"])
        else:
            reply = await raiding_msg.reply(ZQ_REPLY_MESSAGE[fanda_off_key])

        # 概率返现（仅在被反打输时生效）
        if is_win and fanxian_switch == "on":
            if raiding_msg.from_user.id in fanxian_blacklist:
                return
            if random() < fanxian_probability:
                odds = random()
                refund = int(float(win_amt) * 0.9 * odds)
                await raiding_msg.reply(f"+{refund}")
                fanxian_reply = await raiding_msg.reply(
                    f"您触发了一次输后返现，表示对您的止损。倍率为 {odds * 100:.2f} %"
                )
                try:
                    await others.delete_message(fanxian_reply, 20)
                except Exception as e:
                    print(f"删除返现消息失败：{e}")

        # 删除主回复消息
        if reply:
            try:
                await others.delete_message(reply, 20)
            except Exception as e:
                print(f"删除反打提示消息失败：{e}")

        # 若被劫金额过大，清理原消息
        if not is_win and amount >= 20000:
            try:
                await raiding_msg.delete()
            except Exception as e:
                print(f"删除被劫大额消息失败：{e}")


async def record_raiding(action: str, amount: Decimal, count: int, message: Message):
    """
    打劫金额写入数据库
    """
    try:
        user = await User.get(message)
        await user.add_raiding_record(SITE_NAME, action, count, amount)
    except Exception as e:
        logger.exception(f"提交失败: 用户消息, 错误：{e}")


async def dajie_cdtime_Calculate() -> bool:
    """
    打劫CD时间计算
    """
    now = datetime.now()
    try:
        last_time, raid_cd = await Raiding.get_latest_raiding_createtime(
            SITE_NAME, "raiding"
        )
        return (now - last_time) >= timedelta(minutes=float(raid_cd))
    except Exception as e:
        logger.exception(f"冷却时间检查失败: {e}")
        return False
