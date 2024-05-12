# coding=gbk
import copy
import net as nt
import inner_utils as iu
import circle_utils as cu
'''
  ������Ԥ��������
'''


# 1.��i�����в���һ����ʼ�ͽ�����Ǩ-----------------------------------------------
def insert_start_end_trans(net_obj: nt.OpenNet, i):
    net = copy.deepcopy(net_obj)
    source_place = net.source.places[0]
    sink_place = net.sinks[0].places[0]
    source_postset = nt.get_postset(net.flows, source_place)
    sink_preset = nt.get_preset(net.flows, sink_place)
    # ����ı�Ǩ������
    start_tran = 'ti{}'.format(i)
    start_place = 'pi{}'.format(i)
    end_place = 'po{}'.format(i)
    end_tran = 'to{}'.format(i)
    # ��ӿ�������Ǩ��net��
    net.add_places([start_place, end_place])
    net.add_inner_places([start_place, end_place])
    net.add_trans([start_tran, end_tran])
    net.label_map[start_tran] = start_tran
    net.label_map[end_tran] = end_tran
    # ps:��ʼ��Ǩ�ͽ�����Ǩ��˲ʱ��
    net.tran_delay_map[start_tran] = [0, 0]
    net.tran_delay_map[end_tran] = [0, 0]
    # ��������ϵ
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


# 2.ÿ�����в�����ǰ�����AND-split/join---------------------------------
def insert_and_split_join(net_obj: nt.OpenNet, i):
    net = copy.deepcopy(net_obj)
    index = 0
    for tran in net.trans:
        postset = nt.get_postset(net.flows, tran)
        inner_postset = list(set(postset).intersection(set(net.inner_places)))
        # 1.��tran�����˲���
        if len(inner_postset) > 1:
            and_place = 'pas{}{}'.format(i, index)
            and_tran = 'tas{}{}'.format(i, index)
            index += 1
            net.add_places([and_place])
            net.add_inner_places([and_place])
            net.add_trans([and_tran])
            net.label_map[and_tran] = and_tran
            # ps:���and-join��Ǩ��˲ʱ��
            net.tran_delay_map[and_tran] = [0, 0]
            # ��������ϵ
            net.add_flow(tran, and_place)
            net.add_flow(and_place, and_tran)
            # Note:�ų���Ϣ����~~~~~~~~~~~~~~~~~~~~~~~
            for place in inner_postset:
                net.rov_flow(tran, place)
                net.add_flow(and_tran, place)
        preset = nt.get_preset(net.flows, tran)
        inner_preset = list(set(preset).intersection(set(net.inner_places)))
        # 2.��tran�����˲���
        if len(inner_preset) > 1:
            and_place = 'paj{}{}'.format(i, index)
            and_tran = 'taj{}{}'.format(i, index)
            print('test qi:', and_tran, tran)
            index += 1
            net.add_places([and_place])
            net.add_inner_places([and_place])
            net.add_trans([and_tran])
            net.label_map[and_tran] = and_tran
            # ps:���and-join��Ǩ��˲ʱ��
            net.tran_delay_map[and_tran] = [0, 0]
            # ��������ϵ
            net.add_flow(and_tran, and_place)
            net.add_flow(and_place, tran)
            # Note:�ų���Ϣ����~~~~~~~~~~~~~~~~~~~~~~~~
            for place in inner_preset:
                net.rov_flow(place, tran)
                net.add_flow(place, and_tran)
    return net


# 3.��ÿ������ÿ����֧���������һ��ê��(����ǰ����)---------------------------------
def insert_anchors(net_obj: nt.OpenNet, i):  #net_obj����,i�ǲ�����֯�ı��
    net = copy.deepcopy(net_obj)
    # 1.��ȡnet�з�֧����
    branch_tran_map = {}
    inner = iu.get_inner_net(net)
    branch_places = []
    to_graph = inner.to_graph()
    # Note:��ȡ��ǰ�����������½���ѭ����back��Ǩ��
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
    # 2.ÿ����֧����������Ǩǰ����һ��ê��
    index = 1
    # Note:i�ǲ�����֯�ı��
    print('branch_places:', branch_places)
    for bp in branch_places:
        # ����֧��Ǩ��ѭ��back��Ǩ
        branch_trans = branch_tran_map[bp]
        for bt in branch_trans:
            anchor_tran = 'at{}{}'.format(i, index)
            anchor_place = 'ap{}{}'.format(i, index)
            index += 1
            # ��ӿ�������Ǩ��net��
            net.add_places([anchor_place])
            net.add_inner_places([anchor_place])
            net.add_trans([anchor_tran])
            net.label_map[anchor_tran] = anchor_tran
            # ps:���ê����˲ʱ��
            net.tran_delay_map[anchor_tran] = [0, 0]
            # ��������ϵ
            net.rov_flow(bp, bt)
            net.add_flow(bp, anchor_tran)
            net.add_flow(anchor_tran, anchor_place)
            net.add_flow(anchor_place, bt)
    return net
