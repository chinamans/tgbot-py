# 标准库
import traceback

# 第三方库
from pyrogram import filters, Client
from pyrogram.types import Message

# 自定义模块
from app import get_user_app
from config.config import MY_TGID
from libs.state import state_manager
from libs.log import logger
from schedulers import scheduler, scheduler_jobs



@Client.on_message(filters.chat(MY_TGID) & filters.command("scheduler_jobs"))
async def zhuque_fanda_switch(client: Client, message: Message):
    jobs = scheduler.get_jobs()
    if not jobs:
        await message.reply("当前没有正在运行的调度任务。")
    else:
        job_list = "\n".join([f"- {job.id}" for job in jobs])
        await message.reply(f"当前运行的调度任务有：\n{job_list}")


@Client.on_message(filters.chat(MY_TGID) & filters.command(["autofire", "autochangename"]))
async def scheduler_switch_handler(client: Client, message: Message):
    """
    控制调度任务的开关（如自动释放技能、自动更改昵称）。
    用法: /autofire on|off 或 /autochangename on|off
    """
    user_app = get_user_app()
    if len(message.command) < 2:
        await message.reply("❌ 参数不足。\n用法：`/autofire on|off` 或 `/autochangename on|off`")
        return
    command = message.command[0].lstrip('/')
    action = message.command[1].lower()
    valid_modes = {"on", "off"}

    if command not in scheduler_jobs:
        await message.reply(f"❌ 不支持的命令：`/{command}`")
        return

    if action not in valid_modes:
        await message.reply("❌ 参数非法。\n有效选项：`on` `off`")
        return

    # 保存调度状态
    state_manager.set_section("SCHEDULER", {command: action})

    # 移除已有任务（防止重复）
    scheduler.remove_job(job_id=command, jobstfore=None) if scheduler.get_job(command) else None
    if action == "off":
        if command == "autochangename":
            try:
                await user_app.update_profile(last_name= "") 
            except Exception as e:
                trac = "\n".join(traceback.format_exception(e))
                logger.info(f"更新失败! \n{trac}")
        await message.reply(f"🛑 `{command}` 模式已关闭")

    else:
        try:            
            await scheduler_jobs[command]()
            await message.reply(f"✅ `{command}` 模式已开启")
        except Exception as e:
            await message.reply(f"⚠️ 执行 `{command}` 时出错: {e}")