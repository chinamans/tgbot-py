from abc import ABC, abstractmethod
import random
from app import logger

class BetModel(ABC):
    fail_count: int = 0
    guess_dx: int = -1

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
                else:
                    turn_loss_count += 1
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
        """更新连败次数,在监听结果中调用了"""
        if self.guess_dx != -1:
            if result == self.guess_dx:
                self.fail_count = 0
            else:
                self.fail_count += 1

    def get_consecutive_count(self, data: list[int]):
        """
        根据秋人结果计算连大连小次数
        """
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
        """根据配置计算当前下注多少次"""
        consecutive_count = self.get_consecutive_count(data)
        bet_count = consecutive_count - start_count
        if 0 <= bet_count < stop_count:
            return bet_count
        return -1

    def get_bet_bonus(self, start_bonus, bet_count):
        return start_bonus * (2 ** (bet_count + 1) - 1)


class A(BetModel):
    def guess(self, data):
        self.guess_dx = 1 - data[-1]
        return self.guess_dx


class B(BetModel):
    def guess(self, data):
        self.guess_dx = data[-1]
        return self.guess_dx

    def get_bet_count(self, data: list[int], start_count=0, stop_count=0):
        bet_count = self.fail_count - start_count
        if 0 <= bet_count < stop_count:
            return bet_count
        return -1


class E(BetModel):
    def guess(self, data):
        # 收集出现频率
        if len(data) >= 40:  # 至少收集的数据
            # 计算0和1各自的出现频率
            count_0 = data.count(0)
            count_1 = data.count(1)
            
            # 选择出现频率更高的结果
            if count_0 > count_1:
                self.guess_dx = 0
            elif count_1 > count_0:
                self.guess_dx = 1
            else:
                # 当0和1数量相等时，考虑最近5次的结果趋势
                recent_data = data[-5:] if len(data) >= 5 else data
                recent_0 = recent_data.count(0)
                recent_1 = recent_data.count(1)
                
                if recent_0 > recent_1:
                    self.guess_dx = 0
                elif recent_1 > recent_0:
                    self.guess_dx = 1
                else:
                    # 随机选择，看脸
                    self.guess_dx = random.randint(0, 1)
        else:
            # 随机选择，看脸
            self.guess_dx = random.randint(0, 1)
            
        return self.guess_dx

    def get_bet_count(self, data: list[int], start_count=0, stop_count=0):
        bet_count = self.fail_count - start_count
        if 0 <= bet_count < stop_count:
            return bet_count
        return -1


models: dict[str, BetModel] = {"a": A(), "b": B(), "e": E()}


def test(data: list[int]):
    data.reverse()
    ret = {}
    for model in models:
        ret[model] = models[model].test(data)
    return ret
