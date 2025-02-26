from abc import ABC, abstractmethod

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Network.NetworkBase import FlowFragment


class SchedulerBase(ABC):
    def __init__(self, queues: dict, reverse: bool=True):
        self._queues = queues
        self._prio_list = sorted(queues.keys(), reverse=reverse)

    @abstractmethod
    def schedule(self) -> "FlowFragment":
        pass

    def get_queues(self):
        return self._queues

    def get_prio_list(self):
        return self._prio_list
