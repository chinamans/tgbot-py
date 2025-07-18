from abc import ABC, abstractmethod
import random
import numpy as np
from collections import deque
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
    def __init__(self):
        super().__init__()
        self.pattern_window = 10  # 用于模式识别的窗口大小
        self.pattern_memory = {}  # 存储见过的模式及其后续结果
        self.consecutive_threshold = 5  # 连续相同结果阈值
        self.confidence = 0  # 预测置信度 (0-100)
        self.recent_results = deque(maxlen=50)  # 存储最近的结果用于分析
        self.learning_rate = 0.1  # 模式记忆的学习率
        self.bet_size = 1  # 基础下注大小
        self.max_bet_size = 5  # 最大下注倍数
        self.min_bet_size = 1  # 最小下注倍数
        self.bet_history = []  # 下注历史记录

    def guess(self, data):
        # 确保每一局都进行预测
        if len(data) < 5:  # 数据不足时使用简单策略
            self.guess_dx = random.randint(0, 1)
            return self.guess_dx
        
        # 分析历史数据
        self._analyze_data(data)
        
        # 使用组合策略进行预测
        prediction = self._combined_prediction(data)
        
        # 记录预测结果
        self.guess_dx = prediction
        return prediction
    
    def _analyze_data(self, data):
        """分析历史数据以优化预测"""
        # 计算近期胜率
        if len(self.recent_results) > 10:
            recent_wins = sum(1 for r in self.recent_results if r == 1)
            self.win_rate = recent_wins / len(self.recent_results)
        else:
            self.win_rate = 0.5
        
        # 更新下注策略
        if self.win_rate > 0.55:
            # 高胜率时增加下注大小
            self.bet_size = min(self.max_bet_size, self.bet_size + 0.1)
        elif self.win_rate < 0.45:
            # 低胜率时减少下注大小
            self.bet_size = max(self.min_bet_size, self.bet_size - 0.1)
    
    def _combined_prediction(self, data):
        """使用组合策略进行预测"""
        # 1. 模式识别
        pattern_pred = self._pattern_recognition(data)
        
        # 2. 趋势分析
        trend_pred = self._trend_analysis(data)
        
        # 3. 反趋势策略
        counter_pred = 1 - trend_pred if random.random() < 0.3 else trend_pred
        
        # 组合预测结果
        if pattern_pred is not None:
            return pattern_pred
        elif trend_pred == counter_pred:
            return trend_pred
        else:
            # 策略不一致时，根据胜率选择
            return trend_pred if self.win_rate > 0.5 else counter_pred
    
    def _pattern_recognition(self, data):
        """使用模式识别进行预测"""
        # 获取最近的模式窗口
        if len(data) < self.pattern_window:
            return None
            
        recent_pattern = tuple(data[-self.pattern_window:])
        
        # 在记忆中查找相似模式
        best_match = None
        best_score = -1
        best_prediction = None
        
        for pattern, (prediction, score) in self.pattern_memory.items():
            # 计算模式相似度
            match_score = sum(1 for a, b in zip(recent_pattern, pattern) if a == b) / len(recent_pattern)
            
            if match_score > 0.7 and match_score > best_score:
                best_score = match_score
                best_match = pattern
                best_prediction = prediction
        
        if best_match:
            # 更新置信度
            self.confidence = min(95, int(best_score * 100))
            logger.info(f"模式匹配: {best_match} -> {best_prediction} (置信度: {self.confidence}%)")
            return best_prediction
        
        return None
    
    def _trend_analysis(self, data):
        """使用趋势分析进行预测"""
        # 计算短期趋势 (最近10个结果)
        short_term = data[-10:] if len(data) >= 10 else data
        short_sum = sum(short_term)
        short_ratio = short_sum / len(short_term) if short_term else 0.5
        
        # 计算中期趋势 (最近30个结果)
        mid_term = data[-30:] if len(data) >= 30 else data
        mid_sum = sum(mid_term)
        mid_ratio = mid_sum / len(mid_term) if mid_term else 0.5
        
        # 计算长期趋势 (全部可用数据)
        long_sum = sum(data)
        long_ratio = long_sum / len(data) if data else 0.5
        
        # 计算加权趋势
        trend_score = (short_ratio * 0.5) + (mid_ratio * 0.3) + (long_ratio * 0.2)
        
        # 基于趋势做出预测
        if trend_score > 0.55:
            prediction = 1  # 预测大
            self.confidence = min(90, int((trend_score - 0.5) * 200))
        elif trend_score < 0.45:
            prediction = 0  # 预测小
            self.confidence = min(90, int((0.5 - trend_score) * 200))
        else:
            # 趋势不明显，随机预测
            prediction = random.randint(0, 1)
            self.confidence = 50
        
        logger.info(f"趋势分析: 短期{short_ratio:.2f}, 中期{mid_ratio:.2f}, 长期{long_ratio:.2f} -> {prediction} (置信度: {self.confidence}%)")
        return prediction
    
    def set_result(self, result: int):
        """更新连败次数并学习模式"""
        super().set_result(result)
        
        # 添加结果到历史记录
        self.recent_results.append(result)
        
        # 记录下注结果
        self.bet_history.append({
            'prediction': self.guess_dx,
            'actual': result,
            'win': self.guess_dx == result,
            'bet_size': self.bet_size
        })
        
        # 学习当前模式
        if len(self.recent_results) >= self.pattern_window:
            # 获取之前的模式
            pattern = tuple(list(self.recent_results)[-self.pattern_window-1:-1])
            
            # 更新模式记忆
            if pattern not in self.pattern_memory:
                self.pattern_memory[pattern] = (result, 1.0)  # (预测, 准确率)
            else:
                prev_pred, prev_acc = self.pattern_memory[pattern]
                # 更新准确率
                new_acc = prev_acc * (1 - self.learning_rate) + (1 if prev_pred == result else 0) * self.learning_rate
                self.pattern_memory[pattern] = (result, new_acc)
    
    def get_bet_count(self, data: list[int], start_count=0, stop_count=0):
        """每一局都下注，根据胜率动态调整下注大小"""
        # 基于胜率调整下注大小
        if self.win_rate > 0.55:
            # 高胜率时增加下注
            bet_count = min(stop_count - 1, int(self.bet_size))
        elif self.win_rate < 0.45:
            # 低胜率时减少下注
            bet_count = max(0, int(self.bet_size / 2))
        else:
            # 中等胜率时使用基础下注
            bet_count = int(self.bet_size)
        
        # 确保下注次数在有效范围内
        bet_count = max(0, min(stop_count - 1, bet_count))
        
        logger.info(f"下注决策: 胜率={self.win_rate:.2f}, 下注倍数={bet_count}")
        return bet_count


models: dict[str, BetModel] = {"a": A(), "b": B(), "e": E()}


def test(data: list[int]):
    data.reverse()
    ret = {}
    for model in models:
        ret[model] = models[model].test(data)
    return ret
