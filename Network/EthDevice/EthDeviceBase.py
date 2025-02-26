from Network.EthLink.Link import Link
from Utils.Error import Error

from Scheduler.StrictPriorityScheduler import StrictPriorityScheduler
from Scheduler.WeightedRoundRobinScheduler import WeightedRoundRobinScheduler

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Network.NetworkBase import Flow
    from Network.NetworkBase import FlowFragment
    from Network.NetworkBase import Topology

    from Network.EthDevice.Switch import Switch
    from Network.EthDevice.EndSystem import EndSystem


class EthDeviceBase:
    def __init__(self, mac_address: str, num_ports: int):
        self.__mac_address = mac_address
        self.__delay = 0.0
        self.__ports = [Port(i) for i in range(num_ports)]
        self.__links = []

        self.buffer = {}

    def get_mac_address(self):
        return self.__mac_address

    def get_delay(self):
        return self.__delay

    def set_delay(self, delay):
        if delay < 0:
            self.__delay = 0.0
        else:
            self.__delay = delay

    def get_ports(self):
        return self.__ports

    def add_link(self, link: Link):
        self.__links.append(link)

    def delete_link(self, link: Link):
        self.__links.remove(link)

    # 将当前设备与另一个设备通过指定的端口进行连接
    def connect(self, self_port_id: int, another_dev: 'EthDeviceBase', another_port_id: int):
        try:
            # 创建 Link 对象来连接两个设备
            new_link = Link(self, self_port_id, another_dev, another_port_id)
            self.add_link(new_link)
            another_dev.add_link(new_link)

            # 更新端口状态，表示该端口已连接设备
            self.__ports[self_port_id].connect(another_dev, another_port_id)
            another_dev.__ports[another_port_id].connect(self, self_port_id)
        except Exception:
            raise Error.LinkCreationError(f"[Error] -- Cannot create a link between {self.get_mac_address()}(port: {self_port_id}) and {another_dev.get_mac_address()}(port: {another_port_id})!")

    def enqueue_buffer(self, fragment: "FlowFragment"):
        next_egress_port = fragment.get_next_egress_port()

        # next_egress_port = -1 表示该流片段已经到达目的ES
        if next_egress_port != -1:
            self.buffer.setdefault(next_egress_port, []).append(fragment)
        else:
            fragment.finish()


class Port:
    def __init__(self, port_id: int, queue_num: int=8, send_rate: int=150):
        self.__port_id = port_id
        self.__connected_device = None
        self.__connected_device_port = None
        self.__queues = {prio: [] for prio in range(queue_num)}
        self.__send_rate = send_rate

    def get_port_id(self):
        return self.__port_id

    def get_connected_device(self):
        return self.__connected_device

    def get_connected_device_port(self):
        return self.__connected_device_port

    def get_send_rate(self):
        return self.__send_rate

    def has_pending_flows(self):
        return any(len(queue) > 0 for queue in self.__queues.values())

    # 将该端口与指定的设备相连
    def connect(self, dev, dev_port: int):
        self.__connected_device = dev
        self.__connected_device_port = dev_port

    # 断开该端口与指定的设备之间的连接/链路
    def disconnect(self):
        self.__connected_device = None
        self.__connected_device_port = None

    # 将流片段加入端口相应的队列
    def enqueue(self, fragment: "FlowFragment"):
        flow = fragment.get_original_flow()
        prio = flow.get_priority()
        if prio in self.__queues:
            self.__queues[prio].append(fragment)
        else:
            print(f"[Error] -- Invalid priority for Flow {flow.get_flow_id()}.")

    # 将（剩余的）流片段放回至（原）队列的头部
    def enqueue_at_front(self, fragment: "FlowFragment"):
        flow = fragment.get_original_flow()
        prio = flow.get_priority()
        if prio in self.__queues:
            self.__queues[prio].insert(0, fragment)
        else:
            print(f"[Error] -- Invalid priority for Flow {flow.get_flow_id()}.")

    # 将流片段从端口的队列中移除
    def dequeue(self) -> "FlowFragment":
        for prio in sorted(self.__queues.keys()):
            if self.__queues[prio]:
                return self.__queues[prio].pop(0)
        return None

    # 将流片段传输到路径中的下一个交换机
    def forward(self, fragment: "FlowFragment", curr_dev: "EthDeviceBase", dev_dict: dict):
        next_dev, next_egress_port = fragment.get_next(curr_dev, dev_dict)
        next_dev.enqueue_buffer(fragment)

    def schedule(self) -> "FlowFragment":
        scheduler = StrictPriorityScheduler(self.__queues)
        return scheduler.schedule()
