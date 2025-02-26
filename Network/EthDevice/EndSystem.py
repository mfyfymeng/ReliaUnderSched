from .EthDeviceBase import EthDeviceBase


class EndSystem(EthDeviceBase):
    def __init__(self, mac_address: str, num_ports: int=2):
        super().__init__(mac_address, num_ports)

    def __str__(self):
        return f"ES({self.get_mac_address()})"