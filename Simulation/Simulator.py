import numpy as np
import copy
from Network.NetworkBase import *
from Statistics.Statistics import *


class Simulator:
    def __init__(self, topo_file: str, app_file: str):
        self.__topo = Topology()
        self.__topo.create_topo_from_file(topo_file)

        self.__app_manager = AppManager()
        self.__app_manager.load_app_info(app_file)

        self.__curr_time = 0.0
        self.__time_step = 1.0

        self.__statistics = Statistics()

    def set_seed(self, seed: int=42):
        np.random.seed(seed)

    def run(self, max_duration: int):
        print("\n<Network Simulator> Network simulation starts...")

        while self.__curr_time <= max_duration:
            print(f"<Network Simulator> time={self.__curr_time}")

            # 业务按照泊松分布生成curr_time以内新的流实例
            created_flows = self.__app_manager.create_flow(self.__topo, self.__curr_time, self.__time_step)

            if self.__app_manager.get_created_flow_num() == 0:
                self.__curr_time += self.__time_step
                continue

            for flow in created_flows:
                self.__statistics.update_unfinished_flow(flow)

            # 刷新所有交换机的缓冲区：将缓冲区中的流片段加入队列
            self.__flash_switch_buffer()

            # 将源ES端口队列中的流片段（即新生成的流片段）传输至第一个交换机的buffer
            all_devices_dict = self.__topo.get_all_devices()
            self.__app_manager.push(all_devices_dict)

            # 交换机的端口执行调度与传输
            switch_set = self.__topo.get_switches().values()
            for sw in switch_set:
                port_set = sw.get_ports()
                for port in port_set:
                    # 计算当前时间步内可以传输的最大size
                    max_size = port.get_send_rate() * self.__time_step

                    total_transmitted_size = 0
                    while total_transmitted_size < max_size:
                        sched_fragment = port.schedule()
                        if sched_fragment:
                            sched_fragment_size = sched_fragment.get_size()

                            # 如果当前流片段的大小加上已传输的大小未超过max_size，直接传输该片段
                            if total_transmitted_size + sched_fragment_size <= max_size:
                                total_transmitted_size += sched_fragment_size

                                # 将该片段传输至下一个设备的buffer
                                port.forward(sched_fragment, sw, all_devices_dict)

                                flow = sched_fragment.get_original_flow()
                                if flow.is_completed():
                                    flow.end_time = self.__curr_time
                                    self.__statistics.update_completed_flow(flow)
                                    print(f"Flow (id={flow.get_flow_id()}, of App {flow.get_app().get_app_id()}) has completed at time={flow.end_time}.")
                            else:
                                # 如果当前流片段的大小加上已传输的大小超过max_size，则需将其切割为两个部分
                                remaining_size = sched_fragment_size - (max_size - total_transmitted_size)
                                transmitted_fragment = FlowFragment(sched_fragment.get_original_flow(), max_size - total_transmitted_size, self.__curr_time)
                                remaining_fragment = FlowFragment(sched_fragment.get_original_flow(), remaining_size, self.__curr_time)
                                # 将剩余的流片段放回当前队列的队头
                                port.enqueue_at_front(remaining_fragment)
                                total_transmitted_size = max_size
                                # 将该片段传输至下一个设备
                                port.forward(transmitted_fragment, sw, all_devices_dict)
                        else:
                            break

            # 进入下一个仿真时间步
            self.__curr_time += self.__time_step

        print("<Network Simulator> Network simulation has completed.\n")

    # 更新交换机的缓冲区，即将缓冲区中的流片段按优先级移至相应的出端口队列
    def __flash_switch_buffer(self):
        switch_set = self.__topo.get_switches().values()
        for sw in switch_set:
            sw.flash()

    def print_statistic_info(self):
        self.__statistics.app_info = self.__app_manager.get_app_dict()
        self.__statistics.created_flow = self.__app_manager.get_created_flow_dict()

        self.__statistics.print_statistics_info()
