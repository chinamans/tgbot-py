# 标准库
from pathlib import Path

# 第三方库
from pyrogram import filters, Client
from pyrogram.types import Message

# 自定义模块
from config.config import MY_TGID
from libs import others
from libs.state import state_manager
from models.db_to_excel import export_table_to_file
from models.redpocket_db_modle import Redpocket
from models.transform_db_modle import User, Raiding, Transform 
from models.ydx_db_modle import Zhuqueydx


# 监听来自指定TG用户的 /state 命令
@Client.on_message(filters.chat(MY_TGID) & filters.command("export"))
async def db_to_excel_execute(client: Client, message: Message):
    action = "csv"
    valid_keyword = { "ydx", "user", "trans", "dajie", "hongbao"}
    valid_action = {"excel", "csv"}
     
    dbtable_maps = {
        "ydx": Zhuqueydx,
        "user": User,
        "trans": Transform,
        "dajie": Raiding,
        "hongbao": Redpocket
    }
    if len(message.command) < 2:
        await message.reply(
            f"❌ 参数不足。\n用法："
            f"\n/export [ydx | user | trans | dajie | hongbao] [excel | csv] (可选) "
        )
        return
    keyword = message.command[1].lower()
    if len(message.command) == 3:
        action = message.command[2].lower()
        if action not in valid_action:
            await message.reply("❌ 参数非法。\n有效选项：`on` `off`")
            return
    
    

      # 命令名是否合法
    if keyword not in valid_keyword:
        site_list = ', '.join(sorted(valid_keyword))
        await message.reply(f"❌ 参数非法。\n有效设置对象：`{site_list}`")
        return  
    
    
    dbtable = dbtable_maps.get(keyword)

    file_path = await export_table_to_file(dbtable, action)
    await message.reply_document(file_path)

    Path(file_path).unlink()     



    
