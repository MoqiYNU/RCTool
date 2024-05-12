# coding=gbk
import copy
from net_gen import gen_nets
import net as nt
from inner import InnerNet
from collections import Counter
import circle_utils as cu


# 1.��ȡ������֯������(������Ǩ��Ϊ��,����ϻ�ȡ)-----------------------------
def get_inner_net(net: nt.OpenNet):

    source, sinks = net.get_start_ends()
    places, inner_places, msg_places = net.get_places()
    res_places = net.res_places
    trans, rout_trans, label_map = net.get_trans()
    flows = net.get_flows()

    # a)Դ����ֻ��1��(Note:��Դֻ��������ĳ�ʼ��ʶ��)
    inner_net_source = source.get_infor()[0]

    # b)��ֹ����1��
    inner_net_sink = sinks[0].get_infor()[0]

    # c)ȷ������
    inner_net_flows = []
    msg_res_places = msg_places + res_places
    for flow in flows:
        flow_from, flow_to = flow.get_infor()
        # �Ƴ���Ϣ������Դ��
        if flow_from in msg_res_places or flow_to in msg_res_places:
            continue
        inner_net_flows.append(flow)

    # d)ȷ������
    inner_net_places = set()
    for flow in inner_net_flows:
        flow_from, flow_to = flow.get_infor()
        if flow_from in places:
            inner_net_places.add(flow_from)
        if flow_to in places:
            inner_net_places.add(flow_to)

    inner_net = InnerNet(
        inner_net_source,
        inner_net_sink,
        list(inner_net_places),
        trans,
        label_map,
        inner_net_flows,
    )
    inner_net.rout_trans = rout_trans
    # ps:������Ǩ������Ϊ[],��֮����������ȷ��
    inner_net.inter_trans = []
    return inner_net


# 2.����XOR��������֯���������зֽ�(Note:�ؼ��ǻ�ȡ�ֽ���Ǩ��)-----------------------------
def decompose_inner_net(inner_net: InnerNet):

    # 1.��ȡÿ��split�ֳ��ı�Ǩ��~~~~~~~~~~~~~~~~~~~~~~~~~
    trans_in_each_split = []
    # ����ͼ��ȡsplit��Ǩ��
    graph = inner_net.to_graph()
    # Note:��ȡ��ǰ�������н�����˳�ѭ���ı�Ǩ��
    source = inner_net.source
    dfs_obj = cu.DFS()
    # Note:ͬʱ����whileѭ����do-whileѭ��
    back_trans = dfs_obj.get_back_trans(source, graph)
    print('back_trans: ', back_trans)
    places = inner_net.places
    for place in places:
        # Note:�ų�ѭ����
        postSet = set(nt.get_postset(inner_net.flows,
                                     place)) - set(back_trans)
        if len(postSet) > 1:
            trans_in_each_split.append([place, postSet])

    print('trans_in_each_split: ', trans_in_each_split)

    # 2.���������ȡ�ֽ�������(��ִ��·��)~~~~~~~~~~~~~~~~~~~~~~~~~
    exec_paths = []
    # ���ж���
    visiting_queue = [inner_net]
    # ��������
    while visiting_queue:
        from_inner_net = visiting_queue.pop(0)
        # �жϵ�ǰ�����Ƿ��ܹ��ֽ�
        result = can_decompose(trans_in_each_split, from_inner_net)
        # 2.1 �����ֽܷ�(������XOR)��δ���ɹ�,������ӵ��ֽ����б��в���������
        if result is None:
            if from_inner_net_exist(from_inner_net, exec_paths):
                continue
            exec_paths.append(from_inner_net)
            continue
        # 2.2a ���ֽܷ�,�����Ȼ�ȡÿ��split��Ǩ�����İ�
        print('split_trans: ', result[1])
        split_bags = gen_succ_bags(result, from_inner_net.flows)
        print('split_bags:', split_bags)
        trans_in_split_bags = []
        for split_bag in split_bags:
            trans_in_split_bags = trans_in_split_bags + split_bag
        # 2.2b ����from_inner_net�г�split��Ǩ�����İ�֮���Ǩ�Ƽ�
        rest_trans = list(
            set(from_inner_net.trans) - set(trans_in_split_bags))
        for split_bag in split_bags:
            # �ֽ��ÿ��Ƭ���еı�Ǩ��
            frag_trans = split_bag + rest_trans
            # ��ǰ���г�Ƭ���б�Ǩ���������Ǩ��(���Ƴ�)
            rov_trans = list(set(from_inner_net.trans) - set(frag_trans))
            net_copy = copy.deepcopy(from_inner_net)
            # �Ƴ���Ǩ�����������
            net_copy.rov_objs(rov_trans)
            for rov_tran in rov_trans:
                net_copy.rov_flows_by_obj(rov_tran)
            # ���е����ֽ�
            visiting_queue.append(net_copy)
    return exec_paths


# �ж�from_inner_net�Ƿ����һ��trans_in_each_split,��������ɷֽ�
def can_decompose(trans_in_each_split, from_inner_net: InnerNet):
    for [place, split_trans] in trans_in_each_split:
        if set(split_trans) <= set(from_inner_net.trans):
            return [place, split_trans]
    return None


# �ж�from_inner_net�Ƿ����
def from_inner_net_exist(from_inner_net, dep_inner_nets):
    for dep_inner_net in dep_inner_nets:
        if Counter(from_inner_net.trans) == Counter(dep_inner_net.trans):
            return True
    return False


# ���ñ�Ǩ��չ�γɺ��Ǩ�ư�
def gen_succ_bags(result, flows):
    bags = []
    visited_trans = []
    branch_place = result[0]
    split_trans = result[1]
    for tran in split_trans:
        if tran in visited_trans:
            continue
        # ���ж��к��ѷ��ʶ���
        visiting_queue = [tran]
        visited_queue = [tran]
        # ��������
        while visiting_queue:
            from_tran = visiting_queue.pop(0)
            to_places = nt.get_postset(flows, from_tran)
            to_trans = []
            for to_place in to_places:
                # Note:��������split_trans�ķ�֧����~~~~~~~~~~~~~~~~~~~~~~~~~
                if to_place == branch_place:
                    continue
                # Note:�ų�tran֮����xor������split��Ǩ��
                rest_split_trans = set(split_trans) - set([tran])
                # Note:�ų����ܵķ�֧Ǩ��(�����е�split�����Ļ�)
                to_trans = list(
                    set(to_trans + nt.get_postset(flows, to_place)) -
                    rest_split_trans)
            # ����tran�ɴ�ĺ��Ǩ�Ƽ�(����ǰ���ظ�)
            for to_tran in to_trans:
                if to_tran not in visited_queue:
                    visiting_queue.append(to_tran)
                    visited_queue.append(to_tran)
        # print('visited_queue:', tran, visited_queue)
        bags.append(visited_queue)
        # print(bags)
        visited_trans = visited_trans + visited_queue
    return bags


# -------------------------------����---------------------------------#

if __name__ == '__main__':

    # nets = gen_nets('/Users/moqi/Desktop/Petri net 1.xml')
    # inner_net = get_inner_net(nets[1])
    # tree_links, net_copy = rov_sync_links(inner_net)
    # # print(tree_links)
    # final_net = rov_redu_places(net_copy)
    # final_net.print_infor()
    # # final_net.inner_to_dot()
    # # print(inner_net.gen_tree_links())
    # # print(inner_net.to_graph())
    # # print(inner_net.to_reserve_graph())

    # nets = gen_nets('/Users/moqi/Desktop/New Petri net 1 2.xml')
    # inner_nets = get_inner_nets(nets)
    # # for inner_net in inner_nets:
    # #     inner_net.print_infor()
    # dep_inner_nets = decompose_inner_net(inner_nets[0])
    # print('size: ', len(dep_inner_nets))
    # for dep_inner_net in dep_inner_nets:
    #     dep_inner_net.print_infor()

    net = gen_nets('/Users/moqi/Desktop/��ʱ�ļ�/2023.xml')[1]
    inner_net = get_inner_net(net)
    inner_net.inner_to_dot('abc')
    dep_inner_nets = decompose_inner_net(inner_net)
    for i, dep_inner_net in enumerate(dep_inner_nets):
        dep_inner_net.print_infor()

    # print(gen_succ_bags(['T1'], inner_nets[0].flows))

# -------------------------------------------------------------------#
