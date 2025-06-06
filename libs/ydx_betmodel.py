from abc import ABC, abstractmethod


class BetModel(ABC):
    @abstractmethod
    def bet_model(self, data):
        pass

    def test(self, data: list[int]):
        loss_count = [0 for _ in range(50)]
        turn_loss_count = 0
        win_count = 0
        total_count = 0
        for i in range(40, len(data) + 1):
            data_i = data[i - 40 : i]
            dx = self.bet_model(data_i)
            if i < len(data):
                total_count += 1
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


class A(BetModel):
    def bet_model(self, data):
        return 1 - data[-1]


class B(BetModel):
    def bet_model(self, data):
        return data[-1]


class C(BetModel):
    def bet_model(self, data):
        return 1


class D(BetModel):
    def bet_model(self, data):
        return 0


models: dict[str, BetModel] = {"A": A(), "B": B(), "C": C(), "D": D()}


def test(data: list[int]):
    data.reverse()
    ret = {}
    for model in models:
        ret[model] = models[model].test(data)
    return ret
