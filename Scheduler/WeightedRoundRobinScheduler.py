from Scheduler.SchedulerBase import SchedulerBase

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Network.NetworkBase import FlowFragment


class WeightedRoundRobinScheduler(SchedulerBase):
    def __init__(self, queues: dict, weights: dict):
        super().__init__(queues)
        self.__weights = weights
        self.__curr_prio = None
        self.__weight_counter = 0

    def schedule(self) -> "FlowFragment":
        queues = self.get_queues()
        prio_list = self.get_prio_list()

        for _ in range(len(prio_list)):
            if self.__curr_prio is None:
                self.__curr_prio = prio_list[0]

            target_weight = self.__weights.get(self.__curr_prio, 1)

            # 当权重未用完且队列非空时
            if self.__weight_counter < target_weight and queues[self.__curr_prio]:
                self.__weight_counter += 1
                return queues[self.__curr_prio].pop(0)

            # 如果当前优先级权重已用完，切换到下一个优先级
            self.__weight_counter = 0
            curr_index = (prio_list.index(self.__curr_prio) + 1) % len(prio_list)
            self.__curr_prio = prio_list[curr_index]

        return None
