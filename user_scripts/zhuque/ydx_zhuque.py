# 标准库
import re
import asyncio
from decimal import Decimal
from random import random
from typing import Optional, Tuple

# 第三方库
from pyrogram import Client, filters
from pyrogram.types import Message

# 自定义模块
from app import get_bot_app
from config.config import MY_TGID
from filters import custom_filters
from models.ydx_db_modle import Zhuqueydx
from libs.log import logger
from libs.state import state_manager
from app import get_user_app, get_bot_app



TARGET = [-1002262543959]
SITE_NAME = "zhuque"
BONUS_NAME = "灵石"
auto_bet_bouns = 0
auto_bet_count = 0
small_count =  0 #连小次数
big_count = 0   #连大次数
bet_count = 0   #下注次数 


SENDID = {'DIDA':6359018093,#滴答
          'YY':8049813204, #Yy
          'MYID':1016485267, #我
          'LAOTOU':829718065,#老头
          'PIDAN':8115420654,#皮蛋
          'QIANBI':6007161815, #铅笔老
          'R':7811498862, #R
          'SHUJI':5721909476, #川普书记          
}




########################指定金额下注函数##############################################
async def zhuque_ydx_manual_bet(bet_amount: int, flag: str, message: Message):
    
    """
    手动下注任务，根据提供金额依次点击按钮下注。
    :param manual_bet_amount: 用户可用下注总额
    :param flag: 回调按钮标识
    :param message: 原始下注消息对象
    """
    user_app = get_user_app()
    rele_betbouns  = 0
    # 可选下注按钮金额，从大到小排列
    bet_values = [50_000_000, 5_000_000, 1_000_000, 250_000, 50_000, 20_000, 2_000, 500]
    bet_counts = []
    # 限制最大下注额度
    remaining_bouns = min(bet_amount, 10_000_000)
    logger.info(f"可下注总额 remaining_bouns = {remaining_bouns}")
    # 计算各按钮点击次数
    for value in bet_values:
        count = remaining_bouns // value
        bet_counts.append(count)
        remaining_bouns -= count * value

    # 执行下注逻辑
    for i, count in enumerate(bet_counts):
        bet_value = bet_values[i]
        if count <= 0:
            continue

        for _ in range(count):
            callback_data = f'{{"t":"{flag}","b":{int(bet_value)},"action":"ydxxz"}}'
            logger.info(f"尝试下注：{bet_value} x1 | callback_data={callback_data}")
            
            try:
                result_message = await user_app.request_callback_answer(
                    chat_id=message.chat.id,
                    message_id=message.id,
                    callback_data=callback_data
                )
                logger.debug(f"下注结果: {result_message.message}")

                if "零食不足" in result_message.message:
                    logger.warning(f"零食不足，尝试降一档下注")
                    break  
                else:
                    rele_betbouns += bet_value
                    await asyncio.sleep(1)

            except Exception as e:
                logger.exception(f"下注出错：{e}")
                await asyncio.sleep(1)

    logger.info(f"总下注成功金额: {rele_betbouns}")
    if rele_betbouns == 0:
        await user_app.send_message(message.chat.id, "破产了，下注失败")


############检查自己的id是否押注或是否中奖###############################################
async def listofWinners_check(message: Message, target_tgid: int) -> Optional[str]:
    if not message.entities:
        return None

    for entity in message.entities:
        user = getattr(entity, "user", None)
        if user and user.id == target_tgid:
            return user.first_name or "unknown"
    return None

######################### 查询对应firstname中奖金额###############################
def extract_winner_amount(text: str, winner_name: str) -> int | None:
    for line in text.splitlines():
        line = line.strip()
        if winner_name in line and ':' in line:
            # 取最后一个冒号后的内容
            parts = line.rsplit(':', 1)
            if len(parts) == 2:
                amount_str = parts[-1].strip().replace(',', '')
                if amount_str.isdigit():
                    return int(amount_str)
    return None


######################### 查询自定用户名是押注方位和大小###############################

def extract_bet_info(text: str, target_name: str) -> Optional[Tuple[str, int]]:
    current_area = None
    area_map = {"押大": "Big", "押小": "Small"}

    for line in text.splitlines():
        line = line.strip()

        if line.startswith("押大:"):
            current_area = "押大"
            continue
        elif line.startswith("押小:"):
            current_area = "押小"
            continue
        
        if current_area and ':' in line:
            parts = line.rsplit(':', 1)
            if len(parts) == 2:
                name, amount_str = parts
                name = name.strip()
                amount_str = amount_str.strip().replace(',', '')
                if target_name in name and amount_str.isdigit():
                    amount = int(amount_str)
                    return area_map[current_area], amount

    return None



####################开骰结果监听######################

@Client.on_message(
    filters.chat(TARGET)
    & custom_filters.zhuque_bot
    & filters.regex(r"已结算: 结果为 (\d+) (.)")
)

########################开奖结果监听函数##############################
async def zhuque_ydx_dice_reveal(client: Client, message: Message):
    global small_count  # 连小次数
    global big_count    # 连大次数
    global bet_count    # 下注次数

    bet_side = ""
    bet_amount = 0
    win_amount = 0
    result = None
    die_point = 0
    lottery_result = "unknown"

    # 读取开关状态
    ydx_dice_reveal = state_manager.get_item("ZHUQUE", "ydx_dice_reveal", "on")
    ydx_dice_bet = state_manager.get_item("ZHUQUE", "ydx_dice_bet", "off")

    # 两者均关闭时退出
    if ydx_dice_reveal == "off" and ydx_dice_bet == "off":
        return

    # 提取骰子结果和大小
    match = message.matches[0]
    if match:
        die_point = int(match.group(1))
        result_map = {"大": "Big", "小": "Small"}
        lottery_result = result_map.get(match.group(2), "unknown")

    # 计算连续方向
    if lottery_result == "Big":
        big_count += 1
        small_count = 0
    elif lottery_result == "Small":
        small_count += 1
        big_count = 0
    else:
        big_count = 0
        small_count = 0

    consecutive_count = max(big_count, small_count)

    # 查询是否下注
    if message.reply_to_message:
        firstname_bet = await listofWinners_check(message.reply_to_message, MY_TGID)
        if firstname_bet:
            result = extract_bet_info(message.reply_to_message.text, firstname_bet)
            if result:
                bet_side, bet_amount = result
                bet_count += 1
            else:
                bet_count = 0
        else:
            bet_count = 0

    # 查询是否中奖
    firstname_reveal = await listofWinners_check(message, MY_TGID)
    if firstname_reveal:
        win_amount = extract_winner_amount(message.text, firstname_reveal) or 0

    # 写入数据库
    await Zhuqueydx.add_zhuque_ydx_result_record(
        SITE_NAME,
        die_point,
        lottery_result,
        consecutive_count,
        bet_side,
        bet_count,
        bet_amount,
        win_amount
    )



########################开局监听及判断是否下注##############################
@Client.on_message(
    filters.chat(TARGET)
    & custom_filters.zhuque_bot
    & filters.regex(r"创建时间")
)
async def zhuque_ydx_new_round(client: Client, message: Message):
    bot_app = get_bot_app() 
    ydx_dice_bet = state_manager.get_item("ZHUQUE", "ydx_dice_bet", "off")
    ydx_wwd_switch = state_manager.get_item("ZHUQUE", "ydx_wwd_switch", "off")
    start_coun = int(state_manager.get_item("ZHUQUE", "ydx_start_count", 5))
    stop_count = int(state_manager.get_item("ZHUQUE", "ydx_stop_count", 5))
    bet_model = state_manager.get_item("ZHUQUE", "ydx_bet_model", "a")
    start_bouns = int(state_manager.get_item("ZHUQUE", "ydx_start_bouns", 500))

    result_ydx = await Zhuqueydx.get_latest_ydx_info(SITE_NAME)
    if result_ydx:
        lottery_result, consecutive_count, bet_count, win_amount = result_ydx


    if ydx_dice_bet == "off":
        return
    await zhuque_ydx_models(start_coun, stop_count, start_bouns, result_ydx, message, bet_model)




#下注模式后续搞成Class
async def zhuque_ydx_models(start_count, stop_count, start_bonus, result_ydx, message: Message, model="a"): 
    global auto_bet_count

    if not result_ydx:
        return
    lottery_result, consecutive_count, bet_count, win_amount = result_ydx
    consecutive_count = int(consecutive_count)
    bet_count = int(bet_count)
    opposite_map = {"Big": "s", "Small": "b"}
    bet_side = opposite_map.get(lottery_result)

    if win_amount or bet_count == 0:            
            auto_bet_count = 0     

    if model.lower() == 'a':  
        
        # 开始下注逻辑
        should_bet = (
            consecutive_count >= start_count and
            consecutive_count <= (start_count + stop_count) and
            auto_bet_count < stop_count and        
            bet_side is not None
        )
        if should_bet:
            # 等比下注公式：Sn = a(n² + n) + a  
            # 1000 * (2 ** (n + 1) - 1) 
            
            bet_bonus = start_bonus * (2 ** (auto_bet_count + 1) - 1)  
            auto_bet_count +=1      
            await zhuque_ydx_manual_bet(bet_bonus, bet_side, message)
    elif model.lower() == 'b': #启动时随机追一个，连败3败后追上次胜局，连败后3次后继续切上次胜的        


        if auto_bet_count %  2 == 0:
            flag = "b" if random() < 0.5 else "s"
        else:
            flag = bet_side

        should_bet = (
            consecutive_count >= start_count and
            auto_bet_count < stop_count and        
            bet_side is not None
        )

        if should_bet:
            # 等比下注公式：Sn = a(n² + n) + a   
            bet_bonus = start_bonus * (2 ** (auto_bet_count + 1) - 1)  
            auto_bet_count +=1      
            await zhuque_ydx_manual_bet(bet_bonus, bet_side, message)


            