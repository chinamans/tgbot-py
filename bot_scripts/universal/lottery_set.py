# 标准库
import re

# 第三方库
from pyrogram import filters, Client
from pyrogram.types import Message

# 自定义模块
from config.config import MY_TGID
from libs import others
from libs.state import state_manager



@Client.on_message(filters.chat(MY_TGID) & filters.command("lotterysw"))
async def lottery_switch(client: Client, message: Message):

    """
    小菜抽奖自动参与开关
    用法：/lotterysw on | off
    """
    if len(message.command) < 2:
        await message.reply("❌ 参数不足。\n用法：`/lotterysw on | off` ")
        return
    action = message.command[1].lower()
    valid_modes = { "on", "off"}
    MY_PTID = state_manager.get_item("LOTTERY","myptuser","")
    if (MY_PTID == "" and action == "on"):
        await message.reply("❌ 领奖用PT站用户名未设定，无法启动抽奖")
        return

    if action not in valid_modes:
        await message.reply("❌ 参数非法。\n有效选项：`on` `off`")
        return
    state_manager.set_section("LOTTERY", {"lottert_switch": action})
    if action == "on":
        await message.reply(f"✅ 自动参与抽奖已开启")        
    else:
        await message.reply("🛑 自动参与抽奖已关闭")
        
        



@Client.on_message(filters.chat(MY_TGID) & filters.command("lotteryuser"))
async def lottery_ptuser(client: Client, message: Message):

    """
    小菜抽奖l领奖用PT站点用户名
    用法：/lotteryuser str
    """
    if len(message.command) < 2:
        await message.reply("参数不足。用法：`/lotteryuser PTuser`")
        return
    action = message.command[1]

    state_manager.set_section("LOTTERY",{"myptuser": action})
    
    await message.reply(f"领奖用PT用户名已设定为：{action}")

@Client.on_message(filters.chat(MY_TGID) & filters.command("lotterytime"))
async def lottery_time(client: Client, message: Message):    

    """
    小菜抽奖领奖用PT站点用户名
    用法：/lotterytime 08:00 10:00 12:00 23:00
    """

    def is_valid_time_format(s: str) -> bool:
        return re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", s) is not None
    if len(message.command) < 2:
        await message.reply("参数不足。用法：`/lotterytime 08:00 10:00 12:00 23:00`")
        return

    commands = message.command
    args = commands[1:] if len(commands) > 1 else []

    valid_times = []
    invalid_times = []

    for t in args:
        if is_valid_time_format(t):
            valid_times.append(t)
        else:
            invalid_times.append(t)

    if invalid_times:
        await message.reply(f"以下参数不是合法时间格式（HH:MM）：\n`{'`, `'.join(invalid_times)}`")
        return

    if len(valid_times) < 2:
        await message.reply("时间设置至少为2个，一个开始一个结束时间")
        return

    # 如果是奇数个，去掉最后一个
    if len(valid_times) % 2 != 0:
        valid_times = valid_times[:-1]

    raw_pairs = []
    for i in range(0, len(valid_times), 2):
        start, end = sorted([valid_times[i], valid_times[i + 1]])
        raw_pairs.append((start, end))

    # 按开始时间排序
    sorted_pairs = sorted(raw_pairs, key=lambda x: x[0])
    
    state_manager.set_section("LOTTERY", {"lotterytime": sorted_pairs})

    # 美化展示
    pretty_pairs = "\n".join([f"{s} ~ {e}" for s, e in sorted_pairs])
    await message.reply(f"✅ 自动参与抽奖时间段已设定：\n{pretty_pairs}")