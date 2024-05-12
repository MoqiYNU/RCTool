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
  定义应急响应过程工具类
  1.控制流由顺序,选择,并发和迭代组成(无link结构);
  2.迭代结构只含repeat-until结构;
  3.交互是同步+异步的;
  4.涉及时间信息.
'''


# 1a.组合应急响应过程(同步+异步)-------------------------------------------------------
def get_compose_net(nets):
    # gen_sync_trans为合并过程中的中间同步变迁集
    gen_sync_trans = []
    net = compose_nets(nets, gen_sync_trans)
    print('gen_sync_trans: ', gen_sync_trans)
    net.print_infor()
    return net


# 1.1a.组合bag构建组合网---------------------------------------------
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


# 组合两个开放网
def compose_two_nets(net1: OpenNet, net2: OpenNet, gen_sync_trans):

    # 1)产生源和终止标识~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    source1, sinks1 = net1.get_start_ends()
    source2, sinks2 = net2.get_start_ends()
    source = Marking(source1.get_infor() + source2.get_infor())
    sinks = []
    for sink1 in sinks1:
        for sink2 in sinks2:
            sink = Marking(sink1.get_infor() + sink2.get_infor())
            sinks.append(sink)

    # 2)产生库所(不能重复)~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    places1, inner_places1, msg_places1 = net1.get_places()
    places2, inner_places2, msg_places2 = net2.get_places()
    places = list(set(places1 + places2))
    inner_places = list(set(inner_places1 + inner_places2))
    msg_places = list(set(msg_places1 + msg_places2))

    # 3)产生资源~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    res_places1, res_property1, req_res_map1, rel_res_map1 = net1.get_res_places(
    )
    res_places2, res_property2, req_res_map2, rel_res_map2 = net2.get_res_places(
    )
    res_places = list(set(res_places1 + res_places2))
    shared_res = set(res_places1).intersection(set(res_places2))
    res_property = {}
    for res, pro in res_property1.items():
        res_property[res] = pro
    # 跳过共享资源
    for res, pro in res_property2.items():
        if res in shared_res:
            continue
        res_property[res] = pro
    # 在产生变迁中构建
    req_res_map = {}
    rel_res_map = {}

    init_res = []
    init_res1 = net1.get_init_res()
    init_res2 = net2.get_init_res()
    for res in init_res1:
        init_res.append(res)
    # 跳过共享资源
    for res in init_res2:
        if res in shared_res:
            continue
        init_res.append(res)

    # 4)产生变迁~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    trans1, rout_trans1, tran_label_map1 = net1.get_trans()
    trans2, rout_trans2, tran_label_map2 = net2.get_trans()
    sync_trans1, sync_trans2 = get_sync_trans(net1, net2)
    trans = []
    tran_label_map = {}
    tran_delay_map = {}

    # a)net1和net2中非同步变迁
    for tran1 in trans1:
        if tran1 not in sync_trans1:
            trans.append(tran1)
            tran_label_map[tran1] = tran_label_map1[tran1]
            # ps:设置合并变迁时间间隔
            tran_delay_map[tran1] = net1.tran_delay_map[tran1]
            # net1中非同步变迁的请求/释放资源
            req_res_map[tran1] = req_res_map1[tran1]
            rel_res_map[tran1] = rel_res_map1[tran1]
    for tran2 in trans2:
        if tran2 not in sync_trans2:
            trans.append(tran2)
            tran_label_map[tran2] = tran_label_map2[tran2]
            # ps:设置合并变迁时间间隔
            tran_delay_map[tran2] = net2.tran_delay_map[tran2]
            # net2中非同步变迁的请求/释放资源
            req_res_map[tran2] = req_res_map2[tran2]
            rel_res_map[tran2] = rel_res_map2[tran2]

    # b)net1和net2中同步变迁(Note:用于生成同步合并变迁,其中一个变迁可以参加多个同步活动)
    syncMap1 = []
    syncMap2 = []

    print('sync_trans: ', sync_trans1, sync_trans2)

    for sync_tran1 in sync_trans1:

        # sync_trans存储net2中与sync_tran1同步(标号相同)的迁移集
        sync_trans_in_net2 = []

        for sync_tran2 in sync_trans2:
            if tran_label_map1[sync_tran1] == tran_label_map2[sync_tran2]:
                sync_trans_in_net2.append(sync_tran2)

        if sync_tran1 in gen_sync_trans:
            gen_sync_trans.remove(sync_tran1)

        for sync_tran in sync_trans_in_net2:

            if sync_tran in gen_sync_trans:
                gen_sync_trans.remove(sync_tran)

            # 同步变迁Id合并:a_b
            gen_sync_tran = sync_tran1 + '_' + sync_tran
            trans.append(gen_sync_tran)
            tran_label_map[gen_sync_tran] = tran_label_map1[sync_tran1]
            # ps:设置合并变迁时间间隔
            tran_delay_map[gen_sync_tran] = net1.tran_delay_map[sync_tran1]

            # Note:合并同步变迁中多个变迁的请求/释放资源~~~~~~~~~~~~~~~~~~~
            req_res_map[gen_sync_tran] = req_res_map1[
                sync_tran1] + req_res_map2[sync_tran]
            rel_res_map[gen_sync_tran] = rel_res_map1[
                sync_tran1] + rel_res_map2[sync_tran]

            gen_sync_trans.append(gen_sync_tran)

            syncMap1.append([sync_tran1, gen_sync_tran])
            syncMap2.append([sync_tran, gen_sync_tran])

    print('gen_sync_trans: ', gen_sync_trans)
    rout_trans = list(set(rout_trans1 + rout_trans2))

    # 5)产生流关系~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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


# 获取同步中合并迁移集
def get_merge_trans(tran, syncMap):
    merge_trans = []
    for item in syncMap:
        if item[0] == tran:
            merge_trans.append(item[1])
    return merge_trans


# 分别获取net1和net2中同步迁移集
def get_sync_trans(net1, net2):
    sync_trans1 = []
    sync_trans2 = []
    trans1, rout_trans1, label_map1 = net1.get_trans()
    trans2, rout_trans2, label_map2 = net2.get_trans()
    for tran1 in trans1:
        # 排除控制变迁
        if tran1 in rout_trans1:
            continue
        if is_sync_tran(tran1, net1, net2):
            sync_trans1.append(tran1)
    for tran2 in trans2:
        # 排除控制变迁
        if tran2 in rout_trans2:
            continue
        if is_sync_tran(tran2, net2, net1):
            sync_trans2.append(tran2)
    return sync_trans1, sync_trans2


# 判断tran1是不是同步变迁
def is_sync_tran(tran1, net1, net2):
    trans1, rout_trans1, tran_label_map1 = net1.get_trans()
    trans2, rout_trans2, tran_label_map2 = net2.get_trans()
    label1 = tran_label_map1[tran1]
    for tran2 in trans2:
        # 排除控制变迁
        if tran2 in rout_trans2:
            continue
        label2 = tran_label_map2[tran2]
        if label1 == label2:
            return True
    return False


# 1b.获得合并执行路径(异步)------------------------------------------
def get_merge_exec_path(nets):
    merge_ep = merge_exec_paths(nets)
    merge_ep.print_infor()
    return merge_ep


# 1.1b.异步合并执行路径---------------------------------------------
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


# 异步合并两条执行路径
def merge_two_exec_paths(ep1: OpenNet, ep2: OpenNet):

    # 1)产生源和终止标识~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    source1, sinks1 = ep1.get_start_ends()
    source = source1
    sinks = sinks1

    # 2)产生库所(不能重复)~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    places1, inner_places1, msg_places1 = ep1.get_places()
    places2, inner_places2, msg_places2 = ep2.get_places()
    places = list(set(places1 + places2))
    inner_places = list(set(inner_places1 + inner_places2))
    msg_places = list(set(msg_places1 + msg_places2))

    # 3)产生资源~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    res_places1, res_property1, req_res_map1, rel_res_map1 = ep1.get_res_places(
    )
    res_places2, res_property2, req_res_map2, rel_res_map2 = ep2.get_res_places(
    )
    res_places = list(set(res_places1 + res_places2))
    shared_res = set(res_places1).intersection(set(res_places2))
    res_property = {}
    for res, pro in res_property1.items():
        res_property[res] = pro
    # 跳过共享资源
    for res, pro in res_property2.items():
        if res in shared_res:
            continue
        res_property[res] = pro
    # 在产生变迁中构建
    req_res_map = {}
    rel_res_map = {}

    init_res = []
    init_res1 = ep1.get_init_res()
    init_res2 = ep2.get_init_res()
    for res in init_res1:
        init_res.append(res)
    # 跳过共享资源
    for res in init_res2:
        if res in shared_res:
            continue
        init_res.append(res)

    # 4)产生变迁~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    trans1, rout_trans1, tran_label_map1 = ep1.get_trans()
    trans2, rout_trans2, tran_label_map2 = ep2.get_trans()
    trans = []
    tran_label_map = {}
    tran_delay_map = {}

    # net1和net2中变迁
    for tran1 in trans1:
        trans.append(tran1)
        tran_label_map[tran1] = tran_label_map1[tran1]
        # ps:设置合并变迁时间间隔
        tran_delay_map[tran1] = ep1.tran_delay_map[tran1]
        # net1中非同步变迁的请求/释放资源
        req_res_map[tran1] = req_res_map1[tran1]
        rel_res_map[tran1] = rel_res_map1[tran1]
    for tran2 in trans2:
        if tran2 in trans1:  #ps:跳过重复变迁
            continue
        trans.append(tran2)
        tran_label_map[tran2] = tran_label_map2[tran2]
        # ps:设置合并变迁时间间隔
        tran_delay_map[tran2] = ep2.tran_delay_map[tran2]
        # net2中非同步变迁的请求/释放资源
        req_res_map[tran2] = req_res_map2[tran2]
        rel_res_map[tran2] = rel_res_map2[tran2]

    rout_trans = list(set(rout_trans1 + rout_trans2))

    # 5)产生流关系~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    flows1 = ep1.get_flows()
    flows2 = ep2.get_flows()
    flows = flows1 + flows2

    merge_ep = OpenNet(source, sinks, places, trans, tran_label_map, [])
    merge_ep.inner_places = inner_places
    merge_ep.msg_places = msg_places
    merge_ep.rout_trans = rout_trans
    # ps:不重复添加添加flows
    merge_ep.add_flows(flows)
    merge_ep.init_res = init_res
    merge_ep.res_places = res_places
    merge_ep.res_property = res_property
    merge_ep.req_res_map = req_res_map
    merge_ep.rel_res_map = rel_res_map
    merge_ep.tran_delay_map = tran_delay_map
    return merge_ep


# 2.移除组合网中某些变迁-------------------------------------------------------
def rov_some_trans(comp_net: nt.OpenNet, rov_trans):

    comp_net_copy = copy.deepcopy(comp_net)

    # a)确定变迁
    bag = list(set(comp_net_copy.trans) - set(rov_trans))
    bag_rout_trans = list(set(bag).intersection(set(comp_net_copy.rout_trans)))
    # Note:确定bag中变迁时间间隔
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
        # 请求和释放资源以name标识
        bag_req_res_map[tran] = comp_net_copy.req_res_map[tran]
        bag_rel_res_map[tran] = comp_net_copy.rel_res_map[tran]

    # b)确定流和库所(排除资源库所)
    bag_places = set()
    bag_inner_places = set()
    bag_msg_places = set()
    bag_flows = []
    flows = comp_net_copy.get_flows()
    for flow in flows:
        fl_from, fl_to = flow.get_infor()
        if fl_from in bag:  #fl_from为变迁
            bag_places.add(fl_to)
            if fl_to in comp_net_copy.inner_places:
                bag_inner_places.add(fl_to)
            if fl_to in comp_net_copy.msg_places:
                bag_msg_places.add(fl_to)
            bag_flows.append(flow)
        elif fl_to in bag:  #fl_to为变迁
            bag_places.add(fl_from)
            if fl_from in comp_net_copy.inner_places:
                bag_inner_places.add(fl_from)
            if fl_from in comp_net_copy.msg_places:
                bag_msg_places.add(fl_from)
            bag_flows.append(flow)

    # c)确定资源
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

    # 构建由包生成的网
    bag_net = nt.OpenNet(comp_net_copy.source, comp_net_copy.sinks,
                         list(bag_places), bag, bag_label_map, bag_flows)

    bag_net.inner_places = list(bag_inner_places)
    bag_net.msg_places = list(bag_msg_places)

    bag_net.rout_trans = bag_rout_trans

    # 资源库所设置
    bag_net.init_res = bag_init_res
    bag_net.res_places = list(bag_res_places)
    bag_net.res_property = bag_res_property
    print(bag_res_property)
    bag_net.req_res_map = bag_req_res_map
    bag_net.rel_res_map = bag_rel_res_map

    # Note:设置时间
    bag_net.tran_delay_map = bag_tran_delay_map

    return bag_net


# 3.由执行路径组合中变迁集确定在组合网中投影(同步交互确定)-----------------------------------
def net_proj(path):

    nets = ng.gen_nets(path)
    comp_net = get_compose_net(nets)

    # ------------------首先将网comp_net改造为一个工作流网------------------#
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

    proj_nets = []  # 返回投影网集

    for trans in trans_in_exec_path_comp:

        # 1.确定映射在组合网中的变迁集~~~~~~~~~~~~~~~~~~~~~~~~~~~
        trans_in_comp_net = []
        for tran in comp_net.trans:
            # a)异步变迁
            if tran.find('_') == -1:
                if tran in trans:
                    trans_in_comp_net.append(tran)
            else:  # b)同步变迁
                sync_trans = tran.split('_')
                if set(sync_trans) <= set(trans):
                    trans_in_comp_net.append(tran)

        # 2.确定trans_in_comp_net映射的网~~~~~~~~~~~~~~~~~~~~
        bag = trans_in_comp_net + ['ti', 'to']  # 添加ti和to
        # a)确定变迁
        bag_rout_trans = list(set(bag).intersection(set(rout_trans)))
        # Note:确定bag中变迁时间间隔
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
            # 请求和释放资源以name标识
            bag_req_res_map[tran] = comp_net.req_res_map[tran]
            bag_rel_res_map[tran] = comp_net.rel_res_map[tran]

        # b)确定流和库所(排除资源库所)
        bag_places = set()
        bag_inner_places = set()
        bag_msg_places = set()
        bag_flows = []
        flows = comp_net.get_flows()
        for flow in flows:
            fl_from, fl_to = flow.get_infor()
            if fl_from in bag:  #fl_from为变迁
                bag_places.add(fl_to)
                if fl_to in comp_net.inner_places:
                    bag_inner_places.add(fl_to)
                if fl_to in comp_net.msg_places:
                    bag_msg_places.add(fl_to)
                bag_flows.append(flow)
            elif fl_to in bag:  #fl_to为变迁
                bag_places.add(fl_from)
                if fl_from in comp_net.inner_places:
                    bag_inner_places.add(fl_from)
                if fl_from in comp_net.msg_places:
                    bag_msg_places.add(fl_from)
                bag_flows.append(flow)

        # c)确定资源
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

        # d)确定source和sink
        bag_source = nt.Marking(['i'])
        bag_sinks = [nt.Marking(['o'])]

        # 构建由包生成的网
        bag_net = OpenNet(bag_source, bag_sinks, list(bag_places), bag,
                          bag_label_map, bag_flows)

        bag_net.inner_places = list(bag_inner_places)
        bag_net.msg_places = list(bag_msg_places)

        bag_net.rout_trans = bag_rout_trans

        # 资源库所设置
        bag_net.init_res = bag_init_res
        bag_net.res_places = list(bag_res_places)
        bag_net.res_property = bag_res_property
        print(bag_res_property)
        bag_net.req_res_map = bag_req_res_map
        bag_net.rel_res_map = bag_rel_res_map

        # Note:设置时间
        bag_net.tran_delay_map = bag_tran_delay_map

        print('proj net========================================')
        bag_net.print_infor()

        proj_nets.append(bag_net)

    return proj_nets, comp_net


# 计算执行路径组合中变迁集
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
    # 存储多条执行路径组合中的变迁集
    trans_in_exec_path_comp = []
    for elem in prod:
        # Note:index是字符串
        indexs = elem.split(' ')
        trans = []
        for i in range(len(indexs)):
            exec_path = exec_paths_set[i][int(indexs[i])]
            trans = trans + exec_path.trans
        trans_in_exec_path_comp.append(trans)
    return trans_in_exec_path_comp


# 计算多个集合的笛卡尔积
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


# 4.判断实例网是否合法,即若p的前集或后集为空,则p是源库所或汇库所------------------
#   Note:假定CERP是正确的才可以这样判断
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


# 5.获取应急响应中每个组织的内网-------------------------------------------
def get_inner_nets(nets):
    inner_nets = []
    compose_net = get_compose_net(nets)
    # 1.同步变迁集
    sync_inter_trans = get_sync_inter_trans(compose_net)
    for net in nets:
        inner_net = iu.get_inner_net(net)
        # 2.异步变迁集
        asyn_inter_trans = net.get_asyn_inter_trans()
        inner_net.add_inter_trans(asyn_inter_trans)
        trans = net.trans
        inner_net.add_inter_trans(
            list(set(sync_inter_trans).intersection(set(trans))))
        inner_nets.append(inner_net)
    return inner_nets


# 获取组合网中的同步变迁集
def get_sync_inter_trans(net: nt.OpenNet):
    syn_inter_trans = []
    trans = net.trans
    for tran in trans:
        if tran.find('_') != -1:
            merge_trans = tran.split("_")
            syn_inter_trans += merge_trans
    # 避免重复的同步变迁(ps:一个变迁可以参与多个同步交互)
    return list(set(syn_inter_trans))


# 6.计算网中变迁对应的因果集-------------------------------------------
def gen_casual_set(trans, flows, back_trans):
    casual_tran_map = {}
    for tran in trans:
        # 运行队列和已访问队列
        visiting_queue = [tran]
        # Note:因果集不包含自己~~~~~~~~~~~~~~~~~
        visited_queue = []
        # 迭代计算
        while visiting_queue:
            from_tran = visiting_queue.pop(0)
            from_places = nt.get_preset(flows, from_tran)
            casual_trans = []
            for from_place in from_places:
                casual_trans = list(
                    set(casual_trans + nt.get_preset(flows, from_place)))
            # Note:排除back_trans!!!
            casual_trans = list(set(casual_trans) - set(back_trans))
            # 计算tran的因果迁移集(避免前后集重复)
            for casual_tran in casual_trans:
                if casual_tran not in visited_queue:
                    visiting_queue.append(casual_tran)
                    visited_queue.append(casual_tran)
        # print('visited_queue:', tran, visited_queue)
        casual_tran_map[tran] = visited_queue
        # print(bags)
    return casual_tran_map


# 7.计算CERP中所有Back变迁-------------------------------------------
def back_trans_in_CERP(path):
    nets = ng.gen_nets(path)
    inner_nets = get_inner_nets(nets)
    back_trans = []
    for inner_net in inner_nets:
        to_graph = inner_net.to_graph()
        # Note:获取当前网中所有循环中的back变迁集
        source = inner_net.source
        dfs_obj = cu.DFS()
        back_trans = back_trans + dfs_obj.get_back_trans(source, to_graph)
    return back_trans


# 8.计算CERP中所有and split/join变迁-------------------------------------------
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


# 9.批量添加变迁的Delay(ps:同步变迁Delay一致)-------------------------------------------
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
    # 文档根元素
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
        # 缩进 - 换行 - 编码
        domTree.writexml(f, addindent='  ', encoding='ISO-8859-1')


# 最大化产生的同步变迁集
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


# 将组合网中所有变迁依据同步"_"进行分解
def get_sync_trans_set(comp_net: nt.OpenNet):
    sync_trans_set = []
    for tran in comp_net.trans:
        if tran.find('_') != -1:
            merge_trans = tran.split("_")
            sync_trans_set.append(merge_trans)
        else:
            sync_trans_set.append([tran])
    return sync_trans_set


# 产生变迁时间间隔(ps:可以相等)
def gen_delay():
    # min_delay = random.randint(0, 9)
    min_delay = random.randint(3, 6)
    max_delay = -1
    while max_delay < min_delay:
        # max_delay = random.randint(0, 9)
        max_delay = random.randint(3, 6)
    return min_delay, max_delay


# 获取变迁tran的index
def get_index(tran, max_set):
    for index, trans in enumerate(max_set):
        if tran in trans:
            return index
    return -1


# -------------------------------测试---------------------------------#

if __name__ == '__main__':

    # proj_nets, comp_net = net_proj('/Users/moqi/Desktop/临时文件/2023.xml')

    # for index, proj_net in enumerate(proj_nets):
    #     proj_net.net_to_dot(str(index), True)

    # nets = ng.gen_nets('/Users/moqi/Desktop/临时文件/2023.xml')
    # nets = ng.gen_nets('/Users/moqi/Desktop/临时文件/原始模型/Ca-2.xml')
    # comp_net = get_compose_net(nets)
    # # comp_net.net_to_dot('abc', True)
    # print('partner, places, trans:', len(nets), len(comp_net.places),
    #       len(comp_net.trans))

    # max_set = max_sync_trans_set([['a', 'b', 'c'], ['a', 'd'], ['e', 'f'],
    #                               ['g', 'h'], ['k']])
    # print(max_set)

    add_tran_delay('/Users/moqi/Desktop/原始模型/原始数据/Ca-22.xml')

    # proj_nets, comp_net = net_proj(
    #     '/Users/moqi/Desktop/原始模型/归档/原始模型/Ca-22.xml')
    # comp_net.net_to_dot('22', True)

# -------------------------------------------------------------------#
