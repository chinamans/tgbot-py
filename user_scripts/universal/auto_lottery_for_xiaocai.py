# 标准库
import re
import asyncio
from random import randint, random
from datetime import datetime, time

# 第三方库
from pyrogram import filters, Client
from pyrogram.types import Message

# 自定义模块
from app import get_bot_app
from config.config import PT_GROUP_ID, MY_TGID, LOTTERY_TARGET_GROUP, PRIZE_LIST
from config.reply_message import (
    NO_AOUTOLOTTERY_REPLY_MESSAGE,
    LOTTERY_Sticker_REPLY_MESSAGE,
    LOTTERY_LOSE_REPLY_MESSAGE,
)
from filters import custom_filters
from libs.log import logger
from libs.state import state_manager





lottery_list = {}
################# 判断当前时间是否在 cron 时间范围内 #######################
def is_within_time_ranges():
    now = datetime.now().time()
    TIME_RANGES = state_manager.get_item("LOTTERY","lotterytime","[('08:00','11:00'),('13:00','17:00')]")
    for start_str, end_str in TIME_RANGES:
        start = time.fromisoformat(start_str)
        end = time.fromisoformat(end_str)
        if start <= now <= end:
            return True
    return False

#################抽奖监听#######################

@Client.on_message(
    filters.chat(LOTTERY_TARGET_GROUP)
    & filters.regex(r"^新的抽奖已经创建[\s\S]+参与关键词：「(.+)」")
    & (custom_filters.choujiang_bot
       | custom_filters.test
    )
)
async def lottery_new_message(client:Client, message:Message):
    lottert_switch = state_manager.get_item("LOTTERY","lottert_switch","off")
    bot_app = get_bot_app()
    lottery_info = {}   
    pattern = {"ID": r"抽奖 ID：(.+)",
               "boss_name": r"创建者：(\w+)",
               "boss_ID": r"创建者：\w+\s+\((\d+)\)",
               "prize": r"奖品：\n      ▸ (.+)",
               "allowuser": r"允许普通用户参加：(.+)",
               "keyword": r"参与关键词：「(.+)」",
               }                
    for key, pat in pattern.items():
        match = re.search(pat, message.text)
        lottery_info[key] = match.group(1) if match else ""
    result_key = await prize_check(lottery_info["prize"])    

    if lottert_switch == "on":
        if is_within_time_ranges():
            if result_key:
                logger.info(f"自动抽奖已经打开,时间符合,群组符合，奖品符合，开始自动抽奖 抽奖ID: {lottery_info['ID']}")
                lottery_list[lottery_info['ID']] = {'keyword':lottery_info['keyword'],'boss_name':lottery_info['boss_name'],'boss_ID':lottery_info['boss_ID'],'ptsite':result_key,'prizechat':message.chat.id,'flag':0}
                await asyncio.sleep(randint(25, 65)) 
                if lottery_info['ID'] in lottery_list:                                                
                    logger.info(f"ID: {lottery_info['ID']}的抽奖,随机等待后未结束，故参与抽奖,参与群组:{message.chat.title}({message.chat.id}),抽奖关键字:{lottery_list[lottery_info['ID']]['keyword']}")
                    re_message = await client.send_message(message.chat.id, lottery_list[lottery_info['ID']]['keyword'])
                    lottery_list[lottery_info['ID']]['flag'] = 1
                    await bot_app.send_message(PT_GROUP_ID['BOT_MESSAGE_CHAT'],f"ID: {lottery_info['ID']}的抽奖 \n参与群组:{message.chat.title}({message.chat.id}),\n抽奖关键字:{lottery_list[lottery_info['ID']]['keyword']} \n成功参与抽奖 \n 抽奖链接：{message.link}")
                else:
                    await bot_app.send_message(PT_GROUP_ID['BOT_MESSAGE_CHAT'],f"该抽奖在随机等待时间内已经结束，故不参与抽奖。 \n\n{message.text}\n\n{message.link}")
                    logger.info(f"ID: {lottery_info['ID']}的抽奖，在随机等待时间内已经结束，故不参与抽奖")
            else:
                await bot_app.send_message(PT_GROUP_ID['BOT_MESSAGE_CHAT'],f"该抽奖奖品不符合设定范围故不参与抽奖 \n\n{message.text}\n\n{message.link}")
                logger.info(f"抽奖ID: {lottery_info['ID']} 其奖品不符合设定范围故不参与抽奖 ")
            
        else:
            await bot_app.send_message(PT_GROUP_ID['BOT_MESSAGE_CHAT'],f"不在设定自动抽奖时间内,故不参与抽奖 \n\n{message.text}\n\n{message.link}")
            logger.info(f"抽奖ID: {lottery_info['ID']} 不在设定自动抽奖时间内,故不参与抽奖。")
    else:
        await bot_app.send_message(PT_GROUP_ID['BOT_MESSAGE_CHAT'],f"自动抽奖使能开关未打开,故不参与抽奖 \n\n{message.text}\n\n{message.link}")
        logger.info(f"抽奖ID: {lottery_info['ID']} 自动抽奖使能开关未打开,故不参与抽奖。")

#################中奖结果监听#######################
@Client.on_message(
        filters.regex(r"^参与人数够啦！！开奖[\s\S]+中奖信息\n([\s\S]+)")
        & (custom_filters.choujiang_bot  
           |custom_filters.test
        )
    )
async def lottery_draw_result(client:Client, message:Message):
    MY_PTID = state_manager.get_item("LOTTERY","myptuser","")
    lottert_switch = state_manager.get_item("LOTTERY","lottert_switch","off")
    finish_key = ""
    winner = message.matches[0].group(1)
    logger.info(f"lottery_list befor = {lottery_list} ") 
    if lottert_switch:
        if message.chat.id in LOTTERY_TARGET_GROUP:
            match1 = re.search(r"抽奖 ID：(.+)", message.text)
            finish_key = match1.group(1) if match1 else ""
            if str(MY_TGID) != str(lottery_list[finish_key]['boss_ID']):
                logger.info(f"抽奖不是自己发起的，未中奖随机发黑幕,中奖也自动领奖")
                if str(MY_TGID) in winner:                
                    await asyncio.sleep(randint(10, 45)) 
                    if (lottery_list[finish_key]['ptsite'] in ["ZHUQUE_ID", "DOLBY_ID", "SSD_ID", "AUDIENCES_ID"]):
                        if random() > 0.7:
                            await client.send_message(message.chat.id,f"感谢{lottery_list[finish_key]['boss_name']}大佬")
                        else:
                            await client.send_sticker(message.chat.id, LOTTERY_Sticker_REPLY_MESSAGE[f"thank{randint(1,5)}"])

                        if message.chat.id != PT_GROUP_ID[lottery_list[finish_key]['ptsite']]:
                            if random()<0.3:
                                await client.send_message(PT_GROUP_ID[lottery_list[finish_key]['ptsite']],f"感谢{lottery_list[finish_key]['boss_name']} 爷 小弟在这")
                            elif random()>0.7:
                                await client.send_message(PT_GROUP_ID[lottery_list[finish_key]['ptsite']],f"{lottery_list[finish_key]['boss_name']}爷 射这里")
                            else:
                                await client.send_message(PT_GROUP_ID[lottery_list[finish_key]['ptsite']],f"{lottery_list[finish_key]['boss_name']} 大哥, 这里这里")
                    else:
                        if random()<0.3:
                            await client.send_message(message.chat.id,f"{lottery_list[finish_key]['boss_name']}大佬, \n我的是这个: {MY_PTID}")
                        elif random()>0.7:
                            await client.send_message(message.chat.id,f"{lottery_list[finish_key]['boss_name']}哥, \n打这里 {MY_PTID}")
                        else:
                            await client.send_message(message.chat.id,f"这位爷,我的用户名是: {MY_PTID}")
                else:
                    if lottery_list.get(finish_key):
                        if lottery_list[finish_key]['flag'] == 1:
                            await asyncio.sleep(randint(20, 40)) 
                            if random() > 0.2:
                                logger.info(f"随机概率中标,发送未中奖黑幕")
                                if random() > 0.55:
                                    await client.send_message(message.chat.id,f"{LOTTERY_LOSE_REPLY_MESSAGE[randint(1,5)]}")
                                else:
                                    await client.send_sticker(message.chat.id, LOTTERY_Sticker_REPLY_MESSAGE[f"heimu{randint(1,2)}"])
                            else:
                                logger.info(f"随机概率未中标,不发送未中奖黑幕")
            else:
                logger.info(f"抽奖是自己发起的，故不发黑幕,中奖也不领奖")
            if lottery_list.get(finish_key):
                del lottery_list[finish_key]
            logger.info(f"lottery_list aftter = {lottery_list} ") 

@Client.on_message(custom_filters.reply_to_me
                & (filters.regex(r"机器人")
                | filters.regex(r"真人？")
                | filters.regex(r"脚本")
                | filters.regex(r"自动抽奖")
                | filters.regex(r"不是真人")
                | filters.regex(r"脚本抽奖")
                | filters.regex(r"机器人抽奖")
                | filters.regex(r"这个也是"))
                & filters.user                
                )
async def autolottery_negative_reply(client:Client, message:Message):
    await asyncio.sleep(randint(10,60))
    await message.reply(NO_AOUTOLOTTERY_REPLY_MESSAGE[f"negative{randint(1,len(NO_AOUTOLOTTERY_REPLY_MESSAGE))}"])

#################################中奖信息分析#########################
def parse_lottery_info(prize_info):
    pattern = r'(?P<prize>.+?)\s*\*?\s*(?P<count>\d+)\s*：\s*(?P<winners>.+?)\n'
    matches = re.findall(pattern, prize_info, re.DOTALL)
    lottery_info = {}
    for match in matches:
        prize_name = match[0].strip()
        prize_count = int(match[1].strip())
        winners_info = match[2].strip().split('\n')
        winners = []
        for winner_info in winners_info:
            winner_pattern = r'▸\s*(?P<name>.+)\s+\((?P<id>\d+)\)\s+参与消息'
            winner_match = re.match(winner_pattern, winner_info)
            if winner_match:
                winner_data = {
                    'name': winner_match.group('name').strip(),
                    'id': winner_match.group('id').strip()
                }
                winners.append(winner_data)
        lottery_info[prize_name] = {
            'prize_count': prize_count,
            'prize_winners': winners
        }
    return lottery_info

#################查找元素是否在字符串中存在，存在则返回对应键####################### 
async def prize_check(prize_string):
    for key, prize_names in PRIZE_LIST.items():
        for prize in prize_names:
            if prize in prize_string:
                return key
    return False
