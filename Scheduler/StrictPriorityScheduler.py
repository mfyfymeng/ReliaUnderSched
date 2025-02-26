from Scheduler.SchedulerBase import SchedulerBase

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Network.NetworkBase import FlowFragment


class StrictPriorityScheduler(SchedulerBase):
    def __init__(self, queues: dict):
        super().__init__(queues)

    def schedule(self) -> "FlowFragment":
        queues = self.get_queues()
        prio_list = self.get_prio_list()

        for prio in prio_list:
            if queues[prio]:
                return queues[prio].pop(0)

        return None
