import asyncio
from pathlib import Path
from sqlalchemy import text
from config.config import DB_INFO
from models.database import Base
from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    async_scoped_session,
    AsyncSession as _AsyncSession,
)
from sqlalchemy.orm import declarative_base


# SQLite配置路径
db_path = Path("db_file/SQLite/tgbot.db")
db_path.parent.mkdir(parents=True, exist_ok=True)

# 根据配置选择数据库
if DB_INFO["dbset"] == "SQLite":
    DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"

elif DB_INFO["dbset"] == "mySQL":
    password = quote_plus(DB_INFO["password"])
    DATABASE_URL = (
        f"mysql+aiomysql://{DB_INFO['user']}:{password}"
        f"@{DB_INFO['address']}:{DB_INFO['port']}/{DB_INFO['db_name']}"
    )

# SQLite 和 MySQL 的连接配置
if DB_INFO["dbset"] == "SQLite":
    # SQLite 不使用连接池
    async_engine = create_async_engine(DATABASE_URL, echo=True)


else:
    # MySQL 使用连接池
    async_engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        pool_size=10,  # MySQL 使用连接池
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600,
    )


class AsyncSession(_AsyncSession):
    def begin(self):
        if not self.in_transaction():
            return super().begin()
        else:
            return self.begin_nested()


# 创建 sessionmaker
async_session_maker = async_scoped_session(
    async_sessionmaker(bind=async_engine, expire_on_commit=False, class_=AsyncSession),
    asyncio.current_task,
)


async def create_all():
    async with async_engine.begin() as conn:

        if DB_INFO["dbset"] == "SQLite":
            await conn.execute(text("PRAGMA journal_mode=WAL;"))

        await conn.run_sync(Base.metadata.create_all)
