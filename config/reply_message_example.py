from config.config import MY_NAME

ZQ_REPLY_MESSAGE = {
    "infoBy": f"别翻了，口袋比你的脸还干净呢！！",  # 别人 /info 你
    "dajieInfoLose": f"抢你{MY_NAME}哥这么多钱，等我打劫回来！！！？",  # 别人 /dajieinfo 你，你是亏损状态
    "dajieInfoWin": f"{MY_NAME}哥觉得你是个好人！祝你好运！！",  # 别人 /dajieinfo 你，你是盈利状态
    "dajieCoolingDown": f"就这么急不可耐得想给你{MY_NAME}哥送钱？？！",  # 别人 /dajie 你，但是对方冷却还没好被秋人拒绝了
    "meInsufficient": f"你{MY_NAME}哥也难免有资金周转不开的时候，支援点吧！",  # 别人 /dajie 你，但是你自己灵石不足
    "othersInsufficient": f"哇嘎嘎嘎嘎，学人打劫，输完了吧，{MY_NAME}哥送1块打车费，回去猥琐发育吧，",  # 别人 /dajie 你，但是对方灵石不足
    "robbedByWin": f"感谢大佬给你{MY_NAME}哥送钱，继续保持",  # 别人 /dajie 你，而且输了
    "robbedByLose": f"{MY_NAME}哥你也敢抢?看我打劫回来?",  # 别人 /dajie 你，而且赢了
    "robbedByLoseCD":f"{MY_NAME}哥还在CD，养精蓄锐，这次算你走运放过你了",
    "robbedlosfandaoff":f"{MY_NAME}哥你也敢抢？嗯,算了算了，今天心情好下次再反打了",
    "robbedwinfandaoff":f"感谢大佬给你{MY_NAME}哥送钱，看在灵石的份上放过你不反打了",
    "robbedBynosidepot":f"输赢这么少，估计没进加倍区，我都懒得去看我打劫CD好了没有",
    "autoRobbingHint": f"{MY_NAME}的枪已经瞄准你了！！"  # 自动打劫时，跟在 /dajie x 指令后面的提示语，比如回复别人“/dajie 30 HSBC is robbing you”
}
                    
LOTTERY_LOSE_REPLY_MESSAGE = [
    '黑幕',
    '黑幕',
    '黑幕',
    '黑幕',
    '黑幕',
    '黑幕',
    '黑幕',
    '黑幕',
    '黑幕',
    '黑幕'    
]
#这个是没有中奖的词条可以自己各种新增 但是不要和我一样啊


LOTTERY_Sticker_REPLY_MESSAGE = {
    'heimu1':'CAACAgUAAyEGAASEHEl7AAO4Zm_-wWC5oDT8adpRRh9g0PHjvMIAAlEMAAI7XohUAln0iadDgageBA',
    'heimu2':'CAACAgUAAyEGAASEHEl7AAO7Zm_79AWeboVk32M5AYvovb24Ts8AApcKAAJ9LuhUI0kOzgqK1Z0eBA',
    'thank1':'CAACAgUAAyEGAASEHEl7AAPNZnACVCNI6GBiZNkguDanPmlXp60AAm0GAAK60KhVSuCigpo-J6ceBA',
    'thank2':'CAACAgUAAyEGAASEHEl7AAPIZnABzrMSeF-yiiYHpia0SjffCV4AArMHAAK7ApFWws5BsPERfDIeBA',
    'thank3':'CAACAgUAAyEGAASEHEl7AAPGZnABRk2u-9j-J4gEnC2udfBO7e4AAmAHAAJec_FW32cuYwAB_TGzHgQ',
    'thank4':'CAACAgUAAyEGAASEHEl7AAPEZnAAAacdhH02xoFCLOXHInm-mTnGAAJZBAACVGbpV6lLA3veVGh3HgQ',
    'thank5':'CAACAgUAAyEGAASEHEl7AAPKZnAB_zDCcIPkYZQTSq4nlEDKfkQAAioNAALpvxFWLXaoxhdesaoeBA',
}
#这个是贴纸 我就准备了这么几张~


NO_AOUTOLOTTERY_REPLY_MESSAGE = {
    'negative1':'xxxx',
    'negative2':'xxxx',
    'negative3':'xxx',
    'negative4':'xxx',
    'negative5':'xxx',
    'negative6':'xxx',
    'negative7':'xxx',  
}
#这个是被人reply_说是机器人时的反驳词条 可以新加 但是注意'negative7'这个序号
