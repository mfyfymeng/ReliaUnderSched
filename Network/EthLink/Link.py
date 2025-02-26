from Network.EthDevice import EthDeviceBase

class Link:
    def __init__(self, dev1: EthDeviceBase, port1: int, dev2: EthDeviceBase, port2: int):
        self.__start_dev = dev1
        self.__start_dev_port = port1
        self.__end_dev = dev2
        self.__end_dev_port = port2

    def get_start_dev(self):
        return self.__start_dev

    def get_end_dev(self):
        return self.__end_dev

