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
        self.dynamic_strategy = "pattern"  # 当前使用的策略: pattern, trend, random
        self.confidence = 0  # 预测置信度 (0-100)
        self.recent_results = deque(maxlen=20)  # 存储最近的结果用于分析
        self.learning_rate = 0.1  # 模式记忆的学习率

    def guess(self, data):
        # 分析历史数据并选择最佳策略
        self._analyze_data(data)
        
        # 根据当前策略进行预测
        if self.dynamic_strategy == "pattern":
            prediction, confidence = self._pattern_recognition(data)
        elif self.dynamic_strategy == "trend":
            prediction, confidence = self._trend_analysis(data)
        else:
            prediction, confidence = self._random_prediction(data)
        
        # 更新预测置信度
        self.confidence = confidence
        
        # 记录预测结果
        self.guess_dx = prediction
        return prediction
    
    def _analyze_data(self, data):
        """分析历史数据以确定最佳策略"""
        if len(data) < 20:  # 数据不足时使用随机策略
            self.dynamic_strategy = "random"
            return
        
        # 计算最近20个结果的胜率
        recent_wins = sum(1 for i in range(-20, -1) if i < len(data) - 1 and data[i] == self.guess_dx)
        win_rate = recent_wins / min(20, len(data) - 1)
        
        # 根据胜率调整策略
        if win_rate > 0.6:
            # 高胜率时优先使用模式识别
            self.dynamic_strategy = "pattern"
        elif win_rate > 0.45:
            # 中等胜率时使用趋势分析
            self.dynamic_strategy = "trend"
        else:
            # 低胜率时切换到随机策略
            self.dynamic_strategy = "random"
    
    def _pattern_recognition(self, data):
        """使用模式识别进行预测"""
        # 获取最近的模式窗口
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
            # 置信度基于匹配度和历史准确率
            confidence = min(95, int(best_score * 100))
            logger.info(f"模式匹配: {best_match} -> {best_prediction} (置信度: {confidence}%)")
            return best_prediction, confidence
        
        # 没有匹配的模式，使用趋势分析
        logger.info("未找到匹配模式，使用趋势分析")
        return self._trend_analysis(data)
    
    def _trend_analysis(self, data):
        """使用趋势分析进行预测"""
        # 计算短期趋势 (最近10个结果)
        short_term = data[-10:] if len(data) >= 10 else data
        short_sum = sum(short_term)
        short_ratio = short_sum / len(short_term)
        
        # 计算中期趋势 (最近30个结果)
        mid_term = data[-30:] if len(data) >= 30 else data
        mid_sum = sum(mid_term)
        mid_ratio = mid_sum / len(mid_term)
        
        # 计算长期趋势 (全部可用数据)
        long_sum = sum(data)
        long_ratio = long_sum / len(data)
        
        # 计算加权趋势
        trend_score = (short_ratio * 0.5) + (mid_ratio * 0.3) + (long_ratio * 0.2)
        
        # 基于趋势做出预测
        if trend_score > 0.55:
            prediction = 1  # 预测大
            confidence = min(90, int((trend_score - 0.5) * 200))
        elif trend_score < 0.45:
            prediction = 0  # 预测小
            confidence = min(90, int((0.5 - trend_score) * 200))
        else:
            # 趋势不明显，随机预测
            prediction = random.randint(0, 1)
            confidence = 50
        
        logger.info(f"趋势分析: 短期{short_ratio:.2f}, 中期{mid_ratio:.2f}, 长期{long_ratio:.2f} -> {prediction} (置信度: {confidence}%)")
        return prediction, confidence
    
    def _random_prediction(self, data):
        """当其他策略效果不佳时使用随机预测"""
        prediction = random.randint(0, 1)
        confidence = 50
        logger.info(f"随机预测: {prediction} (置信度: {confidence}%)")
        return prediction, confidence
    
    def set_result(self, result: int):
        """更新连败次数并学习模式"""
        super().set_result(result)
        
        # 添加结果到历史记录
        self.recent_results.append(result)
        
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
        """基于预测置信度动态调整下注次数"""
        # 高置信度时更激进
        if self.confidence > 80:
            adjusted_start = max(0, start_count - 1)
            adjusted_stop = min(10, stop_count + 2)
        # 中等置信度时保持原策略
        elif self.confidence > 60:
            adjusted_start = start_count
            adjusted_stop = stop_count
        # 低置信度时保守
        else:
            adjusted_start = start_count + 1
            adjusted_stop = max(3, stop_count - 1)
        
        bet_count = self.fail_count - adjusted_start
        if 0 <= bet_count < adjusted_stop:
            return bet_count
        return -1


models: dict[str, BetModel] = {"a": A(), "b": B(), "e": E()}


def test(data: list[int]):
    data.reverse()
    ret = {}
    for model in models:
        ret[model] = models[model].test(data)
    return ret
