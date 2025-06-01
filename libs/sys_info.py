# 标准库
import os
import sys
import platform
import tomllib
from pathlib import Path

# 第三方库
import pyrogram


pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"

async def system_version_get():
    container_name = os.getenv("HOST_NAME", "")
    sys_info = platform.uname()
    hostname = container_name or sys_info.node
    kernel_version = platform.uname().release
    
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    project_name = data["project"]["name"] or "unkown"

    python_info = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    pyrogram_info = f"{pyrogram.__version__}" 
    tgbot_sate = (
        f"**{project_name} 项目运行状态:\n**"
        f"主机名: {hostname}\n"
        f"主机平台: {sys_info.system}\n"
        f"kernel 版本: {kernel_version}\n"
        f"Python 版本: {python_info}\n"
        f"Pyrogram 版本: {pyrogram_info}\n"
    )
    return project_name, tgbot_sate