from Network.NetworkBase import *
from Simulation.Simulator import Simulator


if __name__ == '__main__':
    topo_file = 'Input/topology_info.json'
    app_file = 'Input/application_info.json'

    simulator = Simulator(topo_file, app_file)
    simulator.set_seed()
    simulator.run(100)
    simulator.print_statistic_info()

