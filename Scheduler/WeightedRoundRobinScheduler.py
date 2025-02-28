from Scheduler.SchedulerBase import SchedulerBase

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Network.NetworkBase import FlowFragment


class WeightedRoundRobinScheduler(SchedulerBase):
    def __init__(self, queues: dict, weights: dict):
        super().__init__(queues)
        self.__weights = weights
        self.__curr_queue = None
        self.__weight_counter = {}  # 用于记录每个队列的权重计数

        # 初始化权重计数器
        for queue_id in self.get_queues():
            self.__weight_counter[queue_id] = 0

    # 先根据权重调度，权重相同则按优先级调度
    def schedule(self) -> "FlowFragment":
        queues = self.get_queues()

        # 获取所有队列id
        queue_list = list(queues.keys())

        # 先按权重从高到低排序，权重相同则按优先级从高到低排序
        sorted_queue_list = sorted(queue_list, key=lambda q: (-self.__weights.get(q, 1), -q))

        for _ in range(len(queue_list)):
            if self.__curr_queue is None:
                self.__curr_queue = sorted_queue_list[0]

            # 获取当前队列的目标权重
            target_weight = self.__weights.get(self.__curr_queue, 0)

            # 如果当前队列的权重未用完且队列非空
            if self.__weight_counter[self.__curr_queue] < target_weight and queues[self.__curr_queue]:
                self.__weight_counter[self.__curr_queue] += 1
                return queues[self.__curr_queue].pop(0)

            # 如果当前队列的权重已用完，切换到下一个队列
            self.__weight_counter[self.__curr_queue] = 0
            curr_index = (sorted_queue_list.index(self.__curr_queue) + 1) % len(sorted_queue_list)
            self.__curr_queue = sorted_queue_list[curr_index]

        return None
