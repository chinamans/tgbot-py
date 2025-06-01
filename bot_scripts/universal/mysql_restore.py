# 标准库
import os
import gzip
import tempfile
import subprocess
from pathlib import Path

# 第三方库
from pyrogram import filters, Client
from pyrogram.types import Message

# 自定义模块
from config.config import DB_INFO,MY_TGID
from libs import others

# === 配置部分 ===
BACKUP_DIR = Path("db_file/mysqlBackup")
RETENTION_DAYS = 8  # 备份保留天数

@Client.on_message(filters.chat(MY_TGID) & filters.command("backuplist"))

async def mysql_backup_list(client: Client, message: Message):
    """
    备份文件清单list查询
    """

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    # === 获取所有备份文件（按修改时间倒序） ===
    backup_files = sorted(
        BACKUP_DIR.glob("*.gz"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    if not backup_files:
        re_mess = "❌ 当前没有数据库备份文件"
    else:
        # 生成编号列表
        backup_list = [f"{i}. {file.name}" for i, file in enumerate(backup_files, 1)]
        backup_text = "\n".join(backup_list)
        re_mess = (
            f"📦 当前数据库备份清单如下：\n\n"
            f"{backup_text}\n\n"
            f"请输入 `/dbrestore 序号` 来还原对应备份"
        )
    
    edit_mess = await message.edit(re_mess)
    await others.delete_message(edit_mess, 20)

@Client.on_message(filters.chat(MY_TGID) & filters.command("dbrestore"))
async def mysql_restore_check(client: Client, message: Message):
    
    """
    mySQL数据还原程序
    """
    global BACKUP_DIR
    if len(message.command) > 1 and message.command[1].isdigit():
        index = int(message.command[1])
        backup_files = sorted(Path(BACKUP_DIR).glob("*.sql.gz"), key=lambda f: f.stat().st_mtime, reverse=True)
        if 1 <= index <= len(backup_files):
            selected_file = backup_files[index - 1]
            edit_mess = await message.edit(
                f"\n🔄 开始还原：{selected_file.name} -> 数据库 `{DB_INFO['db_name']}`"
            )
            try:
                # 1. 解压到临时 SQL 文件
                with gzip.open(selected_file, "rb") as f_in:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".sql") as temp_sql:
                        temp_sql.write(f_in.read())
                        temp_sql_path = temp_sql.name

                # 2. 构造命令行还原
                command = [
                    "mysql",
                    "--binary-mode=1",
                    "-h", DB_INFO["address"],
                    "-P", str(DB_INFO["port"]),
                    "-u", DB_INFO["user"],
                    f"-p{DB_INFO['password']}",
                    DB_INFO["db_name"]
                ]

                result = subprocess.run(
                    command,
                    stdin=open(temp_sql_path, "rb"),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                # 删除临时文件
                os.unlink(temp_sql_path)

                if result.returncode != 0:
                    raise Exception(result.stderr.decode(errors="replace"))

                await edit_mess.edit(f"✅ 数据库 {selected_file.name} 还原完成！")

            except Exception as ex:
                await edit_mess.edit(f"❌ 其他错误: {selected_file.name}  {ex}")
        else:
            await message.edit("❌ 输入的编号无效")
    else:
        await message.edit("❌ 格式错误，请使用：`/dbrestore 编号`")
    
    await others.delete_message(message, 60)
    