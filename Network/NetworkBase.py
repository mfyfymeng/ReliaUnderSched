import json
import time
import networkx as nx
import numpy as np

from Network.EthDevice.EthDeviceBase import EthDeviceBase
from Network.EthDevice.Switch import Switch
from Network.EthDevice.EndSystem import EndSystem
from Network.EthLink.Link import Link
from matplotlib import pyplot as plt


class Topology:
    def __init__(self):
        self.__switches = {}
        self.__end_systems = {}
        self.__links = []
        self.__graph = nx.Graph()

    def get_switches(self) -> dict:
        return self.__switches

    def get_end_systems(self) -> dict:
        return self.__end_systems

    def get_all_devices(self) -> dict:
        all_devices = {}
        for sw in self.__switches.values():
            all_devices.setdefault(sw.get_mac_address(), sw)
        for es in self.__end_systems.values():
            all_devices.setdefault(es.get_mac_address(), es)
        return all_devices

    def add_switch(self, mac_address: str, num_ports: int):
        new_switch = Switch(mac_address, num_ports)
        self.__switches[mac_address] = new_switch
        self.__graph.add_node(mac_address)
        return new_switch

    def add_end_system(self, mac_address: str, num_ports: int):
        new_end_system = EndSystem(mac_address, num_ports)
        self.__end_systems[mac_address] = new_end_system
        self.__graph.add_node(mac_address)
        return new_end_system

    def __connect(self, dev1: EthDeviceBase, port1: int, dev2: EthDeviceBase, port2: int):
        dev1.connect(port1, dev2, port2)
        dev2.connect(port2, dev1, port1)
        new_link = Link(dev1, port1, dev2, port2)
        self.__links.append(new_link)
        self.__graph.add_edge(dev1.get_mac_address(), dev2.get_mac_address())

    def create_topo_from_file(self, filepath: str):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            for sw_data in data['switch']:
                self.add_switch(sw_data['mac_address'], sw_data['port_num'])

            for es_data in data['end_system']:
                self.add_end_system(es_data['mac_address'], es_data['port_num'])

            for link_data in data['link']:
                dev1 = self.__switches.get(link_data['src_dev']) or self.__end_systems.get(link_data['src_dev'])
                dev2 = self.__switches.get(link_data['dst_dev']) or self.__end_systems.get(link_data['dst_dev'])
                self.__connect(dev1, link_data['src_port'], dev2, link_data['dst_port'])

            print("[Success] -- Construct topo completely!")
        except FileNotFoundError:
            print(f"[Error] -- {filepath} not found.")

    def draw(self, show=True, timeout=5):
        pos = nx.spring_layout(self.__graph, iterations=200)
        nx.draw(self.__graph, pos, with_labels=True)
        if show:
            plt.show(block=False)
            plt.pause(timeout)


class Application:
    def __init__(self, id: str, src: EthDeviceBase, dst: EthDeviceBase, size: int, prio: int, interval: int, path: str):
        self.__id = id
        self.__src = src
        self.__dst = dst
        self.__size = size
        self.__prio = prio
        self.__interval = interval
        self.__path = path
        self.__flow_counter = 0

    def get_app_id(self):
        return self.__id

    def get_size(self):
        return self.__size

    def get_priority(self):
        return self.__prio

    def get_interval(self):
        return self.__interval

    def get_src_device(self):
        return self.__src

    def get_path(self):
        return self.__path

    def get_flow_num(self):
        return self.__flow_counter

    def generate_flow_instance(self, arrival_time) -> "Flow":
        new_flow = Flow(self.__flow_counter, self, arrival_time)
        self.__flow_counter += 1
        return new_flow


class Flow:
    def __init__(self, id: int, app: Application, arrival_time: int):
        self.__id = id
        self.__app = app
        self.__arrival_time = arrival_time
        self.__size = app.get_size()

        self.start_time = arrival_time
        self.end_time = None
        self.remaining_size = self.__size

    def get_flow_id(self):
        return self.__id

    def get_app(self):
        return self.__app

    def get_arrival_time(self):
        return self.__arrival_time

    def get_size(self):
        return self.__size

    def get_priority(self):
        return self.__app.get_priority()

    def is_completed(self):
        return self.remaining_size <= 0


class FlowFragment:
    def __init__(self, original_flow: "Flow", size: int, arrival_time: int):
        self.__original_flow = original_flow
        self.__size = size
        self.__arrival_time = arrival_time
        self.__completed_flag = False      # 用于标记流片段是否已完成传输（到达目的ES）
        self.__next_egress_port = None     # 流片段在下个设备的出口端口

    def get_original_flow(self):
        return self.__original_flow

    def get_size(self):
        return self.__size

    def is_completed(self):
        return self.__completed_flag

    def finish(self):
        self.__completed_flag = True
        self.__original_flow.remaining_size -= self.__size

        if self.__original_flow.remaining_size <= 0:
            self.__original_flow.remaining_size = 0

    def get_next_egress_port(self):
        return self.__next_egress_port

    # 获取流片段所处设备的下一个设备和在下一个设备处的出口端口
    def get_next(self, curr_dev: EthDeviceBase, dev_dict: dict):
        next_dev = None

        path = self.__original_flow.get_app().get_path()
        for i in range(len(path) - 1):
            if path[i] == curr_dev.get_mac_address():
                next_dev = dev_dict.get(path[i + 1])

                next_egress_port = None
                if isinstance(next_dev, Switch):
                    temp_dev = dev_dict.get(path[i + 2])
                    for port in temp_dev.get_ports():
                        if port.get_connected_device() == next_dev:
                            next_egress_port = port.get_connected_device_port()
                            break
                elif isinstance(next_dev, EndSystem):
                    next_egress_port = -1  # -1表示该流片段的下一设备为目的ES

        self.__next_egress_port = next_egress_port

        return next_dev, next_egress_port


class AppManager:
    def __init__(self):
        self.__app_dict = {}
        self.__last_generated_time = {}  # 用于记录每类业务生成流的时间
        self.__created_flow_dict = {}
        self.__created_flow_num = 0

    def get_app_dict(self):
        return self.__app_dict

    def get_created_flow_num(self):
        return self.__created_flow_num

    def get_created_flow_dict(self):
        return self.__created_flow_dict

    def load_app_info(self, filepath: str):
        try:
            with open(filepath, 'r') as f:
                app_data = json.load(f)

            for app in app_data:
                app_id = app["app_id"]
                new_app = Application(app["app_id"],
                                      app["src_dev"],
                                      app["dst_dev"],
                                      app["size"],
                                      app["priority"],
                                      app["interval"],
                                      app["path"])

                self.__app_dict[app_id] = new_app
                self.__last_generated_time[app_id] = 0

            print("[Success] -- Load app info completely!")
        except FileNotFoundError:
            print(f"[Error] -- {filepath} not found.")

    # 按照泊松分布为每个业务创建流实例
    def create_flow(self, topo: Topology, curr_time, time_step):
        created_flows = []

        for app in self.__app_dict.values():
            mean_interval = app.get_interval()
            curr_app_id = app.get_app_id()

            # 计算下一个流的到达时间（服从泊松分布）
            time_window_start = curr_time - time_step
            if time_window_start < 0:
                time_window_start = 0

            while self.__last_generated_time[curr_app_id] < curr_time:
                inter_time = np.random.exponential(mean_interval)
                next_arrival_time = self.__last_generated_time[curr_app_id] + inter_time

                if next_arrival_time > curr_time:
                    break

                # 仅在 time_window_start <= next_arrival_time <= curr_time 才生成新的流实例
                if next_arrival_time >= time_window_start:
                    self.__last_generated_time[curr_app_id] = next_arrival_time
                    new_flow = app.generate_flow_instance(next_arrival_time)

                    self.__created_flow_dict.setdefault(curr_app_id, []).append(new_flow)
                    created_flows.append(new_flow)

                    # 将new_flow放入源ES端口的队列中
                    src_dev = topo.get_end_systems().get(app.get_src_device())
                    if not src_dev:
                        print(f"[Error] -- Flow {new_flow.get_flow_id()} (belonging to App {curr_app_id}) has no source device.")
                        continue

                    # 找到ES与交换机相连的端口
                    for port in src_dev.get_ports():
                        connected_dev = port.get_connected_device()
                        if connected_dev is not None:
                            fragment = FlowFragment(new_flow, new_flow.get_size(), new_flow.get_arrival_time())
                            port.enqueue(fragment)
                            break

                    self.__created_flow_num += 1
                    print(f"A new flow instance (id={new_flow.get_flow_id()}, of App {curr_app_id}) has been created on {src_dev} at time={self.__last_generated_time[curr_app_id]}.")

        return created_flows

    # 将新生成的流从源ES端口队列推送至路径上的第一个交换机buffer
    def push(self, dev_dict: dict):
        for app in self.__app_dict.values():
            src_dev = dev_dict.get(app.get_src_device())
            if not src_dev:
                print(f"[Error] -- Flow {flow.get_flow_id()} (belonging to App {app.get_app_id()}) has no source device.")
                continue

            path = app.get_path()
            if not path:
                print(f"[Error] -- Flow {flow.get_flow_id()} (belonging to App {app.get_app_id()}) has no path.")
                continue

            # 获取流路径上的第一个交换机
            first_switch_mac = path[1]
            first_switch = dev_dict.get(first_switch_mac)
            if first_switch is None:
                print(f"[Error] -- Switch {first_switch_mac} is not found.")
                continue

            # 把流从源ES的端口队列送至第一个交换机buffer
            src_dev_port = None
            for port in src_dev.get_ports():
                if port.get_connected_device() == first_switch:
                    src_dev_port = port
                    break

            if src_dev_port is not None:
                while src_dev_port.has_pending_flows():
                    fragment = src_dev_port.dequeue()
                    if fragment is not None:
                        src_dev_port.forward(fragment, src_dev, dev_dict)
