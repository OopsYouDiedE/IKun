# 存放各种数据结构，以及所有的enum；
# 第一个structure是用来存放单个或多个编程步骤的;
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class Turn:
    goal: str
    think: str
    act: str
    observation: str
    review: str
    statu: str



@dataclass
class Step:
    turns: List[Turn]

    @property
    def statu(self):
        return self.turns[-1].statu

    def start(self):
        Lis
