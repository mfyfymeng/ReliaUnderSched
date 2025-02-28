from Network.NetworkBase import *
from Simulation.Simulator import Simulator


if __name__ == '__main__':
    topo_file = 'Input/topology_info.json'
    app_file = 'Input/application_info.json'

    simulator = Simulator(topo_file, app_file)
    simulator.set_seed()

    # 设置端口采用的调度器或调度算法
    # SP  -- 严格优先级调度算法
    # WRR -- 加权轮询调度算法
    simulator.set_scheduler("WRR")

    simulator.run(100)
    simulator.print_statistic_info()

