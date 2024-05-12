from graphviz import Digraph
from net import Flow
import net as nt


# 1.定义内网----------------------------------------------------------
class InnerNet(object):

    def __init__(self, source, sink, places, trans, label_map, flows):
        self.source = source
        self.sink = sink
        self.places = places
        self.trans = trans
        # 路由变迁和交互变迁(ps:交互需通过过程网的组合获得)
        self.rout_trans = []
        self.inter_trans = []
        self.label_map = label_map
        self.flows = flows

    # 1)Utils方法~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def get_start_end(self):
        return self.source, self.sink

    # 添加库所及变迁
    def add_trans(self, ts):
        self.trans = list(set(self.trans + ts))

    def add_places(self, pls):
        self.places = list(set(self.places + pls))

    # 添加交互变迁集
    def add_inter_trans(self, its):
        self.inter_trans = list(set(self.inter_trans + its))

    # 移除库收
    def rov_place(self, pl):
        self.places.remove(pl)

    # 移除多个库收
    def rov_places(self, pls):
        for pl in pls:
            for place in self.places[::-1]:
                if pl == place:
                    self.places.remove(place)
                    break

    # 移除多条变迁
    def rov_trans(self, trs):
        for tr in trs:
            for tran in self.trans[::-1]:
                if tr == tran:
                    self.trans.remove(tran)
                    break

    # 添加流
    def add_flow(self, flow_from, flow_to):
        self.flows.append(Flow(flow_from, flow_to))

    def add_flows(self, fls):
        self.flows = self.flows + fls

    # 移除库所/变迁(用于生成过程树)
    def rov_objs(self, objs):
        for obj in objs:
            if obj in self.places:
                self.places.remove(obj)
            if obj in self.trans:
                self.trans.remove(obj)

    # 移除库所/变迁所关联的流集
    def rov_flows_by_obj(self, obj):
        # Note:********避免跳过for循环中相邻的待删除元素****************
        for flow in self.flows[::-1]:
            fl_from, fl_to = flow.get_infor()
            if fl_from == obj or fl_to == obj:
                self.flows.remove(flow)

    # 移除流
    def rov_flow(self, flow_from, flow_to):
        # Note:********避免跳过for循环中相邻的待删除元素****************
        for flow in self.flows[::-1]:
            fl_from, fl_to = flow.get_infor()
            if fl_from == flow_from and fl_to == flow_to:
                self.flows.remove(flow)
                break

    # 利用前/后集计算网对应的有向图(计算块)~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def to_graph(self):
        graph = {}
        for place in self.places:
            succ_nodes = '#'.join(nt.get_postset(self.flows, place))
            graph[place] = succ_nodes
        for tran in self.trans:
            succ_nodes = '#'.join(nt.get_postset(self.flows, tran))
            graph[tran] = succ_nodes
        return graph

    def to_reserve_graph(self):
        graph = {}
        for place in self.places:
            pre_nodes = '#'.join(nt.get_preset(self.flows, place))
            graph[place] = pre_nodes
        for tran in self.trans:
            pre_nodes = '#'.join(nt.get_preset(self.flows, tran))
            graph[tran] = pre_nodes
        return graph

    # 2)控制台打印网信息~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def print_infor(self):

        print(
            '\n=============================================================================='
        )
        print(
            '                                Inner Net Infor                                 '
        )
        print(
            '------------------------------------------------------------------------------'
        )

        # a)将网中元素转换为字符串=================================================
        infor = []

        infor.append(['Source', self.source])

        infor.append(['Sinks', self.sink])

        str_pls = '[' + ', '.join(self.places) + ']'
        infor.append(['Places', str_pls])

        str_trans = '[' + ', '.join(self.trans) + ']'
        infor.append(['Trans', str_trans])

        str_rts = '[' + ', '.join(self.rout_trans) + ']'
        infor.append(['Rout Trans', str_rts])

        lm_list = []
        for tran, label in self.label_map.items():
            lm_list.append(tran + ': ' + label)
        str_lm = '{' + ', '.join(lm_list) + '}'
        infor.append(['Label Map', str_lm])

        flow_list = []
        for flow in self.flows:
            fl_from, fl_to = flow.get_infor()
            flow_list.append('(' + fl_from + ', ' + fl_to + ')')
        str_fls = '{' + ', '.join(flow_list) + '}'
        infor.append(['Flows', str_fls])

        # b)格式化字符串=================================================
        len_list = [len(x[0]) for x in infor]
        offset = max(len_list) + 5
        for item in infor:
            lines = int(len(item[1]) / 52)
            if lines < 1:
                print("%s: %s" % (item[0].ljust(offset), item[1]))
            else:
                line_str = []
                for i in range(lines + 1):
                    val = item[1][i * 52:(i + 1) * 51 + i + 1]
                    if i == 0:
                        line_str.append(val)
                    else:
                        # Note:第一行之后的每行前面添加21个空格
                        line_str.append(' ' * 21 + val)
                print("%s: %s" % (item[0].ljust(offset), '\n'.join(line_str)))

        print(
            '=============================================================================='
        )

    # 3)将内网转换为dot文件~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def inner_to_dot(self, name):
        dot = Digraph(filename=name, format='jpg')
        dot.graph_attr['rankdir'] = 'LR'
        for place in self.places:
            dot.node(name=place, shape='circle')
            # 汇库所为绿色加粗边框
            if place == self.sink:
                dot.node(name=place,
                         shape='circle',
                         style='bold',
                         color='chartreuse3')
        for tran in self.trans:
            dot.node(name=tran, shape='box')
            # 可约变迁(既不是交互变迁也不是控制变迁)为砖红色加粗边框
            if tran not in self.rout_trans and tran not in self.inter_trans:
                dot.node(name=tran, shape='box', style='bold', color='coral2')
        for flow in self.flows:
            fl_from, fl_to = flow.get_infor()
            dot.edge(fl_from, fl_to, arrowhead='normal')

        dot.view()
