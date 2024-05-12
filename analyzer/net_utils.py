#coding=gbk

from collections import Counter
import copy
from erp_utils import get_compose_net
from lts import LTS, Tran
import net as nt
from net_gen import gen_nets


# 1.1产生可达图(未考虑资源和数据)-------------------------------------------------
def gen_rg(net: nt.OpenNet):

    source, sinks = net.get_start_ends()

    gen_trans = []  # 产生的变迁集

    # 运行队列和已访问队列
    visiting_queue = [source]
    visited_queue = [source]

    # 迭代计算
    while visiting_queue:
        marking = visiting_queue.pop(0)
        enable_trans = nt.get_enable_trans(net, marking)
        for enable_tran in enable_trans:
            # 1)产生后继标识
            preset = nt.get_preset(net.get_flows(), enable_tran)
            postset = nt.get_postset(net.get_flows(), enable_tran)
            succ_makring = nt.succ_makring(marking.get_infor(), preset,
                                           postset)
            # 2)产生后继变迁(Note:迁移动作以标号进行标识)
            # tran = Tran(marking, label_map[enable_tran], succ_makring)
            # 迁移动作以变迁进行标识
            tran = Tran(marking, enable_tran, succ_makring)
            gen_trans.append(tran)
            # 添加未访问的状态
            if not nt.marking_is_exist(succ_makring, visited_queue):
                visiting_queue.append(succ_makring)
                visited_queue.append(succ_makring)

    return LTS(source, sinks, visited_queue, gen_trans)


# 1.2产生可达图(考虑资源约束)----------------------------------------------------
def gen_rg_with_res(net):

    source, sinks = net.get_start_ends()
    trans, rout_trans, label_map = net.get_trans()

    gen_trans = []  # 产生的变迁集

    # 运行队列和已访问队列
    print('net.init_res', net.init_res)
    visiting_queue = [[source, net.init_res]]
    visited_queue = [source]

    # 迭代计算
    while visiting_queue:
        [marking, res] = visiting_queue.pop(0)
        enable_trans = nt.get_enable_trans(net, marking)
        for enable_tran in enable_trans:
            # Note:避免分支中提前将资源消耗掉(每个分支获得资源相同)~~~~~~~~~~~~~~~~~~
            res_copy = copy.deepcopy(res)
            req_res = net.req_res_map[enable_tran]
            # 若当前资源不充足,则跳过当前使能变迁
            if not res_is_suff(res_copy, req_res):
                continue
            # 1)产生后继标识
            preset = nt.get_preset(net.get_flows(), enable_tran)
            postset = nt.get_postset(net.get_flows(), enable_tran)
            succ_makring = nt.succ_makring(marking.get_infor(), preset,
                                           postset)
            # 2)产生后继变迁(Note:迁移动作以标号进行标识)
            tran = Tran(marking, label_map[enable_tran], succ_makring)
            gen_trans.append(tran)
            # 添加未访问的状态
            if not nt.marking_is_exist(succ_makring, visited_queue):
                # print(
                #     'succ_res:', succ_makring.get_infor(),
                #     succ_res(res_copy, net.req_res_map[enable_tran],
                #              net.rel_res_map[enable_tran]))
                visiting_queue.append([
                    succ_makring,
                    succ_res(res_copy, net.req_res_map[enable_tran],
                             net.rel_res_map[enable_tran])
                ])
                visited_queue.append(succ_makring)

    return LTS(source, sinks, visited_queue, gen_trans)


# 判断当前资源是否充足
def res_is_suff(res, req_res):
    cou = Counter(res)
    cou.subtract(Counter(req_res))
    vals = cou.values()
    for val in vals:
        if val < 0:
            return False
    return True


# 获取变迁迁移后的资源集合
def succ_res(res, req_res, rel_res):
    # 移除前集
    for rr in req_res:
        if rr in res:
            res.remove(rr)
    succ_res = res + rel_res
    return succ_res


# 2.利用稳固集产生可达图(未考虑资源和数据)----------------------------------------------
def gen_rg_with_subset(net: nt.OpenNet):

    source, sinks = net.get_start_ends()
    label_map = net.label_map
    gen_trans = []  # 产生的变迁集

    # 运行队列和已访问队列
    visiting_queue = [source]
    visited_queue = [source]

    # 迭代计算
    while visiting_queue:
        marking = visiting_queue.pop(0)
        # print(marking.get_infor())
        # Note:只迁移稳固集中使能活动(未考虑消除忽视问题)
        enable_trans = nt.get_enable_trans(net, marking)
        S = get_stubset(net, marking)
        enable_trans = list(set(enable_trans).intersection(set(S)))
        for enable_tran in enable_trans:
            # 1)产生后继标识
            preset = nt.get_preset(net.get_flows(), enable_tran)
            postset = nt.get_postset(net.get_flows(), enable_tran)
            succ_makring = nt.succ_makring(marking.get_infor(), preset,
                                           postset)
            # 2)产生后继变迁(Note:迁移动作以标号进行标识)
            tran = Tran(marking, label_map[enable_tran], succ_makring)
            gen_trans.append(tran)
            # 添加未访问的状态
            if not nt.marking_is_exist(succ_makring, visited_queue):
                visiting_queue.append(succ_makring)
                visited_queue.append(succ_makring)

    return LTS(source, sinks, visited_queue, gen_trans)


# 计算特定标识的稳固集(Note:未考虑忽视)
def get_stubset(net, marking):
    S = []  # 返回稳固集
    U = []  # 未处理迁移集
    enable_trans = nt.get_enable_trans(net, marking)
    # print(marking.get_infor(), enable_trans)
    if not enable_trans:  # 没有使能迁移,直接返回空稳固集S
        return S
    else:  # 有使能迁移,随机选择一个使能迁移
        first_act = enable_trans[0]
        # print('first_act', first_act)
        S.append(first_act)
        U.append(first_act)
        while U:
            act = U.pop(0)
            if act in enable_trans:
                N = get_disenabling_trans(net, act)
            else:
                N = get_enabling_trans(net, act, marking)
            # 避免重复添加
            subset = set(N) - set(S)
            U = list(set(U).union(subset))
            # 添加稳固集到S
            S = list(set(S).union(N))
        return S


# 获取导致变迁使能的变迁集(以Id标识)
def get_enabling_trans(net, tran, marking):
    enabling_trans = set()
    places = marking.get_infor()
    preset = nt.get_preset(net.get_flows(), tran)
    for place in preset:
        # 跳过已经含有托肯的库所
        if place in places:
            continue
        # 不重复
        enabling_trans = enabling_trans.union(
            set(nt.get_preset(net.get_flows(), place)))
    return list(enabling_trans)


# 获取变迁的冲突变迁集(以Id标识)
def get_disenabling_trans(net, tran):
    disenabling_trans = []
    trans, ctrl_trans, label_map = net.get_trans()
    preset = nt.get_preset(net.get_flows(), tran)
    for temp_tran in trans:
        # 不包括自己
        if temp_tran == tran:
            continue
        temp_preset = nt.get_preset(net.get_flows(), temp_tran)
        # 前集相交(冲突)
        if set(preset).intersection(set(temp_preset)):
            disenabling_trans.append(temp_tran)
    return disenabling_trans


# 3.获取markings的终止标识集----------------------------------------------
def get_sink_markings(markings, sinks):
    ends = []
    for marking in markings:
        if nt.marking_is_exist(marking, sinks):
            ends.append(marking)
    return ends


# -------------------------------测试---------------------------------#

if __name__ == '__main__':

    # net = get_compose_net('/Users/moqi/Desktop/Petri net 1 2.xml')
    # lts = gen_rg_with_subset(net)
    # start, ends, states, trans = lts.get_infor()
    # for state in ends:
    #     print(state.get_infor())
    # # print(start, ends, states)
    # for tran in trans:
    #     state_from, label, state_to = tran.get_infor()
    #     print(state_from.get_infor(), label, state_to.get_infor())

    nets = gen_nets('/Users/moqi/Desktop/临时文件/Ca-7.xml')
    comp_net = get_compose_net(nets)
    rg = gen_rg_with_res(comp_net)
    print(len(rg.states))
    # print('PR:', len(nets), 'PA:', len(comp_net.places), 'TR:',
    #       len(comp_net.trans))
    # rg = gen_rg_with_res(comp_net)
    # # rg = gen_rg(comp_net)
    # rg.rg_to_dot()
    # frags = decompose_net(comp_net)
    # for index, frag in enumerate(frags):
    #     frag.net_to_dot(str(index))

# -------------------------------------------------------------------#
