# coding=gbk
import copy
from net import Flow, Marking, OpenNet
import net_gen as ng
import net as nt
import inner_utils as iu
import random
from xml.dom.minidom import parse
import circle_utils as cu
import erp_utils as erpu
'''
  ����Ӧ����Ӧ���̹�����
  1.��������˳��,ѡ��,�����͵������(��link�ṹ);
  2.�����ṹֻ��repeat-until�ṹ;
  3.������ͬ��+�첽��;
  4.�漰ʱ����Ϣ.
'''


# 1a.���Ӧ����Ӧ����(ͬ��+�첽)-------------------------------------------------------
def get_compose_net(nets):
    # gen_sync_transΪ�ϲ������е��м�ͬ����Ǩ��
    gen_sync_trans = []
    net = compose_nets(nets, gen_sync_trans)
    print('gen_sync_trans: ', gen_sync_trans)
    net.print_infor()
    return net


# 1.1a.���bag���������---------------------------------------------
def compose_nets(nets, gen_sync_trans):
    if len(nets) == 0:
        print('no bag_nets exist, exit...')
        return
    if len(nets) == 1:
        return nets[0]
    else:
        net = compose_two_nets(nets[0], nets[1], gen_sync_trans)
        for i in range(2, len(nets)):
            net = compose_two_nets(net, nets[i], gen_sync_trans)
        return net


# �������������
def compose_two_nets(net1: OpenNet, net2: OpenNet, gen_sync_trans):

    # 1)����Դ����ֹ��ʶ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    source1, sinks1 = net1.get_start_ends()
    source2, sinks2 = net2.get_start_ends()
    source = Marking(source1.get_infor() + source2.get_infor())
    sinks = []
    for sink1 in sinks1:
        for sink2 in sinks2:
            sink = Marking(sink1.get_infor() + sink2.get_infor())
            sinks.append(sink)

    # 2)��������(�����ظ�)~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    places1, inner_places1, msg_places1 = net1.get_places()
    places2, inner_places2, msg_places2 = net2.get_places()
    places = list(set(places1 + places2))
    inner_places = list(set(inner_places1 + inner_places2))
    msg_places = list(set(msg_places1 + msg_places2))

    # 3)������Դ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    res_places1, res_property1, req_res_map1, rel_res_map1 = net1.get_res_places(
    )
    res_places2, res_property2, req_res_map2, rel_res_map2 = net2.get_res_places(
    )
    res_places = list(set(res_places1 + res_places2))
    shared_res = set(res_places1).intersection(set(res_places2))
    res_property = {}
    for res, pro in res_property1.items():
        res_property[res] = pro
    # ����������Դ
    for res, pro in res_property2.items():
        if res in shared_res:
            continue
        res_property[res] = pro
    # �ڲ�����Ǩ�й���
    req_res_map = {}
    rel_res_map = {}

    init_res = []
    init_res1 = net1.get_init_res()
    init_res2 = net2.get_init_res()
    for res in init_res1:
        init_res.append(res)
    # ����������Դ
    for res in init_res2:
        if res in shared_res:
            continue
        init_res.append(res)

    # 4)������Ǩ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    trans1, rout_trans1, tran_label_map1 = net1.get_trans()
    trans2, rout_trans2, tran_label_map2 = net2.get_trans()
    sync_trans1, sync_trans2 = get_sync_trans(net1, net2)
    trans = []
    tran_label_map = {}
    tran_delay_map = {}

    # a)net1��net2�з�ͬ����Ǩ
    for tran1 in trans1:
        if tran1 not in sync_trans1:
            trans.append(tran1)
            tran_label_map[tran1] = tran_label_map1[tran1]
            # ps:���úϲ���Ǩʱ����
            tran_delay_map[tran1] = net1.tran_delay_map[tran1]
            # net1�з�ͬ����Ǩ������/�ͷ���Դ
            req_res_map[tran1] = req_res_map1[tran1]
            rel_res_map[tran1] = rel_res_map1[tran1]
    for tran2 in trans2:
        if tran2 not in sync_trans2:
            trans.append(tran2)
            tran_label_map[tran2] = tran_label_map2[tran2]
            # ps:���úϲ���Ǩʱ����
            tran_delay_map[tran2] = net2.tran_delay_map[tran2]
            # net2�з�ͬ����Ǩ������/�ͷ���Դ
            req_res_map[tran2] = req_res_map2[tran2]
            rel_res_map[tran2] = rel_res_map2[tran2]

    # b)net1��net2��ͬ����Ǩ(Note:��������ͬ���ϲ���Ǩ,����һ����Ǩ���ԲμӶ��ͬ���)
    syncMap1 = []
    syncMap2 = []

    print('sync_trans: ', sync_trans1, sync_trans2)

    for sync_tran1 in sync_trans1:

        # sync_trans�洢net2����sync_tran1ͬ��(�����ͬ)��Ǩ�Ƽ�
        sync_trans_in_net2 = []

        for sync_tran2 in sync_trans2:
            if tran_label_map1[sync_tran1] == tran_label_map2[sync_tran2]:
                sync_trans_in_net2.append(sync_tran2)

        if sync_tran1 in gen_sync_trans:
            gen_sync_trans.remove(sync_tran1)

        for sync_tran in sync_trans_in_net2:

            if sync_tran in gen_sync_trans:
                gen_sync_trans.remove(sync_tran)

            # ͬ����ǨId�ϲ�:a_b
            gen_sync_tran = sync_tran1 + '_' + sync_tran
            trans.append(gen_sync_tran)
            tran_label_map[gen_sync_tran] = tran_label_map1[sync_tran1]
            # ps:���úϲ���Ǩʱ����
            tran_delay_map[gen_sync_tran] = net1.tran_delay_map[sync_tran1]

            # Note:�ϲ�ͬ����Ǩ�ж����Ǩ������/�ͷ���Դ~~~~~~~~~~~~~~~~~~~
            req_res_map[gen_sync_tran] = req_res_map1[
                sync_tran1] + req_res_map2[sync_tran]
            rel_res_map[gen_sync_tran] = rel_res_map1[
                sync_tran1] + rel_res_map2[sync_tran]

            gen_sync_trans.append(gen_sync_tran)

            syncMap1.append([sync_tran1, gen_sync_tran])
            syncMap2.append([sync_tran, gen_sync_tran])

    print('gen_sync_trans: ', gen_sync_trans)
    rout_trans = list(set(rout_trans1 + rout_trans2))

    # 5)��������ϵ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    flows = []
    flows1 = net1.get_flows()
    flows2 = net2.get_flows()

    for flow in flows1:

        flow_from, flow_to = flow.get_infor()

        if flow_from in sync_trans1:
            merge_trans = get_merge_trans(flow_from, syncMap1)
            for merge_tran in merge_trans:
                flows.append(Flow(merge_tran, flow_to))
        elif flow_to in sync_trans1:
            merge_trans = get_merge_trans(flow_to, syncMap1)
            for merge_tran in merge_trans:
                flows.append(Flow(flow_from, merge_tran))
        else:
            flows.append(flow)

    for flow in flows2:

        flow_from, flow_to = flow.get_infor()

        if flow_from in sync_trans2:
            merge_trans = get_merge_trans(flow_from, syncMap2)
            for merge_tran in merge_trans:
                flows.append(Flow(merge_tran, flow_to))
        elif flow_to in sync_trans2:
            merge_trans = get_merge_trans(flow_to, syncMap2)
            for merge_tran in merge_trans:
                flows.append(Flow(flow_from, merge_tran))
        else:
            flows.append(flow)

    openNet = OpenNet(source, sinks, places, trans, tran_label_map, flows)
    openNet.inner_places = inner_places
    openNet.msg_places = msg_places
    openNet.rout_trans = rout_trans
    openNet.init_res = init_res
    openNet.res_places = res_places
    openNet.res_property = res_property
    openNet.req_res_map = req_res_map
    openNet.rel_res_map = rel_res_map
    openNet.tran_delay_map = tran_delay_map
    return openNet


# ��ȡͬ���кϲ�Ǩ�Ƽ�
def get_merge_trans(tran, syncMap):
    merge_trans = []
    for item in syncMap:
        if item[0] == tran:
            merge_trans.append(item[1])
    return merge_trans


# �ֱ��ȡnet1��net2��ͬ��Ǩ�Ƽ�
def get_sync_trans(net1, net2):
    sync_trans1 = []
    sync_trans2 = []
    trans1, rout_trans1, label_map1 = net1.get_trans()
    trans2, rout_trans2, label_map2 = net2.get_trans()
    for tran1 in trans1:
        # �ų����Ʊ�Ǩ
        if tran1 in rout_trans1:
            continue
        if is_sync_tran(tran1, net1, net2):
            sync_trans1.append(tran1)
    for tran2 in trans2:
        # �ų����Ʊ�Ǩ
        if tran2 in rout_trans2:
            continue
        if is_sync_tran(tran2, net2, net1):
            sync_trans2.append(tran2)
    return sync_trans1, sync_trans2


# �ж�tran1�ǲ���ͬ����Ǩ
def is_sync_tran(tran1, net1, net2):
    trans1, rout_trans1, tran_label_map1 = net1.get_trans()
    trans2, rout_trans2, tran_label_map2 = net2.get_trans()
    label1 = tran_label_map1[tran1]
    for tran2 in trans2:
        # �ų����Ʊ�Ǩ
        if tran2 in rout_trans2:
            continue
        label2 = tran_label_map2[tran2]
        if label1 == label2:
            return True
    return False


# 1b.��úϲ�ִ��·��(�첽)------------------------------------------
def get_merge_exec_path(nets):
    merge_ep = merge_exec_paths(nets)
    merge_ep.print_infor()
    return merge_ep


# 1.1b.�첽�ϲ�ִ��·��---------------------------------------------
def merge_exec_paths(eps):
    if len(eps) == 0:
        print('no bag_nets exist, exit...')
        return
    if len(eps) == 1:
        return eps[0]
    else:
        merge_ep = merge_two_exec_paths(eps[0], eps[1])
        for i in range(2, len(eps)):
            merge_ep = merge_two_exec_paths(merge_ep, eps[i])
        return merge_ep


# �첽�ϲ�����ִ��·��
def merge_two_exec_paths(ep1: OpenNet, ep2: OpenNet):

    # 1)����Դ����ֹ��ʶ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    source1, sinks1 = ep1.get_start_ends()
    source = source1
    sinks = sinks1

    # 2)��������(�����ظ�)~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    places1, inner_places1, msg_places1 = ep1.get_places()
    places2, inner_places2, msg_places2 = ep2.get_places()
    places = list(set(places1 + places2))
    inner_places = list(set(inner_places1 + inner_places2))
    msg_places = list(set(msg_places1 + msg_places2))

    # 3)������Դ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    res_places1, res_property1, req_res_map1, rel_res_map1 = ep1.get_res_places(
    )
    res_places2, res_property2, req_res_map2, rel_res_map2 = ep2.get_res_places(
    )
    res_places = list(set(res_places1 + res_places2))
    shared_res = set(res_places1).intersection(set(res_places2))
    res_property = {}
    for res, pro in res_property1.items():
        res_property[res] = pro
    # ����������Դ
    for res, pro in res_property2.items():
        if res in shared_res:
            continue
        res_property[res] = pro
    # �ڲ�����Ǩ�й���
    req_res_map = {}
    rel_res_map = {}

    init_res = []
    init_res1 = ep1.get_init_res()
    init_res2 = ep2.get_init_res()
    for res in init_res1:
        init_res.append(res)
    # ����������Դ
    for res in init_res2:
        if res in shared_res:
            continue
        init_res.append(res)

    # 4)������Ǩ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    trans1, rout_trans1, tran_label_map1 = ep1.get_trans()
    trans2, rout_trans2, tran_label_map2 = ep2.get_trans()
    trans = []
    tran_label_map = {}
    tran_delay_map = {}

    # net1��net2�б�Ǩ
    for tran1 in trans1:
        trans.append(tran1)
        tran_label_map[tran1] = tran_label_map1[tran1]
        # ps:���úϲ���Ǩʱ����
        tran_delay_map[tran1] = ep1.tran_delay_map[tran1]
        # net1�з�ͬ����Ǩ������/�ͷ���Դ
        req_res_map[tran1] = req_res_map1[tran1]
        rel_res_map[tran1] = rel_res_map1[tran1]
    for tran2 in trans2:
        if tran2 in trans1:  #ps:�����ظ���Ǩ
            continue
        trans.append(tran2)
        tran_label_map[tran2] = tran_label_map2[tran2]
        # ps:���úϲ���Ǩʱ����
        tran_delay_map[tran2] = ep2.tran_delay_map[tran2]
        # net2�з�ͬ����Ǩ������/�ͷ���Դ
        req_res_map[tran2] = req_res_map2[tran2]
        rel_res_map[tran2] = rel_res_map2[tran2]

    rout_trans = list(set(rout_trans1 + rout_trans2))

    # 5)��������ϵ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    flows1 = ep1.get_flows()
    flows2 = ep2.get_flows()
    flows = flows1 + flows2

    merge_ep = OpenNet(source, sinks, places, trans, tran_label_map, [])
    merge_ep.inner_places = inner_places
    merge_ep.msg_places = msg_places
    merge_ep.rout_trans = rout_trans
    # ps:���ظ�������flows
    merge_ep.add_flows(flows)
    merge_ep.init_res = init_res
    merge_ep.res_places = res_places
    merge_ep.res_property = res_property
    merge_ep.req_res_map = req_res_map
    merge_ep.rel_res_map = rel_res_map
    merge_ep.tran_delay_map = tran_delay_map
    return merge_ep


# 2.�Ƴ��������ĳЩ��Ǩ-------------------------------------------------------
def rov_some_trans(comp_net: nt.OpenNet, rov_trans):

    comp_net_copy = copy.deepcopy(comp_net)

    # a)ȷ����Ǩ
    bag = list(set(comp_net_copy.trans) - set(rov_trans))
    bag_rout_trans = list(set(bag).intersection(set(comp_net_copy.rout_trans)))
    # Note:ȷ��bag�б�Ǩʱ����
    bag_tran_delay_map = {}
    for id, delay in comp_net_copy.tran_delay_map.items():
        if id in bag:
            bag_tran_delay_map[id] = delay
    bag_label_map = {}
    for id, label in comp_net_copy.label_map.items():
        if id in bag:
            bag_label_map[id] = label
    bag_req_res_map = {}
    bag_rel_res_map = {}
    for tran in bag:
        # ������ͷ���Դ��name��ʶ
        bag_req_res_map[tran] = comp_net_copy.req_res_map[tran]
        bag_rel_res_map[tran] = comp_net_copy.rel_res_map[tran]

    # b)ȷ�����Ϳ���(�ų���Դ����)
    bag_places = set()
    bag_inner_places = set()
    bag_msg_places = set()
    bag_flows = []
    flows = comp_net_copy.get_flows()
    for flow in flows:
        fl_from, fl_to = flow.get_infor()
        if fl_from in bag:  #fl_fromΪ��Ǩ
            bag_places.add(fl_to)
            if fl_to in comp_net_copy.inner_places:
                bag_inner_places.add(fl_to)
            if fl_to in comp_net_copy.msg_places:
                bag_msg_places.add(fl_to)
            bag_flows.append(flow)
        elif fl_to in bag:  #fl_toΪ��Ǩ
            bag_places.add(fl_from)
            if fl_from in comp_net_copy.inner_places:
                bag_inner_places.add(fl_from)
            if fl_from in comp_net_copy.msg_places:
                bag_msg_places.add(fl_from)
            bag_flows.append(flow)

    # c)ȷ����Դ
    bag_res_places = set()
    for value in bag_req_res_map.values():
        bag_res_places = bag_res_places | set(value)
    bag_res_property = {}
    for bag_res_place in bag_res_places:
        bag_res_property[bag_res_place] = comp_net_copy.res_property[
            bag_res_place]
    bag_init_res = [
        res for res in comp_net_copy.get_init_res() if res in bag_res_places
    ]

    # �����ɰ����ɵ���
    bag_net = nt.OpenNet(comp_net_copy.source, comp_net_copy.sinks,
                         list(bag_places), bag, bag_label_map, bag_flows)

    bag_net.inner_places = list(bag_inner_places)
    bag_net.msg_places = list(bag_msg_places)

    bag_net.rout_trans = bag_rout_trans

    # ��Դ��������
    bag_net.init_res = bag_init_res
    bag_net.res_places = list(bag_res_places)
    bag_net.res_property = bag_res_property
    print(bag_res_property)
    bag_net.req_res_map = bag_req_res_map
    bag_net.rel_res_map = bag_rel_res_map

    # Note:����ʱ��
    bag_net.tran_delay_map = bag_tran_delay_map

    return bag_net


# 3.��ִ��·������б�Ǩ��ȷ�����������ͶӰ(ͬ������ȷ��)-----------------------------------
def net_proj(path):

    nets = ng.gen_nets(path)
    comp_net = get_compose_net(nets)

    # ------------------���Ƚ���comp_net����Ϊһ����������------------------#
    init_marking = comp_net.source.get_infor()
    final_marking = comp_net.sinks[0].get_infor()

    comp_net.add_places(['i', 'o'])
    comp_net.add_trans(['ti', 'to'])
    comp_net.add_rout_trans(['ti', 'to'])
    comp_net.label_map['ti'] = 'ti'
    comp_net.tran_delay_map['ti'] = [0.0, 0.0]
    comp_net.label_map['to'] = 'to'
    comp_net.tran_delay_map['to'] = [0.0, 0.0]
    comp_net.req_res_map['ti'] = []
    comp_net.req_res_map['to'] = []
    comp_net.rel_res_map['ti'] = []
    comp_net.rel_res_map['to'] = []

    comp_net.add_flow('i', 'ti')
    for place in init_marking:
        comp_net.add_flow('ti', place)
    comp_net.add_flow('to', 'o')
    for place in final_marking:
        comp_net.add_flow(place, 'to')

    comp_net.source = nt.Marking(['i'])
    comp_net.sinks = [nt.Marking(['o'])]
    # comp_net.net_to_dot('comp_net')
    # ----------------------------------------------------------------#

    comp_net_trans, rout_trans, label_map = comp_net.get_trans()
    tran_delay_map = comp_net.tran_delay_map
    trans_in_exec_path_comp = compute_trans_in_exec_path_comp(path)

    proj_nets = []  # ����ͶӰ����

    for trans in trans_in_exec_path_comp:

        # 1.ȷ��ӳ����������еı�Ǩ��~~~~~~~~~~~~~~~~~~~~~~~~~~~
        trans_in_comp_net = []
        for tran in comp_net.trans:
            # a)�첽��Ǩ
            if tran.find('_') == -1:
                if tran in trans:
                    trans_in_comp_net.append(tran)
            else:  # b)ͬ����Ǩ
                sync_trans = tran.split('_')
                if set(sync_trans) <= set(trans):
                    trans_in_comp_net.append(tran)

        # 2.ȷ��trans_in_comp_netӳ�����~~~~~~~~~~~~~~~~~~~~
        bag = trans_in_comp_net + ['ti', 'to']  # ���ti��to
        # a)ȷ����Ǩ
        bag_rout_trans = list(set(bag).intersection(set(rout_trans)))
        # Note:ȷ��bag�б�Ǩʱ����
        bag_tran_delay_map = {}
        for id, delay in tran_delay_map.items():
            if id in bag:
                bag_tran_delay_map[id] = delay
        bag_tran_delay_map['ti'] = [0.0, 0.0]
        bag_tran_delay_map['to'] = [0.0, 0.0]
        bag_label_map = {}
        for id, label in label_map.items():
            if id in bag:
                bag_label_map[id] = label
        bag_req_res_map = {}
        bag_rel_res_map = {}
        for tran in bag:
            # ������ͷ���Դ��name��ʶ
            bag_req_res_map[tran] = comp_net.req_res_map[tran]
            bag_rel_res_map[tran] = comp_net.rel_res_map[tran]

        # b)ȷ�����Ϳ���(�ų���Դ����)
        bag_places = set()
        bag_inner_places = set()
        bag_msg_places = set()
        bag_flows = []
        flows = comp_net.get_flows()
        for flow in flows:
            fl_from, fl_to = flow.get_infor()
            if fl_from in bag:  #fl_fromΪ��Ǩ
                bag_places.add(fl_to)
                if fl_to in comp_net.inner_places:
                    bag_inner_places.add(fl_to)
                if fl_to in comp_net.msg_places:
                    bag_msg_places.add(fl_to)
                bag_flows.append(flow)
            elif fl_to in bag:  #fl_toΪ��Ǩ
                bag_places.add(fl_from)
                if fl_from in comp_net.inner_places:
                    bag_inner_places.add(fl_from)
                if fl_from in comp_net.msg_places:
                    bag_msg_places.add(fl_from)
                bag_flows.append(flow)

        # c)ȷ����Դ
        bag_res_places = set()
        for value in bag_req_res_map.values():
            bag_res_places = bag_res_places | set(value)
        bag_res_property = {}
        for bag_res_place in bag_res_places:
            bag_res_property[bag_res_place] = comp_net.res_property[
                bag_res_place]
        bag_init_res = [
            res for res in comp_net.get_init_res() if res in bag_res_places
        ]

        # d)ȷ��source��sink
        bag_source = nt.Marking(['i'])
        bag_sinks = [nt.Marking(['o'])]

        # �����ɰ����ɵ���
        bag_net = OpenNet(bag_source, bag_sinks, list(bag_places), bag,
                          bag_label_map, bag_flows)

        bag_net.inner_places = list(bag_inner_places)
        bag_net.msg_places = list(bag_msg_places)

        bag_net.rout_trans = bag_rout_trans

        # ��Դ��������
        bag_net.init_res = bag_init_res
        bag_net.res_places = list(bag_res_places)
        bag_net.res_property = bag_res_property
        print(bag_res_property)
        bag_net.req_res_map = bag_req_res_map
        bag_net.rel_res_map = bag_rel_res_map

        # Note:����ʱ��
        bag_net.tran_delay_map = bag_tran_delay_map

        print('proj net========================================')
        bag_net.print_infor()

        proj_nets.append(bag_net)

    return proj_nets, comp_net


# ����ִ��·������б�Ǩ��
def compute_trans_in_exec_path_comp(path):
    nets = ng.gen_nets(path)
    inner_nets = get_inner_nets(nets)
    index_array = []
    exec_paths_set = []
    for inner_net in inner_nets:
        exec_paths = iu.decompose_inner_net(inner_net)
        index_array.append(range(len(exec_paths)))
        exec_paths_set.append(exec_paths)
    prod = product(index_array)
    # �洢����ִ��·������еı�Ǩ��
    trans_in_exec_path_comp = []
    for elem in prod:
        # Note:index���ַ���
        indexs = elem.split(' ')
        trans = []
        for i in range(len(indexs)):
            exec_path = exec_paths_set[i][int(indexs[i])]
            trans = trans + exec_path.trans
        trans_in_exec_path_comp.append(trans)
    return trans_in_exec_path_comp


# ���������ϵĵѿ�����
def product(list_of_list):
    list1 = list_of_list[0]
    for tmp_list in list_of_list[1:]:
        list2 = tmp_list
        two_res_list = two(list1, list2)
        list1 = two_res_list
    return list1


def two(list1, list2):
    res_list = []
    for int1 in list1:
        for int2 in list2:
            res_list.append(str(int1) + ' ' + str(int2))
    return res_list


# 4.�ж�ʵ�����Ƿ�Ϸ�,����p��ǰ�����Ϊ��,��p��Դ����������------------------
#   Note:�ٶ�CERP����ȷ�Ĳſ��������ж�
def proj_net_is_legal(proj_net: nt.OpenNet):
    start_end_places = []
    source = proj_net.source
    sinks = proj_net.sinks
    start_end_places = start_end_places + source.places
    for sink in sinks:
        start_end_places = start_end_places + sink.places
    flows = proj_net.flows
    for place in proj_net.places:
        if len(nt.get_preset(flows, place)) == 0 or len(
                nt.get_postset(flows, place)) == 0:
            if place not in start_end_places:
                return False
    return True


# 5.��ȡӦ����Ӧ��ÿ����֯������-------------------------------------------
def get_inner_nets(nets):
    inner_nets = []
    compose_net = get_compose_net(nets)
    # 1.ͬ����Ǩ��
    sync_inter_trans = get_sync_inter_trans(compose_net)
    for net in nets:
        inner_net = iu.get_inner_net(net)
        # 2.�첽��Ǩ��
        asyn_inter_trans = net.get_asyn_inter_trans()
        inner_net.add_inter_trans(asyn_inter_trans)
        trans = net.trans
        inner_net.add_inter_trans(
            list(set(sync_inter_trans).intersection(set(trans))))
        inner_nets.append(inner_net)
    return inner_nets


# ��ȡ������е�ͬ����Ǩ��
def get_sync_inter_trans(net: nt.OpenNet):
    syn_inter_trans = []
    trans = net.trans
    for tran in trans:
        if tran.find('_') != -1:
            merge_trans = tran.split("_")
            syn_inter_trans += merge_trans
    # �����ظ���ͬ����Ǩ(ps:һ����Ǩ���Բ�����ͬ������)
    return list(set(syn_inter_trans))


# 6.�������б�Ǩ��Ӧ�������-------------------------------------------
def gen_casual_set(trans, flows, back_trans):
    casual_tran_map = {}
    for tran in trans:
        # ���ж��к��ѷ��ʶ���
        visiting_queue = [tran]
        # Note:������������Լ�~~~~~~~~~~~~~~~~~
        visited_queue = []
        # ��������
        while visiting_queue:
            from_tran = visiting_queue.pop(0)
            from_places = nt.get_preset(flows, from_tran)
            casual_trans = []
            for from_place in from_places:
                casual_trans = list(
                    set(casual_trans + nt.get_preset(flows, from_place)))
            # Note:�ų�back_trans!!!
            casual_trans = list(set(casual_trans) - set(back_trans))
            # ����tran�����Ǩ�Ƽ�(����ǰ���ظ�)
            for casual_tran in casual_trans:
                if casual_tran not in visited_queue:
                    visiting_queue.append(casual_tran)
                    visited_queue.append(casual_tran)
        # print('visited_queue:', tran, visited_queue)
        casual_tran_map[tran] = visited_queue
        # print(bags)
    return casual_tran_map


# 7.����CERP������Back��Ǩ-------------------------------------------
def back_trans_in_CERP(path):
    nets = ng.gen_nets(path)
    inner_nets = get_inner_nets(nets)
    back_trans = []
    for inner_net in inner_nets:
        to_graph = inner_net.to_graph()
        # Note:��ȡ��ǰ��������ѭ���е�back��Ǩ��
        source = inner_net.source
        dfs_obj = cu.DFS()
        back_trans = back_trans + dfs_obj.get_back_trans(source, to_graph)
    return back_trans


# 8.����CERP������and split/join��Ǩ-------------------------------------------
def concurrent_trans_in_CERP(path):
    nets = ng.gen_nets(path)
    inner_nets = get_inner_nets(nets)
    con_trans = []
    for inner_net in inner_nets:
        flows = inner_net.flow
        for tran in inner_net.trans:
            if len(nt.get_preset(flows, tran)) > 1 or len(
                    nt.get_postset(flows, tran)) > 1:
                con_trans.append(tran)
    return con_trans


# 9.������ӱ�Ǩ��Delay(ps:ͬ����ǨDelayһ��)-------------------------------------------
def add_tran_delay(path):
    nets = ng.gen_nets(path)
    comp_net = get_compose_net(nets)
    max_set = max_sync_trans_set(get_sync_trans_set(comp_net))
    gen_delay_list = []
    for i in range(len(max_set)):
        min_delay, max_delay = gen_delay()
        gen_delay_list.append([min_delay, max_delay])
    print('Delay test:', max_set, gen_delay_list)
    domTree = parse(path)
    # �ĵ���Ԫ��
    root_node = domTree.documentElement
    tran_elems = root_node.getElementsByTagName('transition')
    for tran_elem in tran_elems:
        id = tran_elem.getAttribute('id').strip()
        index = get_index(id, max_set)
        [min_delay, max_delay] = gen_delay_list[index]
        tran_elem.getElementsByTagName(
            'minDelay')[0].childNodes[0].data = min_delay
        tran_elem.getElementsByTagName(
            'maxDelay')[0].childNodes[0].data = max_delay
    with open(path, 'w') as f:
        # ���� - ���� - ����
        domTree.writexml(f, addindent='  ', encoding='ISO-8859-1')


# ��󻯲�����ͬ����Ǩ��
def max_sync_trans_set(sync_trans_set):
    max_set = []
    while sync_trans_set:
        first_sync_trans = sync_trans_set.pop(0)
        remaing_sync_trans_set = []
        for sync_trans in sync_trans_set:
            if set(first_sync_trans) & set(sync_trans):
                first_sync_trans += sync_trans
            else:
                remaing_sync_trans_set.append(sync_trans)
        max_set.append(list(set(first_sync_trans)))
        sync_trans_set = remaing_sync_trans_set
    return max_set


# ������������б�Ǩ����ͬ��"_"���зֽ�
def get_sync_trans_set(comp_net: nt.OpenNet):
    sync_trans_set = []
    for tran in comp_net.trans:
        if tran.find('_') != -1:
            merge_trans = tran.split("_")
            sync_trans_set.append(merge_trans)
        else:
            sync_trans_set.append([tran])
    return sync_trans_set


# ������Ǩʱ����(ps:�������)
def gen_delay():
    # min_delay = random.randint(0, 9)
    min_delay = random.randint(3, 6)
    max_delay = -1
    while max_delay < min_delay:
        # max_delay = random.randint(0, 9)
        max_delay = random.randint(3, 6)
    return min_delay, max_delay


# ��ȡ��Ǩtran��index
def get_index(tran, max_set):
    for index, trans in enumerate(max_set):
        if tran in trans:
            return index
    return -1


# -------------------------------����---------------------------------#

if __name__ == '__main__':

    # proj_nets, comp_net = net_proj('/Users/moqi/Desktop/��ʱ�ļ�/2023.xml')

    # for index, proj_net in enumerate(proj_nets):
    #     proj_net.net_to_dot(str(index), True)

    # nets = ng.gen_nets('/Users/moqi/Desktop/��ʱ�ļ�/2023.xml')
    # nets = ng.gen_nets('/Users/moqi/Desktop/��ʱ�ļ�/ԭʼģ��/Ca-2.xml')
    # comp_net = get_compose_net(nets)
    # # comp_net.net_to_dot('abc', True)
    # print('partner, places, trans:', len(nets), len(comp_net.places),
    #       len(comp_net.trans))

    # max_set = max_sync_trans_set([['a', 'b', 'c'], ['a', 'd'], ['e', 'f'],
    #                               ['g', 'h'], ['k']])
    # print(max_set)

    add_tran_delay('/Users/moqi/Desktop/ԭʼģ��/ԭʼ����/Ca-22.xml')

    # proj_nets, comp_net = net_proj(
    #     '/Users/moqi/Desktop/ԭʼģ��/�鵵/ԭʼģ��/Ca-22.xml')
    # comp_net.net_to_dot('22', True)

# -------------------------------------------------------------------#
