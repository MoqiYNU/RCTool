from graphviz import Digraph
import net as nt


# 1.定义LTS(可达图)---------------------------------------------
class LTS(object):

    def __init__(self, start, ends, states, trans):
        self.start = start
        self.ends = ends
        self.states = states
        self.trans = trans

    def get_infor(self):
        return self.start, self.ends, self.states, self.trans

    # 获取lts中所有名字集(不重复)
    def get_labels(self):
        labels = set()
        for tran in self.trans:
            state_from, label, state_to = tran.get_infor()
            labels.add(label)
        return list(labels)

    # a)将可达图转换为lts(正确性验证)~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def rg_to_lts(self):
        index_marking_map = {}
        lts_start = 'S{}'.format(self.get_marking_index(self.start))
        lts_ends = []
        for end in self.ends:
            lts_ends.append('S{}'.format(self.get_marking_index(end)))
        lts_states = []
        for state in self.states:
            index = 'S{}'.format(self.get_marking_index(state))
            index_marking_map[index] = state
            # print(self.get_marking_index(state), '-------->',
            #       state.get_infor())
            lts_states.append(index)
        lts_trans = []
        for tran in self.trans:
            state_from, label, state_to = tran.get_infor()
            lts_state_from = 'S{}'.format(self.get_marking_index(state_from))
            lts_state_to = 'S{}'.format(self.get_marking_index(state_to))
            lts_trans.append(Tran(lts_state_from, label, lts_state_to))
        return LTS(lts_start, lts_ends, lts_states,
                   lts_trans), index_marking_map

    # b)将lts转换为dot文件~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def lts_to_dot(self):
        dot = Digraph('lts')
        # dot.graph_attr['rankdir'] = 'LR'
        for state in self.states:
            dot.node(name=state, shape='circle')
            # 如果该节点在终止状态集,变将shape写成doublecircle
            if state in self.ends:
                dot.node(name=state, shape='doublecircle')
            if state == self.start:
                dot.node(name=state, shape='circle')
                # 添加一个空节点，并将其颜色设置为白色
                dot.node(name='', color='white')
                dot.edge('', state, label='', arrowhead='normal')
        for tran in self.trans:
            state_from, label, state_to = tran.get_infor()
            dot.edge(state_from, state_to, label=label, arrowhead='normal')
        dot.view()

    # b)将lts转换为dot文件~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def lts_to_dot_flag(self, flag):
        dot = Digraph(flag)
        # dot.graph_attr['rankdir'] = 'LR'
        for state in self.states:
            dot.node(name=state, shape='circle')
            # 如果该节点在终止状态集,变将shape写成doublecircle
            if state in self.ends:
                dot.node(name=state, shape='doublecircle')
            if state == self.start:
                dot.node(name=state, shape='circle')
                # 添加一个空节点，并将其颜色设置为白色
                dot.node(name='', color='white')
                dot.edge('', state, label='', arrowhead='normal')
        for tran in self.trans:
            state_from, label, state_to = tran.get_infor()
            dot.edge(state_from, state_to, label=label, arrowhead='normal')
        dot.view()

    # c)将rg转换为dot文件~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def rg_to_dot(self):
        dot = Digraph('rg', format='jpg')
        # dot.graph_attr['rankdir'] = 'LR'
        # 设置dpi=600
        dot.graph_attr['dpi'] = '300'
        for state in self.states:
            new_state = 'S{}'.format(self.get_marking_index(state))
            print(new_state, '------>', state.get_infor())
            # Note:每个状态添加tips显示其标识
            str_pls = '[' + ', '.join(state.get_infor()) + ']'
            dot.node(name=new_state, shape='circle', tooltip=str_pls)
            # 如果该节点在终止状态集,变将shape写成doublecircle
            if nt.marking_is_exist(state, self.ends):
                new_state = 'S{}'.format(self.get_marking_index(state))
                dot.node(name=new_state, shape='doublecircle')
            if nt.equal_markings(state, self.start):
                new_state = 'S{}'.format(self.get_marking_index(state))
                dot.node(name=new_state, shape='circle')
                # 添加一个空节点，并将其颜色设置为白色
                dot.node(name='', color='white')
                dot.edge('', new_state, label='', arrowhead='normal')
        for tran in self.trans:
            state_from, label, state_to = tran.get_infor()
            new_state_from = 'S{}'.format(self.get_marking_index(state_from))
            new_state_to = 'S{}'.format(self.get_marking_index(state_to))
            dot.edge(new_state_from,
                     new_state_to,
                     label=label,
                     arrowhead='normal')
        dot.view(filename='rg.dot')

    # 返回可达图中标识在states中位置
    def get_marking_index(self, state):
        for index, temp_state in enumerate(self.states):
            if nt.equal_markings(state, temp_state):
                return index
        return -1


# 2.定义变迁---------------------------------------------
class Tran(object):

    def __init__(self, state_from, label, state_to):
        self.state_from = state_from
        self.label = label
        self.state_to = state_to

    def get_infor(self):
        return self.state_from, self.label, self.state_to
