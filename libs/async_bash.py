import asyncio


async def bash(command):
    command_list = command.split(" ")
    proc = await asyncio.create_subprocess_exec(
        *command_list,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"bash failed: {stderr.decode().strip()}")
    return stdout.decode().strip()
