#coding=gbk

from collections import Counter
import copy
from erp_utils import get_compose_net
from lts import LTS, Tran
import net as nt
from net_gen import gen_nets


# 1.1�����ɴ�ͼ(δ������Դ������)-------------------------------------------------
def gen_rg(net: nt.OpenNet):

    source, sinks = net.get_start_ends()

    gen_trans = []  # �����ı�Ǩ��

    # ���ж��к��ѷ��ʶ���
    visiting_queue = [source]
    visited_queue = [source]

    # ��������
    while visiting_queue:
        marking = visiting_queue.pop(0)
        enable_trans = nt.get_enable_trans(net, marking)
        for enable_tran in enable_trans:
            # 1)������̱�ʶ
            preset = nt.get_preset(net.get_flows(), enable_tran)
            postset = nt.get_postset(net.get_flows(), enable_tran)
            succ_makring = nt.succ_makring(marking.get_infor(), preset,
                                           postset)
            # 2)������̱�Ǩ(Note:Ǩ�ƶ����Ա�Ž��б�ʶ)
            # tran = Tran(marking, label_map[enable_tran], succ_makring)
            # Ǩ�ƶ����Ա�Ǩ���б�ʶ
            tran = Tran(marking, enable_tran, succ_makring)
            gen_trans.append(tran)
            # ���δ���ʵ�״̬
            if not nt.marking_is_exist(succ_makring, visited_queue):
                visiting_queue.append(succ_makring)
                visited_queue.append(succ_makring)

    return LTS(source, sinks, visited_queue, gen_trans)


# 1.2�����ɴ�ͼ(������ԴԼ��)----------------------------------------------------
def gen_rg_with_res(net):

    source, sinks = net.get_start_ends()
    trans, rout_trans, label_map = net.get_trans()

    gen_trans = []  # �����ı�Ǩ��

    # ���ж��к��ѷ��ʶ���
    print('net.init_res', net.init_res)
    visiting_queue = [[source, net.init_res]]
    visited_queue = [source]

    # ��������
    while visiting_queue:
        [marking, res] = visiting_queue.pop(0)
        enable_trans = nt.get_enable_trans(net, marking)
        for enable_tran in enable_trans:
            # Note:�����֧����ǰ����Դ���ĵ�(ÿ����֧�����Դ��ͬ)~~~~~~~~~~~~~~~~~~
            res_copy = copy.deepcopy(res)
            req_res = net.req_res_map[enable_tran]
            # ����ǰ��Դ������,��������ǰʹ�ܱ�Ǩ
            if not res_is_suff(res_copy, req_res):
                continue
            # 1)������̱�ʶ
            preset = nt.get_preset(net.get_flows(), enable_tran)
            postset = nt.get_postset(net.get_flows(), enable_tran)
            succ_makring = nt.succ_makring(marking.get_infor(), preset,
                                           postset)
            # 2)������̱�Ǩ(Note:Ǩ�ƶ����Ա�Ž��б�ʶ)
            tran = Tran(marking, label_map[enable_tran], succ_makring)
            gen_trans.append(tran)
            # ���δ���ʵ�״̬
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


# �жϵ�ǰ��Դ�Ƿ����
def res_is_suff(res, req_res):
    cou = Counter(res)
    cou.subtract(Counter(req_res))
    vals = cou.values()
    for val in vals:
        if val < 0:
            return False
    return True


# ��ȡ��ǨǨ�ƺ����Դ����
def succ_res(res, req_res, rel_res):
    # �Ƴ�ǰ��
    for rr in req_res:
        if rr in res:
            res.remove(rr)
    succ_res = res + rel_res
    return succ_res


# 2.�����ȹ̼������ɴ�ͼ(δ������Դ������)----------------------------------------------
def gen_rg_with_subset(net: nt.OpenNet):

    source, sinks = net.get_start_ends()
    label_map = net.label_map
    gen_trans = []  # �����ı�Ǩ��

    # ���ж��к��ѷ��ʶ���
    visiting_queue = [source]
    visited_queue = [source]

    # ��������
    while visiting_queue:
        marking = visiting_queue.pop(0)
        # print(marking.get_infor())
        # Note:ֻǨ���ȹ̼���ʹ�ܻ(δ����������������)
        enable_trans = nt.get_enable_trans(net, marking)
        S = get_stubset(net, marking)
        enable_trans = list(set(enable_trans).intersection(set(S)))
        for enable_tran in enable_trans:
            # 1)������̱�ʶ
            preset = nt.get_preset(net.get_flows(), enable_tran)
            postset = nt.get_postset(net.get_flows(), enable_tran)
            succ_makring = nt.succ_makring(marking.get_infor(), preset,
                                           postset)
            # 2)������̱�Ǩ(Note:Ǩ�ƶ����Ա�Ž��б�ʶ)
            tran = Tran(marking, label_map[enable_tran], succ_makring)
            gen_trans.append(tran)
            # ���δ���ʵ�״̬
            if not nt.marking_is_exist(succ_makring, visited_queue):
                visiting_queue.append(succ_makring)
                visited_queue.append(succ_makring)

    return LTS(source, sinks, visited_queue, gen_trans)


# �����ض���ʶ���ȹ̼�(Note:δ���Ǻ���)
def get_stubset(net, marking):
    S = []  # �����ȹ̼�
    U = []  # δ����Ǩ�Ƽ�
    enable_trans = nt.get_enable_trans(net, marking)
    # print(marking.get_infor(), enable_trans)
    if not enable_trans:  # û��ʹ��Ǩ��,ֱ�ӷ��ؿ��ȹ̼�S
        return S
    else:  # ��ʹ��Ǩ��,���ѡ��һ��ʹ��Ǩ��
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
            # �����ظ����
            subset = set(N) - set(S)
            U = list(set(U).union(subset))
            # ����ȹ̼���S
            S = list(set(S).union(N))
        return S


# ��ȡ���±�Ǩʹ�ܵı�Ǩ��(��Id��ʶ)
def get_enabling_trans(net, tran, marking):
    enabling_trans = set()
    places = marking.get_infor()
    preset = nt.get_preset(net.get_flows(), tran)
    for place in preset:
        # �����Ѿ������пϵĿ���
        if place in places:
            continue
        # ���ظ�
        enabling_trans = enabling_trans.union(
            set(nt.get_preset(net.get_flows(), place)))
    return list(enabling_trans)


# ��ȡ��Ǩ�ĳ�ͻ��Ǩ��(��Id��ʶ)
def get_disenabling_trans(net, tran):
    disenabling_trans = []
    trans, ctrl_trans, label_map = net.get_trans()
    preset = nt.get_preset(net.get_flows(), tran)
    for temp_tran in trans:
        # �������Լ�
        if temp_tran == tran:
            continue
        temp_preset = nt.get_preset(net.get_flows(), temp_tran)
        # ǰ���ཻ(��ͻ)
        if set(preset).intersection(set(temp_preset)):
            disenabling_trans.append(temp_tran)
    return disenabling_trans


# 3.��ȡmarkings����ֹ��ʶ��----------------------------------------------
def get_sink_markings(markings, sinks):
    ends = []
    for marking in markings:
        if nt.marking_is_exist(marking, sinks):
            ends.append(marking)
    return ends


# -------------------------------����---------------------------------#

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

    nets = gen_nets('/Users/moqi/Desktop/��ʱ�ļ�/Ca-7.xml')
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
