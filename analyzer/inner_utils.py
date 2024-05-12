# coding=gbk
import copy
from net_gen import gen_nets
import net as nt
from inner import InnerNet
from collections import Counter
import circle_utils as cu


# 1.获取单个组织的内网(交互变迁设为空,由组合获取)-----------------------------
def get_inner_net(net: nt.OpenNet):

    source, sinks = net.get_start_ends()
    places, inner_places, msg_places = net.get_places()
    res_places = net.res_places
    trans, rout_trans, label_map = net.get_trans()
    flows = net.get_flows()

    # a)源库所只有1个(Note:资源只在组合网的初始标识中)
    inner_net_source = source.get_infor()[0]

    # b)终止库所1个
    inner_net_sink = sinks[0].get_infor()[0]

    # c)确定流集
    inner_net_flows = []
    msg_res_places = msg_places + res_places
    for flow in flows:
        flow_from, flow_to = flow.get_infor()
        # 移除消息流和资源流
        if flow_from in msg_res_places or flow_to in msg_res_places:
            continue
        inner_net_flows.append(flow)

    # d)确定库所
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
    # ps:交互变迁集先设为[],由之后过程网组合确定
    inner_net.inter_trans = []
    return inner_net


# 2.依据XOR将单个组织的内网进行分解(Note:关键是获取分解后变迁集)-----------------------------
def decompose_inner_net(inner_net: InnerNet):

    # 1.获取每个split分出的变迁集~~~~~~~~~~~~~~~~~~~~~~~~~
    trans_in_each_split = []
    # 利用图获取split变迁集
    graph = inner_net.to_graph()
    # Note:获取当前网中所有进入和退出循环的变迁集
    source = inner_net.source
    dfs_obj = cu.DFS()
    # Note:同时考虑while循环和do-while循环
    back_trans = dfs_obj.get_back_trans(source, graph)
    print('back_trans: ', back_trans)
    places = inner_net.places
    for place in places:
        # Note:排除循环流
        postSet = set(nt.get_postset(inner_net.flows,
                                     place)) - set(back_trans)
        if len(postSet) > 1:
            trans_in_each_split.append([place, postSet])

    print('trans_in_each_split: ', trans_in_each_split)

    # 2.迭代计算获取分解后的内网(即执行路径)~~~~~~~~~~~~~~~~~~~~~~~~~
    exec_paths = []
    # 运行队列
    visiting_queue = [inner_net]
    # 迭代计算
    while visiting_queue:
        from_inner_net = visiting_queue.pop(0)
        # 判断当前内网是否能够分解
        result = can_decompose(trans_in_each_split, from_inner_net)
        # 2.1 若不能分解(即不含XOR)且未生成过,则将其添加到分解网列表中并跳过计算
        if result is None:
            if from_inner_net_exist(from_inner_net, exec_paths):
                continue
            exec_paths.append(from_inner_net)
            continue
        # 2.2a 若能分解,则首先获取每条split变迁引出的包
        print('split_trans: ', result[1])
        split_bags = gen_succ_bags(result, from_inner_net.flows)
        print('split_bags:', split_bags)
        trans_in_split_bags = []
        for split_bag in split_bags:
            trans_in_split_bags = trans_in_split_bags + split_bag
        # 2.2b 计算from_inner_net中除split变迁引出的包之外的迁移集
        rest_trans = list(
            set(from_inner_net.trans) - set(trans_in_split_bags))
        for split_bag in split_bags:
            # 分解后每个片段中的变迁集
            frag_trans = split_bag + rest_trans
            # 当前网中除片段中变迁外的其他变迁集(需移除)
            rov_trans = list(set(from_inner_net.trans) - set(frag_trans))
            net_copy = copy.deepcopy(from_inner_net)
            # 移除变迁及其关联的流
            net_copy.rov_objs(rov_trans)
            for rov_tran in rov_trans:
                net_copy.rov_flows_by_obj(rov_tran)
            # 进行迭代分解
            visiting_queue.append(net_copy)
    return exec_paths


# 判断from_inner_net是否包含一个trans_in_each_split,若含有则可分解
def can_decompose(trans_in_each_split, from_inner_net: InnerNet):
    for [place, split_trans] in trans_in_each_split:
        if set(split_trans) <= set(from_inner_net.trans):
            return [place, split_trans]
    return None


# 判断from_inner_net是否存在
def from_inner_net_exist(from_inner_net, dep_inner_nets):
    for dep_inner_net in dep_inner_nets:
        if Counter(from_inner_net.trans) == Counter(dep_inner_net.trans):
            return True
    return False


# 利用变迁扩展形成后继迁移包
def gen_succ_bags(result, flows):
    bags = []
    visited_trans = []
    branch_place = result[0]
    split_trans = result[1]
    for tran in split_trans:
        if tran in visited_trans:
            continue
        # 运行队列和已访问队列
        visiting_queue = [tran]
        visited_queue = [tran]
        # 迭代计算
        while visiting_queue:
            from_tran = visiting_queue.pop(0)
            to_places = nt.get_postset(flows, from_tran)
            to_trans = []
            for to_place in to_places:
                # Note:跳过引出split_trans的分支库所~~~~~~~~~~~~~~~~~~~~~~~~~
                if to_place == branch_place:
                    continue
                # Note:排除tran之外由xor引出的split变迁集
                rest_split_trans = set(split_trans) - set([tran])
                # Note:排除可能的分支迁移(可能有到split库所的环)
                to_trans = list(
                    set(to_trans + nt.get_postset(flows, to_place)) -
                    rest_split_trans)
            # 计算tran可达的后继迁移集(避免前后集重复)
            for to_tran in to_trans:
                if to_tran not in visited_queue:
                    visiting_queue.append(to_tran)
                    visited_queue.append(to_tran)
        # print('visited_queue:', tran, visited_queue)
        bags.append(visited_queue)
        # print(bags)
        visited_trans = visited_trans + visited_queue
    return bags


# -------------------------------测试---------------------------------#

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

    net = gen_nets('/Users/moqi/Desktop/临时文件/2023.xml')[1]
    inner_net = get_inner_net(net)
    inner_net.inner_to_dot('abc')
    dep_inner_nets = decompose_inner_net(inner_net)
    for i, dep_inner_net in enumerate(dep_inner_nets):
        dep_inner_net.print_infor()

    # print(gen_succ_bags(['T1'], inner_nets[0].flows))

# -------------------------------------------------------------------#
