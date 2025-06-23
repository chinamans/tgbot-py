# scheduler_manager.py
import asyncio
import traceback
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from libs.log import logger

# 全局调度器实例
scheduler = None

def get_scheduler():
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
        logger.info("创建新的调度器实例")
    return scheduler

def start_scheduler():
    """启动定时任务调度器"""
    sched = get_scheduler()
    if not sched.running:
        try:
            sched.start()
            logger.info("定时任务调度器已启动")
        except Exception as e:
            logger.error(f"启动调度器失败: {e}")
            logger.error(traceback.format_exc())

def schedule_model_switch(interval_minutes: int):
    """安排模型切换任务"""
    try:
        sched = get_scheduler()
        
        # 移除现有任务
        if sched.get_job('model_switch_job'):
            sched.remove_job('model_switch_job')
        
        # 添加新任务
        sched.add_job(
            switch_model_job,
            'interval',
            minutes=interval_minutes,
            id='model_switch_job'
        )
        logger.info(f"已安排模型切换任务，间隔: {interval_minutes}分钟")
    except Exception as e:
        logger.error(f"安排任务失败: {e}")
        logger.error(traceback.format_exc())

def stop_model_switch():
    """停止模型切换"""
    try:
        sched = get_scheduler()
        if sched.get_job('model_switch_job'):
            sched.remove_job('model_switch_job')
        logger.info("已停止模型切换任务")
    except Exception as e:
        logger.error(f"停止任务失败: {e}")
        logger.error(traceback.format_exc())

async def switch_model_job():
    """自动切换下注模型任务"""
    try:
        # 延迟导入避免循环依赖
        from libs.state import state_manager
        
        logger.debug("开始执行模型切换任务...")
        
        # 获取当前状态
        current_index = int(state_manager.get_item("ZHUQUE", "current_model_index", "0"))
        models = ["a", "b"]
        
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
        logger.error(traceback.format_exc())
