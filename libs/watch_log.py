import asyncio
import aiofiles
import os
from libs.async_bash import bash
from libs.log import logger

# logger = logging.Logger("main")


async def monitor_log_file(log_file_path, trigger_string, command):
    last_position = 0
    try:
        async with aiofiles.open(log_file_path, mode="r") as f:
            await f.seek(0, os.SEEK_END)  # 移动到文件末尾
            last_position = await f.tell()
            while True:
                line = await f.readline()  # 异步读取新行
                if line:
                    if trigger_string in line:
                        logger.info(1)
                        # await bash(command)
                else:
                    # 检查文件是否被截断
                    current_size = os.path.getsize(log_file_path)
                    if current_size < last_position:
                        await f.seek(0)  # 文件被截断，回到开头
                        last_position = 0
                    await asyncio.sleep(0.1)  # 短暂休眠以降低 CPU 使用率
                last_position = await f.tell()  # 更新读取位置
    except FileNotFoundError:
        logger.error(f"错误：文件 {log_file_path} 不存在")
    except asyncio.CancelledError:
        logger.error("停止监控")
    except Exception as e:
        logger.error(f"监控错误: {e}")


if __name__ == "__main__":
    log_file_path = "logs/Mytgbot.log"  # 替换为实际日志文件路径
    asyncio.run(monitor_log_file(log_file_path, "Request timed out", "echo 1"))
