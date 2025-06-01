# 标准库
import os
import gzip
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# 自定义模块
from app import scheduler, get_bot_app
from config.config import DB_INFO, PT_GROUP_ID
from libs.log import logger


# === 配置部分 ===
BACKUP_DIR = Path("db_file/mysqlBackup")
RETENTION_DAYS = 8  # 备份保留天数


@scheduler.scheduled_job("cron", hour=6, minute=6, second=6, id="mysql_backup")
async def mysql_backup():
    bot_app = get_bot_app()
    """
    自动mysql备份
    """
    # === 生成带时间戳的备份文件名 ===

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if os.name == "posix":
        if DB_INFO["dbset"] == "mySQL":            
            backup_filename = f"{DB_INFO['db_name']}_backup_{timestamp}.sql"
            backup_path = BACKUP_DIR / backup_filename
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # 执行 mysqldump 并输出到未压缩的 .sql 文件
            try:
                with open(backup_path, "w", encoding="utf-8") as f_out:
                    result = subprocess.run(
                        [
                            "mysqldump",
                            "--no-tablespaces",  # 避免无权限错误
                            "-h", DB_INFO["address"],
                            "-P", str(DB_INFO["port"]),
                            "-u", DB_INFO["user"],
                            f"-p{DB_INFO['password']}",
                            DB_INFO["db_name"]
                        ],
                        stdout=f_out,
                        stderr=subprocess.PIPE,
                        text=True  # 自动处理字符串编码
                    )
                    if result.returncode != 0:
                        logger.error(f"数据库备份失败: {result.stderr}")                        
                        re_mess = await bot_app.send_document(PT_GROUP_ID['BOT_MESSAGE_CHAT'],f"数据库备份失败: {result.stderr}")  
                        backup_path.unlink(missing_ok=True)  # 删除损坏文件
                        return                               
                backup_filename_gz = backup_filename + '.gz'
                backup_path_gz = BACKUP_DIR / backup_filename_gz                
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(backup_path_gz, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out) 
                backup_path.unlink()
                logger.info(f"✅ 数据库备份成功: {backup_path_gz}") 
                re_mess = await bot_app.send_document(
                    chat_id=PT_GROUP_ID['BOT_MESSAGE_CHAT'],
                    document=str(backup_path_gz),
                    caption=f"✅ 数据库备份成功: {backup_filename_gz} \n本地备份路径为:{BACKUP_DIR}"
                )               
            except Exception as e:
                logger.error(f"❌ 备份异常: {e}")
                backup_path.unlink(missing_ok=True)

            # 删除过期备份
            now = datetime.now()
            for file in BACKUP_DIR.glob("*.sql"):
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if (now - mtime).days > RETENTION_DAYS:
                    logger.info(f"🗑️ 删除过期备份: {file}")
                    re_mess = await bot_app.send_message(PT_GROUP_ID['BOT_MESSAGE_CHAT'],f"🗑️ 删除过期备份: {file}")
                    file.unlink()
        else:
            logger.info("当前数据库设置非 mySQL，跳过备份")
    else:
        logger.info("非 Linux 系统，跳过备份任务")
