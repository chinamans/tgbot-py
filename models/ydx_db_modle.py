# 标准库
from datetime import datetime
from typing import Optional, Tuple

# 第三方库
from sqlalchemy import String, Integer, Numeric, DateTime, func, desc, select
from sqlalchemy.orm import mapped_column, Mapped

# 自定义模块
from models.database import Base
from models import async_session_maker


class Zhuqueydx(Base):
    """
    朱雀ydx 数据库
    """

    __tablename__ = "zhuque_ydx"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    website: Mapped[str] = mapped_column(String(32))
    die_point: Mapped[int] = mapped_column(Integer)
    lottery_result: Mapped[str] = mapped_column(String(32))
    consecutive_count: Mapped[int] = mapped_column(Integer)
    bet_side: Mapped[str] = mapped_column(String(32))
    bet_count: Mapped[int] = mapped_column(Integer)
    bet_amount: Mapped[float] = mapped_column(Numeric(16, 2))
    win_amount: Mapped[float] = mapped_column(Numeric(16, 2))

    @classmethod
    async def add_zhuque_ydx_result_record(
        cls,
        website: str,
        die_point: int,
        lottery_result: str,
        consecutive_count: int,
        bet_side: str,
        bet_count: int,
        bet_amount: float,
        win_amount: float,
    ):
        """
        ydx数据写入数据库

        参数:
            website (str): 网站名称
            die_point (int): 死点
            lottery_result (str): 开奖结果
            consecutive_side (str): 连续方向
            consecutive_count (int): 连续次数
            bet_amount (float): 投注金额
            win_amount (float): 中奖金额

        返回:
            None
        """
        async with async_session_maker() as session, session.begin():
            redpocket = cls(
                website=website,
                die_point=die_point,
                lottery_result=lottery_result,
                consecutive_count=consecutive_count,
                bet_side=bet_side,
                bet_count=bet_count,
                bet_amount=bet_amount,
                win_amount=win_amount,
            )
            session.add(redpocket)

    @classmethod
    async def get_latest_ydx_info(
        cls, website: str
    ) -> Optional[Tuple[str, int, int, float]]:
        """
        查询指定网站的最新一条记录的 lottery_result、consecutive_count、bet_count 和 win_amount。

        参数:
            website (str): 需要查询的站点标识。

        返回:
            Optional[Tuple[str, int, int, float]]: 如果存在记录，则返回对应字段的元组；
            否则返回 None。
        """
        async with async_session_maker() as session, session.begin():
            stmt = (
                select(
                    cls.lottery_result,
                    cls.consecutive_count,
                    cls.bet_count,
                    cls.win_amount,
                )
                .where(cls.website == website)
                .order_by(desc(cls.create_time))
                .limit(1)
            )
            result = (await session.execute(stmt)).one_or_none()
            if result:
                return result
            return None

    @classmethod
    async def get_data(
        cls, website: str = "zhuque", limit: int = 1
    ) -> Optional[Tuple[str, int, int, float]]:
        """
        查询指定网站的最新 limit 条 die_point 记录。

        参数:
            website (str): 需要查询的站点标识。
            limit (int): 查询的记录条数，默认为 1。

        返回:
            Optional[List[int]]: 如果存在记录，则返回 die_point 列表；
            否则返回 None。
        """
        async with async_session_maker() as session, session.begin():
            stmt = (
                select(
                    cls.die_point,
                )
                .where(cls.website == website)
                .order_by(desc(cls.create_time))
                .limit(limit)
            )
            result = (await session.execute(stmt)).scalars().all()
            if result:
                return result
            return None
