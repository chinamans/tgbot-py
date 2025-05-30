import os
import sys
import platform
import pyrogram
import tomllib  # Python 3.11+，老版本用 toml 库
from pathlib import Path


def get_project_name():
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    return data["project"]["name"]


async def system_version_get():
    sys_info = platform.uname()
    project_name = get_project_name()
    python_info = f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    pyrogram_info = f"脚本依赖: pyrogram: {pyrogram.__version__}" 
    re_message = f"您的`{project_name}`项目在`{sys_info.node}`的`{sys_info.system}`设备上登录 \n{python_info} {pyrogram_info}"
    return project_name, re_message