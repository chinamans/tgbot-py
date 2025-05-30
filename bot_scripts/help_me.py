from pathlib import Path
from pyrogram.types import Message
from pyrogram import filters, Client
from config.config import MY_TGID
from libs.command_tablepy import generate_command_table_image


@Client.on_message(filters.chat(MY_TGID) & filters.command("helpme"))
async def help_message(client: Client, message: Message):
    command_data = [
        (
            "/id",
            "被回复的消息的telegram ID查询",
            "/id",
            "如果没有回复任何消息则查询自己的",
        ),
        (
            "/dme num",
            "删除当前群组num条自己发消息",
            "/dme 10",
            "删除当前群组10条自己发消息",
        ),
        (
            "/blockyword add str",
            "115群监听,增加不监听关键字",
            "/blockyword add 不良人",
            "新增不监听关键字 “不良人",
        ),
        (
            "/blockyword remove str",
            "115群监听,删除不监听关键字",
            "/blockyword remove 不良人",
            "删除不监听关键字 “不良人",
        ),
        ("/dyjk on/off", "115群电影监控 打开 / 关闭", "/dyjk on", "监听打开"),
        ("/dyzf on/off", "CMSbot转发群消息打开/关闭", "/dyzf on", "转发打开"),
        (
            "autochangename on/off",
            "telegram更新时间昵称打开/关闭",
            "/autochangename on",
            "打开",
        ),
        (
            "/zpr(zp) str num 0/1/2",
            "p站搜索二次图片(0 SFW 1 NSFW 2 混合)",
            "/zpr 明日香 2 0",
            "zpr图片模式/zp文件模式 命令后的参数可选",
        ),
        ("/jupai", "回复的文字消息或/jupai 文字 ", "/jupai 你好", "将‘你好’ 转为jupai"),
        ("/xjj", "小姐姐视频", "/xjj", "/"),
        ("/backuplist", "获取当前已有数据库备份清单", "/backuplist", "/"),
        (
            "/dbrestore num",
            "还原第num号备份(num根据backuplist获取)",
            "/dbrestore 1",
            "还原第1个备份",
        ),
        ("/prizewheel num", "朱雀大转盘", "/prizewheel 10", "朱雀大转盘转10次"),
        ("/getinfo", "朱雀查询个人信息", "/getinfo", "/"),
        (
            "/fanda lose/win/all on/off",
            "朱雀打劫被打劫自动反击",
            "/fanda lose on",
            "被打劫输时自动反击启动",
        ),
        (
            "/fanxian on/off",
            "被打劫时对方输，1%的情况下给与一定比例的返现",
            "/fanxian on",
            "返现功能启启动",
        ),
    ]

    command_imge = await generate_command_table_image(command_data)
    await message.reply_photo(command_imge)
    Path(command_imge).unlink()
