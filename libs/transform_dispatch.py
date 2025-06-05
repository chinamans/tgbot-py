# 标准库
import os
from pathlib import Path
from random import randint
# 第三方库
from pyrogram.types import Message

# 自定义模块
from config import config, reply_message
from libs import others
from libs.log import logger
from libs.leaderboard_imge import get_leaderboard
from models.transform_db_modle import User



def build_message(user: User, bonus, bonus_name, sumcount, sumbonus, user_ranking, direction):
    if direction == "get":
        return (
            f"<{user.name}> 大佬，感谢您打赏的 {bonus} {bonus_name}\n"
            f"您打赏了小弟 {sumcount} 次，共计 {sumbonus} {bonus_name}\n"
            f"您是 {config.MY_NAME} 个人打赏总榜的第 {user_ranking} 名\n"
        )
    else:  # "pay"
        return (
        
            f"<{user.name}> 大佬，这是小弟孝敬您的 {abs(bonus):,} {bonus_name}，请笑纳\n"
            f"小弟共孝敬了您 {sumcount} 次，共 {sumbonus} {bonus_name}\n"
            f"您是小弟个人孝敬总榜的第 {user_ranking} 名\n"
        )


async def transform(
    transform_message: Message,
    bonus: int,
    website: str,
    bonus_name: str,
    direction: str = "get",
    leaderboard: bool = "on",
    payleaderboard: bool = "off",
    notification: bool = "on"
):
    leaderboard_image_path = None

    try:
        user = await User.get(transform_message)
        await user.add_transform_record(website, bonus)

        sumcount, sumbonus = await user.get_pay_bonus_count_sum_for_website(website, direction)
        user_ranking = await user.get_pay_user_bonus_rank(website, direction)

        need_leaderboard = leaderboard if direction == "get" else payleaderboard
        if need_leaderboard == "on":
            top5 = await user.get_pay_bonus_leaderboard_by_website(
                site_name=website,
                Direction=direction,
                top_n=5
            )
            leaderboard_image_path = await get_leaderboard(top5, direction)

    except Exception as e:
        logger.exception(f"提交失败: 用户消息：{transform_message}, 错误：{e}")
        await transform_message.reply("转换失败，请稍后再试。")
        return

    if notification == "on":
        text = build_message(user, bonus, bonus_name, sumcount, sumbonus, user_ranking, direction)
        if direction == "get":            
            await transform_message.reply_sticker(reply_message.LOTTERY_Sticker_REPLY_MESSAGE[f"thank{randint(1,5)}"])

        if leaderboard_image_path:
            # 拼接额外提示信息
            if direction == "get":
                extra = f"当前 {config.MY_NAME} 个人打赏总榜 TOP5 如图上所示"
            else:
                extra = f"当前 {config.MY_NAME} 个人孝敬总榜 TOP5 如图上所示"
            full_caption = f"```\n{text + extra}\n```"
            re_mess = await transform_message.reply_photo(
                photo=leaderboard_image_path,
                caption=full_caption
            )
        else:
            re_mess = await transform_message.reply(f"```\n{text}\n```")

        await others.delete_message(re_mess, 30)


    if leaderboard_image_path and Path(leaderboard_image_path).exists():
        Path(leaderboard_image_path).unlink()
