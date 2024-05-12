# coding=gbk
from collections import Counter
import net_gen as ng
import inner_utils as iu


# 1.�����ȡ����back��Ǩ����--------------------------------------------------
class DFS(object):

    def __init__(self):
        self.circles = []

    # �ݹ�DFS�ҳ�����ͼ�����еĻ�
    def dfs(self, start, graph):
        gen_list = []
        gen_list.append(start)
        vis_list = []
        while gen_list:
            # print('gen_list:', gen_list)
            last = gen_list[-1]
            # print('last:', last)
            # ����'#'���ɽ��ĺ��(Note:ĳЩ�������ֹ������û�к�̽��)
            if graph[last]:
                nodes = graph[last].split('#')
            else:
                nodes = []
            # print('nodes:', nodes)
            if nodes == [] or self.is_exist(nodes, gen_list):
                # ��ȡ��~~~~~~~~~~~~~~~~~~~~~~~~~~
                if nodes:
                    for node in nodes:
                        index = gen_list.index(node)
                        circle = gen_list[index:]
                        # ���δ�������Ļ�
                        if self.is_gen_circle(circle, self.circles):
                            continue
                        self.circles.append(circle)
                        print('circle:', circle)
                # print('path: ', gen_list)
                vis_list.append(last)
                gen_list.pop()
            else:
                unvis_node = self.first_unvis_node(nodes, vis_list, gen_list)
                if unvis_node is None:
                    vis_list.append(last)
                    gen_list.pop()
                    # Note:���÷���
                    self.reset_vis(last, nodes, vis_list, gen_list)
                    # print('gen_list', gen_list)
                else:
                    gen_list.append(unvis_node)

    # ��ȡdo-while��back��Ǩ,e.g ['P2', 'T3', 'P3', 'T4', 'P4', 'T6']
    def get_back_trans(self, start, graph):
        self.dfs(start, graph)
        back_trans = set()
        for circle in self.circles:
            back_trans.add(circle[-1])
        return list(back_trans)

    # �жϵ�ǰ���Ƿ������
    def is_gen_circle(self, circle, circles):
        for temp_circle in circles:
            if Counter(circle) == Counter(temp_circle):
                return True
        return False

    def is_exist(self, nodes, gen_list):
        for node in nodes:
            if node not in gen_list:
                return False
            else:
                continue
        return True

    def first_unvis_node(self, nodes, vis_list, gen_list):
        for node in nodes:
            # Note:���⵽֮ǰ�߹�����ѭ��
            if node in gen_list:
                continue
            if node not in vis_list:
                return node
        return None

    def reset_vis(self, last, nodes, vis_list, gen_list):
        for node in nodes:
            # Note:����Ԫ��Ҳ�迼����ѭ��(node == last)
            if node in gen_list or node == last:
                continue
            vis_list.remove(node)


# 2.ȷ������ĳ����Ǩ�Ƿ��ڻ���--------------------------------------------------
class DeterCircles(object):

    def __init__(self):
        # ����ѭ�����ѡ���ı���
        self.visited = []
        self.trace = []
        self.has_circle = False
        self.circles = []

    # �ݹ�DFS�ҳ�����ͼ�����еĻ�
    def dfs(self, start, graph):
        if (start in self.visited):
            if (start in self.trace):
                self.has_circle = True
                trace_index = self.trace.index(start)
                circle = []
                for i in range(trace_index, len(self.trace)):
                    circle.append(self.trace[i])
                    print(self.trace[i] + ' ', end='')
                self.circles.append(circle)
                print('\n', end='')
                return
            return

        self.visited.append(start)
        self.trace.append(start)

        if (start != ''):
            children = graph[start].split('#')
            for child in children:
                self.dfs(child, graph)
        self.trace.pop()

    # �ж�tran�Ƿ��ڻ���
    def is_in_circle(self, tran, graph):
        self.dfs(tran, graph)
        for circle in self.circles:
            if tran in circle:
                return True
        return False


# -------------------------------����---------------------------------#

if __name__ == '__main__':

    dfs_obj = DFS()
    net = ng.gen_nets('/Users/moqi/Desktop/New Petri net 112.xml')[0]
    inner = iu.get_inner_net(net)
    to_graph = inner.to_graph()
    # Note:��ȡ��ǰ�����������½���ѭ����back��Ǩ��
    source = inner.source
    dfs_obj.dfs(source, to_graph)
    print(dfs_obj.get_back_trans('P0', to_graph))

# -------------------------------------------------------------------#
