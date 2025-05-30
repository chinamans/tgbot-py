import re
import os
import json
import shutil
import aiohttp
from pathlib import Path
from libs import others
from libs.log import logger
from aiohttp import ClientTimeout
from typing import List, Optional
from pyrogram import filters, Client
from pyrogram.types.messages_and_media import Message
from config.config import M115_GROUP_ID, ADMIN_ID, EMBY_API_KEY, EMBY_SERVER,TMDB_API_KEY,proxy_set


media_path = Path("temp_file/get_media")
blockyword_path = Path("db_file/dbflag/blockyword.json")
blockyword_path.parent.mkdir(parents=True, exist_ok=True)  


monitor_enabled = False
otherchat_trans = False
LINK_PATTERN = re.compile(r"https://115cdn\.com/s/[^\s]+")  # 匹配 115 链接
TARGET = {
    
    "CHANNEL_SHARES_115_ID":-1002188663986,
    "PAN115_SHARE_ID":-1002343015438,
    "GUAGUALE115_ID": -1002245898899
}
     
# ================== TMDB API 类 ==================
class TmdbApi:
    """
    TMDB识别匹配（异步版）
    """
    def __init__(self):
        self.api_key = TMDB_API_KEY
        self.language = 'zh'
        self.base_url = 'https://api.themoviedb.org/3'
        self.proxy = proxy_set['PROXY_URL']  # 可以是 socks5 或 http 代理

    def _get_request_kwargs(self, params: dict) -> dict:
        """构造 aiohttp 请求参数，是否使用代理由 proxy_enable 决定"""
        kwargs = {
            'params': params,
            'ssl': False
        }
        if proxy_set['proxy_enable'] == True:
            kwargs['proxy'] = self.proxy
        return kwargs

    async def search_all(self, title: str, year: str = None) -> List[dict]:
        """
        异步搜索电影和电视剧，返回带有类型字段的结果
        """
        movie_results = await self.search_movies(title, year)
        tv_results = await self.search_tv(title, year)
        for result in movie_results:
            result["media_type"] = "movie"
        for result in tv_results:
            result["media_type"] = "tv"
        result_all  = movie_results + tv_results
        logger.info(f"tmdb 查询结果 {result_all}")

        return result_all
    
    async def search_movies(self, title: str, year: str = None) -> List[dict]:
        """异步查询电影"""
        if not title:
            return []

        url = f"{self.base_url}/search/movie"
        params = {
            'api_key': self.api_key,
            'language': self.language,
            'query': title,
            'year': year
        }

        try:
            timeout = ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                kwargs = self._get_request_kwargs(params)
                async with session.get(url, **kwargs) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data.get('results', [])
        except aiohttp.ClientError as e:
            logger.error(f"TMDB Movie API 错误: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"其他错误: {str(e)}")
            return []
        

    async def search_tv(self, title: str, year: str = None) -> List[dict]:
        """异步查询电视剧"""
        if not title:
            return []

        url = f"{self.base_url}/search/tv"
        params = {
            'api_key': self.api_key,
            'language': self.language,
            'query': title,
            'first_air_date_year': year
        }

        try:
            timeout = ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                kwargs = self._get_request_kwargs(params)
                async with session.get(url, **kwargs) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data.get('results', [])
        except aiohttp.ClientError as e:
            logger.error(f"TMDB TV API 错误: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"其他错误: {str(e)}")
            return []

    @staticmethod
    def compare_names(file_name: str, tmdb_names: list) -> bool:
        """比较文件名是否匹配，忽略大小写和特殊字符"""
        if not file_name or not tmdb_names:
            return False
        if not isinstance(tmdb_names, list):
            tmdb_names = [tmdb_names]
        file_name = re.sub(r'[\W_]+', ' ', file_name).strip().upper()
        for tmdb_name in tmdb_names:
            tmdb_name = re.sub(r'[\W_]+', ' ', tmdb_name).strip().upper()
            if file_name == tmdb_name:
                return True
        return False
    

async def get_movies(title: str, year: Optional[str] = None, media_type: Optional[str] = None, tmdb_id: Optional[int] = None):
    """
    根据标题和年份，检查电影是否在Emby中存在，存在则返回列表
    :param title: 标题
    :param year: 年份，可以为空，为空时不按年份过滤
    :param tmdb_id: TMDB ID
    :param host: 媒体服务器的主机地址
    :param apikey: API 密钥
    :return: 含title、year属性的字典列表
    """ 
    if media_type.lower() == "movie":
        media_type = "media_type"
    elif media_type.lower == "tv":
        media_type = "Series"
    else:
        media_type = None

    url = f"{EMBY_SERVER}emby/Items"
    params = {
        "IncludeItemTypes": f"{media_type}",
        "Fields": "ProviderIds,OriginalTitle,ProductionYear,Path,UserDataPlayCount,UserDataLastPlayedDate,ParentId",
        "StartIndex": 0,
        "Recursive": "true",
        "SearchTerm": title,
        "Limit": 10,
        "IncludeSearchTypes": "false",
        "api_key": EMBY_API_KEY
    }

    try:
        # 使用 aiohttp 异步请求
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                res = await response.json() 
                print("res",res)               
                if res:
                    res_items = res.get("Items")
                    print("，res_items",res_items)
                    if res_items:
                        tmdb_values = []
                        tmdb_values = [item['ProviderIds'].get('Tmdb') for item in res_items if 'Tmdb' in item['ProviderIds']]                        
                        return tmdb_values
                    else:
                        return []
                else:
                    return []                    
    except Exception as e:
        logger.error(f"连接Items出错：" + str(e))
        return []

       
        
# ================== 消息处理逻辑 ==================

async def extract_115_links(message: Message) -> List[str]:
    """提取消息中的 115 链接"""
    if message.caption:
        return LINK_PATTERN.findall(message.caption)
    return []


async def send_115_links(client:Client, message, title, year):
    """
    提取并发送 115 链接
    """
    links = await extract_115_links(message)
    if links:
        for link in links:
            await client.send_message(M115_GROUP_ID['CMS_BOT_ID'], link)
            logger.info(f"已发送媒体: [标题: {title}, 年份: {year}] 链接: {link}")
    else:
        logger.warning("未找到 115 链接。")
        

async def search_and_send_message(client: Client, title, year, complete_series, message):
    if not title:
        logger.info(f"❌ TMDB 未匹配到媒体 | Title: {title}, Year: {year}")
        return

    tmdb_api = TmdbApi()
    results = await tmdb_api.search_all(title, year)

    if not results:
        logger.info(f"❌ TMDB 无搜索结果 | Title: {title}, Year: {year}")
        return

    # 选取匹配项
    result_index = next(
        (
            i for i, item in enumerate(results)
            if (item.get("title") == title or item.get("name") == title)
            and ((item.get("release_date") or item.get("first_air_date") or "")[:4] == str(year))
        ),
        next(
            (i for i, item in enumerate(results)
             if item.get("title") == title or item.get("name") == title),
            0
        )
    )
            




    # 提取 TMDB 结果
    media = results[result_index]
    tmdb_title = media.get('title') or media.get('name', 'Unknown Title')
    tmdb_year = media.get('release_date') or media.get('first_air_date') or 'Unknown Date'
    tmdb_id = media.get('id', 'Unknown ID')
    tmdb_media_type = media.get('media_type', 'Unknown Type')

    logger.info(f"TMDB 匹配成功 | Title: {tmdb_title}, Year: {tmdb_year}, TMDB ID: {tmdb_id}, Type: {tmdb_media_type}")

    # 内部方法封装：检查 Emby 是否已有，未有则推送链接
    async def check_and_send():
        try:
            print(title,year)
            tmdb_list = await get_movies(title=title, year=year, media_type=tmdb_media_type)
            print("tmdb_list",tmdb_list)
            if tmdb_list and str(tmdb_id) in tmdb_list:
                logger.info(f"已存在于媒体库 | Title: {title}, TMDB ID: {tmdb_id}")
            else:
                await send_115_links(client, message, title, year)
        except Exception as e:
            logger.error(f"获取媒体信息失败 | Title: {title}, Error: {e}")

    # 分类型处理
    if tmdb_media_type == "movie":
        await check_and_send()

    elif tmdb_media_type == "tv":
        if complete_series:
            await check_and_send()
        else:
            logger.info(f"TV Series not complete | Title: {title}, TMDB ID: {tmdb_id}")

    else:
        logger.info(f"Unsupported media type: {tmdb_media_type} | Title: {title}, TMDB ID: {tmdb_id}")



@Client.on_message(
        filters.chat(list(TARGET.values()))
        & filters.regex(r"https://115cdn\.com/s/[^\s]+")
    )
async def monitor_channels(client: Client, message: Message):
    """监控频道消息，提取并转发 115 链接。"""
    global monitor_enabled
    title = ""
    if not monitor_enabled:
        return
    if os.path.exists(blockyword_path):
        with open(blockyword_path, "r", encoding="utf-8") as f:
            blockyword_list = json.load(f)
    else:
        blockyword_list = [] 

 
    if (message.chat.id == TARGET["CHANNEL_SHARES_115_ID"]
        or message.chat.id == TARGET["GUAGUALE115_ID"]):
        match = None
        caption = message.caption or "" 
        match = re.search(r"(.*?)\s*\((\d+)\)", caption)         
        if match:
            title = match.group(1).strip()  # 括号前的内容
            year = match.group(2).strip() 
            if "EP" not in caption and "全" in caption:
                complete_series = True
            else:
                complete_series = False

              
        
    elif message.chat.id == TARGET["PAN115_SHARE_ID"]:
        
        size_match = None
        title_year_match = None
        complete_series = False
        caption = message.caption or "" 
        unit_map = {'M': 1, 'G': 1024, 'T': 1024**2}
        if "】" in message.caption:
            title_year_pattern = r"[】](.*?)\s*\((\d+)\)"
        else:  # 如果没有【】，从:后匹配
            title_year_pattern = r"[:] (.*?)\s*\((\d+)\)"

        title_year_match = re.search(title_year_pattern, caption)


        size_pattern = r"大\s*小[：:]\s*([\d.]+)\s*([TGM])"
        size_match = re.search(size_pattern, caption)        
       
        if title_year_match:
            title = title_year_match.group(1).strip()  # 括号前的内容
            year = title_year_match.group(2).strip()

        if size_match:            
            size_value = size_match.group(1)  # 如 '1.02'
            size_unit = size_match.group(2)   # 如 'G'
            size_mb = float(size_value) * unit_map[size_unit]
            if size_mb >= 10240 and "第" not in caption:
                complete_series = True
            else:
                complete_series = False
    if title and year:        
        if any(word in title for word in blockyword_list):
            logger.info(f"检索到群组: [{message.chat.title}] 媒体信息: {title} {year} 是屏蔽关键字,不开始检索") 
        else:
            logger.info(f"检索到群组: [{message.chat.title}] 媒体信息: {title} {year}")
            await search_and_send_message(client,title, year,complete_series ,message)




# ================== 开关命令处理 ==================
@Client.on_message(
        filters.me 
        & (filters.command("dyjk")
           | filters.command("dyzf")
        )           
    )
async def toggle_monitor(client: Client, message: Message):
    """切换监控功能或转发功能状态"""
    global monitor_enabled, otherchat_trans
    if len(message.command) < 2:
        await message.reply("参数不足。用法：`/dyjk on|off` 或 `/dyzf on|off`")
        return
    cmd_name = message.command[0].lower()
    action = message.command[1].lower()

    if action not in ("on", "off"):
        await message.reply("无效参数。请使用 `on` 或 `off`")
        return
    enable = (action == "on")
    status = "启动" if enable else "停止"

    if cmd_name == "dyjk":
        monitor_enabled = enable
        re_mess = await message.edit(f"✅ 监控功能已{status}！")
    elif cmd_name == "dyzf":
        otherchat_trans = enable
        re_mess = await message.edit(f"🔄 转发功能已{status}！")
    else:
        re_mess = await message.edit("无效命令。支持 `/dyjk` 或 `/dyzf`。")
    if re_mess:
        await others.delete_message(re_mess,8)


# ================== 添加、删除屏蔽关键字 ==================
@Client.on_message(
        filters.me 
        & filters.command("blockyword")
    )

async def blockyword_add_remove(client: Client, message: Message):
    """115电影删选屏蔽词增加或删除"""  

    if len(message.command) < 3:
        await message.reply("参数不足。用法：`/blockyword add xxx` 或 `/blockyword remove xxx` ")
        return
    cmd_name = message.command[0].lower()
    action = message.command[1].lower()
    words = message.command[2].lower()   
    
    if os.path.exists(blockyword_path):
        with open(blockyword_path, "r", encoding="utf-8") as f:
            blockyword_list = json.load(f)
    else:
        blockyword_list = []
    
    if action in "add" or "remove":
        if action == "add":        
            if words not in blockyword_list:
                blockyword_list.append(words)
        elif action == "remove":
            if words in blockyword_list:
                blockyword_list.remove(words)        
        try:
            with open(blockyword_path, "w", encoding="utf-8") as f:
                json.dump(blockyword_list, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"屏蔽次增加或删除失败 {str(e)}")
            return
        
        re_mess=await message.edit(f'屏蔽词{words}{action}成功\n当前当前屏蔽词以下：{blockyword_list}')
    else:
        await message.reply("无效参数。请使用 `add` 或 `remove`")
   
    if re_mess:
        await others.delete_message(re_mess,15)




@Client.on_message(
        filters.private 
        & filters.user(M115_GROUP_ID['CMS_BOT_ID'])
    )
async def forward_to_group(client:Client, message: Message):
    """
    CMS_BOT message 转发 给个人CMS群组
    """
    global otherchat_trans
    if otherchat_trans:
        await message.copy(M115_GROUP_ID['CMS_TRANS_CHAT'])
        logger.info(f"成功将CMS_BOT的消息转发给个人CMS群组")


@Client.on_message(
        filters.chat(M115_GROUP_ID['CMS_TRANS_CHAT'])
        & filters.user(ADMIN_ID)
    )

async def forward_to_CMS_bot(client:Client, message: Message):
    """
    个人CMS群组的特定人员消息转发至CMS_BOT
    """
    global otherchat_trans
    if otherchat_trans:
        await message.copy(M115_GROUP_ID['CMS_BOT_ID'])
        logger.info(f"成功将群组消息转发给CMS_BOT")




# ================== 手动查询媒体信息 ==================
@Client.on_message(
    filters.me & filters.command("getmedia")
)
async def getmedia(client: Client, message: Message):
    media_path.mkdir(parents=True, exist_ok=True)

    args = message.command[1:]
    title = args[0] if len(args) >= 1 else ""
    year = args[1] if len(args) >= 2 else "0"

    if not title:
        await message.reply("请提供电影名称，例如：/getmedia 泰坦尼克号 1997")
        return

    tmdb_api = TmdbApi()
    result_mess = await tmdb_api.search_all(title, year)
    
    file_path = media_path / f"{title}({year}).txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(result_mess, ensure_ascii=False, indent=4))

    await client.send_document(M115_GROUP_ID['MESSAGE_TRASN_CHAT'], file_path)
    shutil.rmtree(media_path, ignore_errors=True)
    await message.delete()