import aiohttp
import asyncio
import time
from config.config import MY_TGID,PT_GROUP_ID,ZHUQUE_COOKIE, ZHUQUE_X_CSRF
from pyrogram import filters, Client
from pyrogram.types import Message
from libs import others
from libs.log import logger


#  配置区，运行前填好配置
cookie_headers = {
    "Cookie": ZHUQUE_COOKIE,
    "X-Csrf-Token": ZHUQUE_X_CSRF,
}
prizes3 = {
     "id": "UID",
     "username": "用户名",
     "name":"等级",
     "upload":"上传",
     "download":"下载",     
     "bonus": "灵石", 
 }
retry_times = 0
info_counts = {item: 0 for item in prizes3.keys()}

url = "https://zhuque.in/api/user/getInfo?"


async def getInfo():
    global retry_times
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=cookie_headers) as response:
                if response.status == 200:
                    retry_times = 0
                    json_response = await response.json()
                    if json_response:
                        for key, value in prizes3.items():
                            if key == "name":
                                info_counts[key] = json_response.get("data", {}).get("class", {}).get(key,"")
                            else:
                                info_counts[key] = json_response.get("data", {}).get(key,"")
                        return info_counts 
                else:
                    print(f"Request failed with status {response.status}")
                    return None          
    except aiohttp.ClientError as e:
        if retry_times < 10:
            print(f"Client error: {e}")
            return_times += 1 
            await asyncio.sleep(5)            
            return await getInfo
    except aiohttp.ServerDisconnectedError as e:    
        if retry_times < 10:
            print(f"Server disconnected: {e}")  
            retry_times += 1 
            await asyncio.sleep(5)            
            return await getInfo    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None  


#########################朱雀信息查询###############################   
@Client.on_message(filters.me & filters.command("getinfo"))
async def zhuque_getInfo(client: Client, message: Message):
    starttime = time.time()
    send_result = await message.reply(f"```\n信息查询中……```")
    prize_counts = await getInfo()
    await send_result.edit(
        f"**查询完成：**耗时：{(time.time()-starttime):.3f} Sec \n**个人信息如下：**\n"
        +"\n".join(
            [
                f"{prizes3[prize]} : {count} "
                for prize, count in prize_counts.items()
                if (prize !="upload" and prize !="download")
            ]
        )
        + f"\n{prizes3['upload']} : {prize_counts['upload']/1024/1024/1024/1024:.2f} TiB\n{prizes3['download']} : {prize_counts['download']/1024/1024/1024/1024:.2f} TiB"
    )
    if message.chat.id not in {MY_TGID, PT_GROUP_ID["BOT_MESSAGE_CHAT"]}:
        await others.delete_message(message, 1)


