# 第三方库
from pyrogram import filters, Client
from pyrogram.types import Message

# 自定义模块
from config.config import MY_TGID
from libs import others
from libs.state import state_manager


header = "SHARE115TOCMS"

# ================== 开关命令处理 ==================
@Client.on_message(filters.chat(MY_TGID) & filters.command("share115tocms"))
async def share115tocms_switch_set(client: Client, message: Message):

    """
    监控115群将115分享链接发给cmsbot功能的相关设定
    用法：/share115tocms on | off
    """


    if len(message.command) < 2:
        await message.reply("参数不足。用法：`/share115tocms on|off`")
        return
    action = message.command[1].lower()
    valid_modes = { "on", "off"}

    if action not in valid_modes:
        await message.reply("无效参数。请使用 `on` 或 `off`")
        return
    enable = (action == "on")
    status = "启动" if enable else "停止"

    state_manager.set_section(header, {"shareswitch": action})

    await message.reply(f"✅ 115群监听TOCMS功能已{status}！")





# ================== 设置相关参数 ==================
@Client.on_message(filters.chat(MY_TGID) & filters.command("set115tocms"))
async def share115tocms_info_set(client: Client, message: Message):
    
    """    
    用法: /set115tocms keyword str
    """

    if len(message.command) < 3:
        await message.reply(
            f"❌ 参数不足。\n"
            f"用法："
            f"\n/set115tocms cmsbot bot_id    设置CMS的botid(不是API)" 
            f"\n/set115tocms embyapi api_key    设置emby的API_key"  
            f"\n/set115tocms embyserver ip    设置emby的地址如：http://172.0.0.1:8096/ 特别注意不要地址要有http://，最后要有'/'"
            f"\n/set115tocms tmdbapi api_key    设置TMDB的API_key" 
        )
        return

    command = message.command[0].lower().lstrip('/')
    keyword = message.command[1].lower()
    action = message.command[2]


    valid_keyword = {"cmsbot", "embyapi", "embyserver", "tmdbapi"}

    # 命令名是否合法
    if keyword not in valid_keyword:
        site_list = ', '.join(sorted(valid_keyword))
        await message.reply(f"❌ 参数非法。\n有效设置对象：`{site_list}`")
        return
    
    # 应用设置    
    state_manager.set_section(header, {keyword: action})
    await message.reply(f"`{keyword} ` 已设定为 {action}")
       


        

# ================== 添加、删除屏蔽关键字 ==================

@Client.on_message(filters.chat(MY_TGID) & filters.command("blockyword"))
async def blockyword_add_remove(client: Client, message: Message):
    """115电影删选屏蔽词增加或删除"""  

    if len(message.command) < 3:
        await message.reply("参数不足。用法：`/blockyword add xxx` 或 `/blockyword remove xxx` ")
        return
    cmd_name = message.command[0].lower()
    action = message.command[1].lower()
    words = message.command[2].lower()   
    blockyword_list = state_manager.get_item(header,"blockyword_list",[])

    if action in "add" or "remove":
        if action == "add":        
            if words not in blockyword_list:
                blockyword_list.append(words)
        elif action == "remove":
            if words in blockyword_list:
                blockyword_list.remove(words)  

        state_manager.set_section(header, {"blockyword_list": blockyword_list})

        re_mess=await message.reply(f'屏蔽词{words}{action}成功\n当前当前屏蔽词以下：{blockyword_list}')
    else:
        await message.reply("无效参数。请使用 `add` 或 `remove`")
   


