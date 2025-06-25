import asyncio
from libs.log import logger
import traceback


async def bash(command):
    command_list = command.split(" ")
    try:
        proc = await asyncio.create_subprocess_exec(
            *command_list,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout = "\n".join(map(lambda x: x.decode().strip(), await proc.communicate()))
        if proc.returncode != 0:
            raise RuntimeError(f"bash {command} failed: {stdout}")
        return stdout
    except Exception as e:
        logger.error(traceback.format_exc())