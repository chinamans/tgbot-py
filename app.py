import sys
import traceback
import pyrogram
from pyrogram import Client
from libs.log import logger

async def main():
    try:
        logger.info("="*50)
        logger.info("应用开始启动...")
        logger.info(f"Python版本: {sys.version}")
        logger.info(f"Pyrogram版本: {pyrogram.__version__}")
        
        # 检查状态文件
        from pathlib import Path
        state_path = Path("config/state.toml")
        if not state_path.exists():
            logger.warning("状态文件不存在，将创建空文件")
            state_path.touch()
        
        # 初始化客户端
        bot_app = get_bot_app()
        user_app = get_user_app()
        
        # 启动客户端
        await bot_app.start()
        await user_app.start()
        logger.info("客户端启动成功")
        
        # 设置命令
        from setup import setup_commands
        await setup_commands()
        logger.info("命令设置完成")
        
        # 初始化调度器
        from scheduler_manager import start_scheduler
        start_scheduler()
        logger.info("调度器初始化完成")
        
        # 检查自动切换状态
        from libs.state import state_manager
        auto_switch = state_manager.get_item("ZHUQUE", "auto_switch_model", "off")
        if auto_switch == "on":
            interval = int(state_manager.get_item("ZHUQUE", "switch_interval", "30"))
            from scheduler_manager import schedule_model_switch
            schedule_model_switch(interval)
            logger.info(f"检测到自动切换已开启，安排任务: {interval}分钟")
        
        # 保持运行
        logger.info("应用启动完成，等待消息...")
        await pyrogram.idle()
        
    except Exception as e:
        logger.critical(f"启动过程中发生致命错误: {str(e)}")
        logger.critical(traceback.format_exc())
        raise
    finally:
        # 清理
        await bot_app.stop()
        await user_app.stop()
        logger.info("应用已停止")
