from Network.NetworkBase import *


class Statistics:
    def __init__(self):
        self.app_info = {}
        self.created_flow = {}
        self.completed_flow = {}
        self.unfinished_flow = {}

    # 统计信息总览
    def print_statistics_info(self):
        print("==================== Statistic Info ====================")
        self.print_app_type()
        self.print_created_flow()
        self.print_completed_flow()
        self.print_unfinished_flow()

    # 网络中的业务类型
    def print_app_type(self):
        print(f"Application types: {list(self.app_info.keys())}")

    # 流实例的生成情况
    def print_created_flow(self):
        created_flows_num = []
        for flow_list in self.created_flow.values():
            created_flows_num.append(len(flow_list))
        print(f"Created flows num: {created_flows_num}")

    # 流实例的完成情况
    def print_completed_flow(self):
        completed_flows_num = []
        app_types = list(self.app_info.keys())
        for app_type in app_types:
            completed_flows_num.append(len(self.completed_flow.get(app_type, [])))
        print(f"Completed flows num: {completed_flows_num}")

    # 流实例的未完成情况
    def print_unfinished_flow(self):
        unfinished_flows_set = []
        unfinished_flows_num = []
        for app_type, flow_list in self.unfinished_flow.items():
            for flow in flow_list:
                unfinished_flows_set.append(flow)

        app_types = list(self.app_info.keys())
        for app_type in app_types:
            unfinished_flows_num.append(len(self.unfinished_flow.get(app_type, [])))

        if unfinished_flows_set:
            print(f"Unfinished flows num: {unfinished_flows_num}")
            for flow in unfinished_flows_set:
                print(f"id={flow.get_flow_id()}, App {flow.get_app().get_app_id()}, remaining {flow.remaining_size}")
        else:
            print("Unfinished flows: There are no unfinished flows.")

    def update_completed_flow(self, flow: Flow):
        app_type = flow.get_app().get_app_id()
        if app_type not in self.completed_flow:
            self.completed_flow[app_type] = []

        # 当流完成时，将流加入completed_flow中，并从unfinished_flow中移除
        self.completed_flow[app_type].append(flow)
        if app_type in self.unfinished_flow:
            self.unfinished_flow[app_type] = [f for f in self.unfinished_flow[app_type] if f.get_flow_id() != flow.get_flow_id()]

    def update_unfinished_flow(self, flow: Flow):
        app_type = flow.get_app().get_app_id()
        if app_type not in self.unfinished_flow:
            self.unfinished_flow[app_type] = []

        # 查找该流是否已经存在于未完成流的字典中
        unfinished_flow = next((f for f in self.unfinished_flow[app_type] if f.get_flow_id() == flow.get_flow_id()), None)
        if unfinished_flow:
            index = self.unfinished_flow[app_type].index(unfinished_flow)
            self.unfinished_flow[app_type][index] = flow
        else:
            self.unfinished_flow[app_type].append(flow)
