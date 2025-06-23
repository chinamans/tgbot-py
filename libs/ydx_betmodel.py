from abc import ABC, abstractmethod
import random

from app import logger


class BetModel(ABC):
    fail_count: int = 0
    guess_dx: int = -1
    last_win: bool = False  # 添加属性记录上次是否中奖

    @abstractmethod
    def guess(self, data):
        pass

    def test(self, data: list[int]):
        loss_count = [0 for _ in range(50)]
        turn_loss_count = 0
        win_count = 0
        total_count = 0
        for i in range(40, len(data) + 1):
            data_i = data[i - 40 : i]
            dx = self.guess(data_i)
            if i < len(data):
                total_count += 1
                self.set_result(data[i])
                if data[i] == dx:
                    loss_count[turn_loss_count] += 1
                    win_count += 1
                    turn_loss_count = 0
                    self.last_win = True  # 标记本次中奖
                else:
                    turn_loss_count += 1
                    self.last_win = False  # 标记本次未中奖
        max_nonzero_index = next(
            (
                index
                for index, value in reversed(list(enumerate(loss_count)))
                if value != 0
            ),
            -1,
        )
        return {
            "loss_count": loss_count[: max_nonzero_index + 1],
            "max_nonzero_index": max_nonzero_index,
            "win_rate": win_count / total_count,
            "win_count": 2 * win_count - total_count,
            "turn_loss_count": turn_loss_count,
            "guess": dx,
        }

    def set_result(self, result: int):
        if self.guess_dx != -1:
            if result == self.guess_dx:
                self.fail_count = 0
            else:
                self.fail_count += 1

    def get_consecutive_count(self, data: list[int]):
        """计算当前连续相同结果的次数"""
        if not data:
            return 0
        last = data[-1]
        count = 0
        for v in reversed(data):
            if v == last:
                count += 1
            else:
                break
        dx = "小大"
        logger.info(f"连{dx[last]} [{count}]次")
        return count

    def get_bet_count(self, data: list[int], start_count=0, stop_count=0):
        """计算下注期数（与策略A一致）"""
        consecutive_count = self.get_consecutive_count(data)
        bet_count = consecutive_count - start_count
        if 0 <= bet_count < stop_count:
            return bet_count
        return -1

    def get_bet_bonus(self, start_bonus, bet_count):
        """基础倍投策略"""
        return start_bonus * (2 ** (bet_count + 1) - 1
        
class A(BetModel):
    def guess(self, data):
        self.guess_dx = 1 - data[-1]  # 反龙策略
        return self.guess_dx


class B(BetModel):
    def guess(self, data):
        self.guess_dx = data[-1]  # 跟龙策略
        return self.guess_dx
    
    def get_bet_bonus(self, start_bonus, bet_count):
        if self.last_win:
            return start_bonus
        else:
            return super().get_bet_bonus(start_bonus, bet_count)

class E(BetModel):
    def guess(self, data):
        if self.guess_dx == -1:
            self.guess_dx = random.randint(0, 1)
        if self.fail_count % 2 == 0:
            self.guess_dx = random.randint(0, 1)
        return self.guess_dx
    
    def get_bet_count(self, data: list[int], start_count=0, stop_count=0):
        if 0 < self.fail_count < stop_count:
            return self.fail_count
        count=super().get_bet_count(data, start_count, stop_count)
        if count >= 0:
            return min(self.fail_count,count)
        return -1


models: dict[str, BetModel] = {"a": A(), "b": B(), "e": E()}


def test(data: list[int]):
    data.reverse()
    ret = {}
    for model in models:
        ret[model] = models[model].test(data)
    return ret
