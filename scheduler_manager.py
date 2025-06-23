# scheduler_manager.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from libs.state import state_manager
from libs.log import logger

scheduler = AsyncIOScheduler()

async def switch_model_job():
    """自动切换下注模型任务"""
    try:
        # 获取当前状态
        current_index = int(state_manager.get_item("ZHUQUE", "current_model_index", 0))
        models = ["a", "b"]  # 可切换的模型列表
        
        # 计算下一个模型索引
        new_index = (current_index + 1) % len(models)
        
        # 更新状态
        state_manager.set_section("ZHUQUE", {
            "current_model_index": str(new_index),
            "ydx_bet_model": models[new_index]
        })
        
        logger.info(f"自动切换下注模型: {models[current_index]} → {models[new_index]}")
    except Exception as e:
        logger.error(f"切换模型失败: {e}")

def start_scheduler():
    """启动定时任务"""
    if not scheduler.running:
        scheduler.start()
        logger.info("定时任务调度器已启动")

def schedule_model_switch(interval_minutes: int):
    """安排模型切换任务"""
    # 移除现有任务
    scheduler.remove_job('model_switch_job')
    
    # 添加新任务
    scheduler.add_job(
        switch_model_job,
        'interval',
        minutes=interval_minutes,
        id='model_switch_job'
    )
    logger.info(f"已安排模型切换任务，间隔: {interval_minutes}分钟")

def stop_model_switch():
    """停止模型切换"""
    scheduler.remove_job('model_switch_job')
    logger.info("已停止模型切换任务")