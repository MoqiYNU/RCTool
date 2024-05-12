# coding=gbk
import copy
import net as nt
import inner_utils as iu
import circle_utils as cu
'''
  定义网预处理工具类
'''


# 1.第i个网中插入一个开始和结束变迁-----------------------------------------------
def insert_start_end_trans(net_obj: nt.OpenNet, i):
    net = copy.deepcopy(net_obj)
    source_place = net.source.places[0]
    sink_place = net.sinks[0].places[0]
    source_postset = nt.get_postset(net.flows, source_place)
    sink_preset = nt.get_preset(net.flows, sink_place)
    # 插入的变迁及库所
    start_tran = 'ti{}'.format(i)
    start_place = 'pi{}'.format(i)
    end_place = 'po{}'.format(i)
    end_tran = 'to{}'.format(i)
    # 添加库所及变迁到net中
    net.add_places([start_place, end_place])
    net.add_inner_places([start_place, end_place])
    net.add_trans([start_tran, end_tran])
    net.label_map[start_tran] = start_tran
    net.label_map[end_tran] = end_tran
    # ps:开始变迁和结束变迁是瞬时的
    net.tran_delay_map[start_tran] = [0, 0]
    net.tran_delay_map[end_tran] = [0, 0]
    # 构建流关系
    net.add_flow(source_place, start_tran)
    net.add_flow(start_tran, start_place)
    for tran in source_postset:
        net.rov_flow(source_place, tran)
        net.add_flow(start_place, tran)
    net.add_flow(end_place, end_tran)
    net.add_flow(end_tran, sink_place)
    for tran in sink_preset:
        net.rov_flow(tran, sink_place)
        net.add_flow(tran, end_place)
    return net


# 2.每个网中并发块前后插入AND-split/join---------------------------------
def insert_and_split_join(net_obj: nt.OpenNet, i):
    net = copy.deepcopy(net_obj)
    index = 0
    for tran in net.trans:
        postset = nt.get_postset(net.flows, tran)
        inner_postset = list(set(postset).intersection(set(net.inner_places)))
        # 1.由tran引出了并发
        if len(inner_postset) > 1:
            and_place = 'pas{}{}'.format(i, index)
            and_tran = 'tas{}{}'.format(i, index)
            index += 1
            net.add_places([and_place])
            net.add_inner_places([and_place])
            net.add_trans([and_tran])
            net.label_map[and_tran] = and_tran
            # ps:添加and-join变迁是瞬时的
            net.tran_delay_map[and_tran] = [0, 0]
            # 构建流关系
            net.add_flow(tran, and_place)
            net.add_flow(and_place, and_tran)
            # Note:排除消息库所~~~~~~~~~~~~~~~~~~~~~~~
            for place in inner_postset:
                net.rov_flow(tran, place)
                net.add_flow(and_tran, place)
        preset = nt.get_preset(net.flows, tran)
        inner_preset = list(set(preset).intersection(set(net.inner_places)))
        # 2.由tran结束了并发
        if len(inner_preset) > 1:
            and_place = 'paj{}{}'.format(i, index)
            and_tran = 'taj{}{}'.format(i, index)
            print('test qi:', and_tran, tran)
            index += 1
            net.add_places([and_place])
            net.add_inner_places([and_place])
            net.add_trans([and_tran])
            net.label_map[and_tran] = and_tran
            # ps:添加and-join变迁是瞬时的
            net.tran_delay_map[and_tran] = [0, 0]
            # 构建流关系
            net.add_flow(and_tran, and_place)
            net.add_flow(and_place, tran)
            # Note:排除消息库所~~~~~~~~~~~~~~~~~~~~~~~~
            for place in inner_preset:
                net.rov_flow(place, tran)
                net.add_flow(place, and_tran)
    return net


# 3.在每个网中每个分支库所后插入一个锚点(需提前插入)---------------------------------
def insert_anchors(net_obj: nt.OpenNet, i):  #net_obj是网,i是参与组织的编号
    net = copy.deepcopy(net_obj)
    # 1.获取net中分支库所
    branch_tran_map = {}
    inner = iu.get_inner_net(net)
    branch_places = []
    to_graph = inner.to_graph()
    # Note:获取当前网中所有重新进入循环的back变迁集
    source = inner.source
    dfs_obj = cu.DFS()
    back_trans = dfs_obj.get_back_trans(source, to_graph)
    # print(back_trans)
    for place in inner.places:
        postset = nt.get_postset(inner.flows, place)
        branch_trans = list(set(postset) - set(back_trans))
        if len(branch_trans) > 1:
            branch_places.append(place)
            branch_tran_map[place] = branch_trans
    # 2.每个分支库所引出变迁前插入一个锚点
    index = 1
    # Note:i是参与组织的编号
    print('branch_places:', branch_places)
    for bp in branch_places:
        # 到分支变迁的循环back变迁
        branch_trans = branch_tran_map[bp]
        for bt in branch_trans:
            anchor_tran = 'at{}{}'.format(i, index)
            anchor_place = 'ap{}{}'.format(i, index)
            index += 1
            # 添加库所及变迁到net中
            net.add_places([anchor_place])
            net.add_inner_places([anchor_place])
            net.add_trans([anchor_tran])
            net.label_map[anchor_tran] = anchor_tran
            # ps:添加锚点是瞬时的
            net.tran_delay_map[anchor_tran] = [0, 0]
            # 更新流关系
            net.rov_flow(bp, bt)
            net.add_flow(bp, anchor_tran)
            net.add_flow(anchor_tran, anchor_place)
            net.add_flow(anchor_place, bt)
    return net
