from Network.EthDevice.EthDeviceBase import EthDeviceBase


class Switch(EthDeviceBase):
    def __init__(self, mac_address: str, num_ports: int=4):
        super().__init__(mac_address, num_ports)

    # 将交换机buffer中的内容更新至对于的端口和队列中
    def flash(self):
        for egress_port_id, fragment_list in self.buffer.items():
            while fragment_list:
                fragment = fragment_list.pop(0)
                egress_port = self.get_ports()[egress_port_id]
                egress_port.enqueue(fragment)

    def __str__(self):
        return f"SW({self.get_mac_address()})"
