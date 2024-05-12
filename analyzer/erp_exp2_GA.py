# coding=gbk
import os
import pickle
import time
import net as nt
import erp_utils as erpu
import circle_utils as cu
import copy
import geatpy as ea
import numpy as np
import sympy as sp
import net_gen as ng
import random
import erp_zeng as zeng
import csv
import math
from scipy import integrate


# Expr1.产生无冲突的CERP-----------------------------------------------
def gen_resolved_CERP(path):

    exec_paths = gen_exec_paths(path)

    cond_exec_paths = []  #候选执行路径
    conflict_exec_paths = []  #存在资源冲突的执行路径
    for exec_path in exec_paths:
        result = res_suff_check(exec_path)
        if result == 'Under-resourced':
            continue
        elif result == 'Resourced':
            cond_exec_paths.append(exec_path)
        else:
            conflict_exec_paths.append(exec_path)

    for exec_path in conflict_exec_paths:
        resolved_exec_path = gen_resolved_exec_path_NSGAII(exec_path)
        cond_exec_paths.append(resolved_exec_path)

    renamed_exec_paths = []
    for exec_path in cond_exec_paths:
        renamed_exec_paths.append(rename_exec_path(exec_path))

    inter_CERP = erpu.merge_exec_paths(renamed_exec_paths)

    idf_places = []
    for index in range(len(renamed_exec_paths)):
        idf_place = 'ep{}'.format(index)
        idf_places.append(idf_place)
    # 设置中间过程的idf库所
    inter_CERP.idf_places = idf_places
    # 将idf库所加入到中间过程的初始Marking中
    source_places = inter_CERP.source.get_infor()
    source_places = source_places + idf_places
    inter_CERP.source = nt.Marking(source_places)

    # 获取分支库所-变迁对集
    branch_pairs = get_branch_pairs(inter_CERP)
    for [place, tran] in branch_pairs:

        inter_CERP.rov_flow(place, tran)

        ct = 'C{}'.format(tran)
        inter_CERP.add_trans([ct])
        inter_CERP.label_map[ct] = ct
        inter_CERP.tran_delay_map[ct] = [0, 0]

        pt = 'P{}'.format(tran)
        inter_CERP.add_places([pt])
        inter_CERP.add_inner_places([pt])

        inter_CERP.add_flow(place, ct)
        inter_CERP.add_flow(ct, pt)
        inter_CERP.add_flow(pt, tran)

        asso_idfs, unasso_idfs = get_bt_idfs(tran, renamed_exec_paths)
        for idf in asso_idfs:
            inter_CERP.follow_arcs.append(['ep{}'.format(idf), ct])
        for idf in unasso_idfs:
            inter_CERP.delete_arcs.append(['ep{}'.format(idf), ct])

    return inter_CERP


# 利用时间延时重命名执行路径中变迁集
def rename_exec_path(exec_path: nt.OpenNet):
    exec_path_copy = copy.deepcopy(exec_path)
    trans = exec_path.trans
    renamed_trans = []
    for tran in trans:
        [a, b] = exec_path.tran_delay_map[tran]
        renamed_tran = tran + '.{}{}'.format(int(a), int(b))
        renamed_trans.append(renamed_tran)
    exec_path_copy.rename_trans(trans, renamed_trans)
    # exec_path_copy.print_infor()
    # exec_path_copy.net_to_dot('renamed_exec_path', True)
    return exec_path_copy


# 获取分支库所-变迁对集
def get_branch_pairs(CERP: nt.OpenNet):
    pairs = []
    flows = CERP.flows
    for place in CERP.inner_places:
        postset = nt.get_postset(flows, place)
        # ps:含时间的CERP中无循环结构
        if len(postset) > 1:
            for tran in postset:
                pairs.append([place, tran])
    return pairs


# 获取分支变迁关联和未关联的标识
def get_bt_idfs(branch_tran, renamed_exec_paths):
    asso_idfs = []
    unasso_idfs = []
    for index, renamed_exec_path in enumerate(renamed_exec_paths):
        if branch_tran in renamed_exec_path.trans:
            asso_idfs.append(index)
        else:
            unasso_idfs.append(index)
    return asso_idfs, unasso_idfs


# Expr2.比较执行路径-----------------------------------------------
def optimize_res_conf_exec_path(path):

    base_name, file_extension = os.path.splitext(path)
    case = base_name.split('/')[-1]

    exec_paths = gen_exec_paths(path)
    for number, exec_path in enumerate(exec_paths):

        result = res_suff_check(exec_path)
        print('exec_path{}'.format(number), result)

        if result == 'Partially resourced':
            gen_resolved_exec_path_NSGAII(exec_path)
            # start_time = time.time()  #开始时间
            # resolved_exec_path = gen_resolved_exec_path_NSGAII(exec_path)
            # end_time = time.time()  #结束时间
            # total_time = (end_time - start_time) * 1000.0
            # resolved_exec_path.net_to_dot('solu', True)
            # fire_time_map, exec_time = calc_fire_time(resolved_exec_path)
            # print('EPA res conf: ', len(get_res_confs(resolved_exec_path)))
            # print('EPA exec time: ', exec_time)
            # print('EPA waiting delay: ', get_waiting_delay(resolved_exec_path))
            # print('EPA Time: ', total_time)
            # print('\n................................................')

            # 序列化解决执行路径
            # path = '/Users/moqi/Desktop/原始模型/实验结果/EPA-{}.pkl'.format(case)
            # with open(path, 'wb') as f:
            #     pickle.dump(resolved_exec_path, f)

            # # 1.1创建文件对象
            # print('fire_time_map:', fire_time_map)
            # csv_name = '/Users/moqi/Desktop/原始模型/实验结果/csv结果/EPA-{}.csv'.format(
            #     case)
            # with open(csv_name, 'w') as f:
            #     # 1.2基于文件对象构建csv写入对象
            #     writer = csv.writer(f)
            #     # 1.3构建列表头
            #     writer.writerow(['Tran', 'Min Firing Time', 'Max Firing Time'])
            #     # 1.4填入内容
            #     for key, value in fire_time_map.items():
            #         if key.startswith('Td') or key in ['ti', 'to']:  # 跳过延时变迁
            #             continue
            #         row = []
            #         row.append(key)
            #         row.append(value[0])
            #         row.append(value[1])
            #         writer.writerow(row)


# 1.产生执行路径-----------------------------------------------
def gen_exec_paths(path):
    exec_paths = []
    proj_nets, comp_net = erpu.net_proj(path)
    # comp_net.net_to_dot('exec_path', True)
    for proj_net in proj_nets:
        # 投影网要是合法的
        print('legal:', proj_net_is_legal(proj_net))
        if proj_net_is_legal(proj_net):
            exec_paths.append(proj_net)
    return exec_paths


def proj_net_is_legal(proj_net: nt.OpenNet):
    # Note:每条执行路径被改造为工作流网
    start_end_places = ['i', 'o']
    flows = proj_net.flows
    # 1)若place的前集或后集为空,则p是源库所或汇库所
    for place in proj_net.places:
        if len(nt.get_preset(flows, place)) == 0 or len(
                nt.get_postset(flows, place)) == 0:
            if place not in start_end_places:
                print('前集或后集为空', place)
                return False
    # 2)投影网中无环结构
    dfs_obj = cu.DFS()
    to_graph = proj_net.to_graph()
    print(to_graph)
    dfs_obj.dfs('i', to_graph)
    circles = dfs_obj.circles
    if circles:
        print('有环........')
        return False
    return True


# 2.计算执行路径的变迁点火时间------------------------------------
def calc_fire_time(exec_path: nt.OpenNet):
    fire_time_map = {}
    trans = exec_path.trans
    flows = exec_path.flows
    # 设置初始变迁'ti'点火时间为[0,0]
    fire_time_map['ti'] = [0, 0]
    visited_trans = ['ti']
    # 迭代地计算变迁关联点火时间
    while len(trans) != len(visited_trans):
        rest_trans = list(set(trans) - set(visited_trans))
        one_tran = get_one_deter_tran(rest_trans, flows, fire_time_map)
        # print('one_tran', one_tran)
        # 计算tran的点火时间
        preset_trans_one = get_preset_trans(flows, one_tran)
        # print(preset_trans_one)
        low_times = []
        upper_times = []
        for tran in preset_trans_one:
            [a, b] = fire_time_map[tran]
            low_times.append(a)
            upper_times.append(b)
        # 需加上自己的firing delay
        [dl, du] = exec_path.tran_delay_map[one_tran]
        fire_time_map[one_tran] = [max(low_times) + dl, max(upper_times) + du]
        visited_trans.append(one_tran)
    # 返回每条变迁点火时间和执行路径的完成时间
    return fire_time_map, fire_time_map['to']


# 获取一个能够计算点火时间的变迁
def get_one_deter_tran(rest_trans, flows, fire_time_map):
    for tran in rest_trans:
        if tran_is_deter(tran, flows, fire_time_map):
            return tran
    return None


# 确定变迁能否计算点火时间
def tran_is_deter(tran, flows, fire_time_map):
    preset_trans = get_preset_trans(flows, tran)
    if set(preset_trans).issubset(set(fire_time_map.keys())):
        return True
    return False


# 获取tran前集的前集(变迁集)
def get_preset_trans(flows, tran):
    preset_trans = set()
    preset_places = nt.get_preset(flows, tran)
    for place in preset_places:
        trans = nt.get_preset(flows, place)
        preset_trans = preset_trans | set(trans)
    return list(preset_trans)


# 3.检测执行路径的资源充分性------------------------------------
def res_suff_check(exec_path: nt.OpenNet):
    res_places = exec_path.res_places
    res_map = get_res_map(exec_path)
    for res in res_places:
        res_property = exec_path.res_property[res]
        if res_property == 1:  #消化性资源
            if res not in exec_path.init_res or len(res_map[res][0]) > 1:
                print('Under-resourced res:', res)
                return 'Under-resourced'
        else:  #重复性资源
            if res not in exec_path.init_res:
                print('Under-resourced res:', res)
                return 'Under-resourced'
    res_confs = get_res_confs(exec_path)
    if len(res_confs) > 0:
        return 'Partially resourced'
    else:
        return 'Resourced'


# 获取所有的资源冲突对
def get_res_confs(exec_path: nt.OpenNet):
    res_confs = []
    fire_time_map, exec_time = calc_fire_time(exec_path)
    pote_res_confs = get_pote_res_confs(exec_path)
    for [ti, tj] in pote_res_confs:
        [s_ti, e_ti] = fire_time_map[ti]
        [s_tj, e_tj] = fire_time_map[tj]
        # Note:判断两个区间是否重叠
        overlap = min(e_ti, e_tj) - max(s_ti, s_tj)
        if overlap > 0:
            print('conflict: ', [ti, tj], [s_ti, e_ti], [s_tj, e_tj])
            res_confs.append([ti, tj])
    return res_confs


# 获取所有的资源冲突对
def get_res_confs_by_fire_time(exec_path: nt.OpenNet, fire_time_map):
    res_confs = []
    pote_res_confs = get_pote_res_confs(exec_path)
    for [ti, tj] in pote_res_confs:
        [s_ti, e_ti] = fire_time_map[ti]
        [s_tj, e_tj] = fire_time_map[tj]
        # Note:判断两个区间是否重叠
        overlap = min(e_ti, e_tj) - max(s_ti, s_tj)
        if overlap > 0:
            res_confs.append([ti, tj])
    return res_confs


# 获取所有的潜在资源冲突对
def get_pote_res_confs(exec_path: nt.OpenNet):
    pote_res_confs = []
    res_map = get_res_map(exec_path)
    for res, val in res_map.items():
        req_trans = val[0]
        if len(req_trans) <= 1:
            continue
        for trani in req_trans:
            for tranj in req_trans:
                if trani != tranj:
                    elem = [trani, tranj]
                    if not is_exist(elem, pote_res_confs):
                        pote_res_confs.append(elem)
    return pote_res_confs


# 判断某个list是否存在
def is_exist(list, list_set):
    for temp_list in list_set:
        if set(list) == set(temp_list):
            return True
    return False


# 获取所有资源的请求变迁集和释放变迁集
def get_res_map(exec_path: nt.OpenNet):
    res_map = {}
    res_places = exec_path.res_places
    for res in res_places:
        req_res_map = exec_path.req_res_map
        rel_res_map = exec_path.rel_res_map
        req_trans = []
        rel_trans = []
        for key, val in req_res_map.items():
            if res in val:
                req_trans.append(key)
        for key, val in rel_res_map.items():
            if res in val:
                rel_trans.append(key)
        res_map[res] = [req_trans, rel_trans]
    return res_map


# 4.通过NSGAII获取非支配执行路径--------------------------------------
def gen_resolved_exec_path_NSGAII(exec_path: nt.OpenNet):

    # ps:首先计算变迁点火时间,不是每次计算开销很大
    org_fire_time_map, [x1, y1] = calc_fire_time(exec_path)

    pote_res_confs = get_pote_res_confs(exec_path)
    print('pote_res_confs: ', pote_res_confs)
    size = len(pote_res_confs)
    varTypes = []
    lb = []
    ub = []
    lbin = []
    ubin = []
    for i in range(size):
        varTypes.append(1)
        lb.append(-1)
        ub.append(1)
        lbin.append(1)
        ubin.append(1)

    @ea.Problem.single  #关键:定义单染色体
    def evalVars(Vars):  # 定义目标函数(含约束)
        solu = Vars.tolist()  #Vars是n维数组

        # 深拷贝exec_path
        exec_path_copy = copy.deepcopy(exec_path)
        solu_exec_path = get_solu_exec_path_by_fire_time(
            solu, pote_res_confs, org_fire_time_map, exec_path_copy)
        solu_fire_time_map, [x2, y2] = calc_fire_time(solu_exec_path)
        res_confs = get_res_confs_by_fire_time(solu_exec_path,
                                               solu_fire_time_map)
        print('res_confs: ', res_confs)
        # disc = get_waiting_delay(solu_exec_path)
        # if x2 - x1 > y2 - y1:
        #     disc = x2 - x1
        # else:
        #     disc = y2 - y1
        disc = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        # if x2 >= y1:
        #     disc = 0
        # else:  # 延时率
        #     disc = 1 - finish_earlier([x2, y2], [x1, y1])

        # disc = 1 - finish_earlier_pre([x2, y2], [x1, y1])

        print('org_exec_time, solu_exec_time, disc:', len(res_confs), [x1, y1],
              [x2, y2], disc)

        ObjV = [float(disc)]
        CV = len(res_confs)  # 计算违反约束程度

        return ObjV, CV

    problem = ea.Problem(
        name='SSGA',
        M=1,  # 目标维数
        maxormins=[1],  # 目标最小最大化标记列表，1：最小化该目标；-1：最大化该目标
        Dim=size,  # 决策变量维数
        varTypes=varTypes,  # 决策变量的类型列表，0：实数；1：整数
        lb=lb,  # 决策变量下界
        ub=ub,  # 决策变量上界s
        lbin=lbin,
        ubin=ubin,
        evalVars=evalVars)

    # 构建算法soea_SEGA_templet
    algorithm = ea.soea_steadyGA_templet(
        problem,
        ea.Population(Encoding='RI', NIND=100),
        MAXGEN=200,  # 最大进化代数。
        logTras=0,  # 表示每隔多少代记录一次日志信息，0表示不记录。
        # trappedValue=1e-6,
        # maxTrappedCount=10
    )

    res = ea.optimize(
        algorithm,
        seed=1,
        verbose=True,
        drawing=0,  #不绘制最终结果图
        outputMsg=True,
        drawLog=False,
        saveFlag=False,
    )

    # # 可行解(ps:每个是非支配的但可能存在重复)
    best_solu = res['Vars'].tolist()[0]
    print('feasible_solus:', best_solu)

    exec_path_copy = copy.deepcopy(exec_path)
    resolved_exec_path = get_solu_exec_path(best_solu, pote_res_confs,
                                            exec_path_copy)
    # 获取已解决的执行路径
    return resolved_exec_path


# 4.通过SSGA获取非支配执行路径--------------------------------------
def gen_resolved_exec_path_SSGA(exec_path: nt.OpenNet):

    # ps:首先计算变迁点火时间,不是每次计算开销很大
    org_fire_time_map, [x1, y1] = calc_fire_time(exec_path)

    pote_res_confs = get_pote_res_confs(exec_path)
    print('pote_res_confs: ', pote_res_confs)
    size = len(pote_res_confs)
    varTypes = []
    lb = []
    ub = []
    lbin = []
    ubin = []
    for i in range(size):
        varTypes.append(1)
        lb.append(-1)
        ub.append(1)
        lbin.append(1)
        ubin.append(1)

    def evalVars(pop):  # 定义目标函数(含约束)
        # print('Vars:', pop, len(pop), pop[0])
        objs = []
        const = []
        for i in range(len(pop)):
            solu = pop[i].tolist()
            # print('solu:', solu)
            # 深拷贝exec_path
            exec_path_copy = copy.deepcopy(exec_path)
            solu_exec_path = get_solu_exec_path_by_fire_time(
                solu, pote_res_confs, org_fire_time_map, exec_path_copy)
            solu_fire_time_map, [x2, y2] = calc_fire_time(solu_exec_path)
            res_confs = get_res_confs_by_fire_time(solu_exec_path,
                                                   solu_fire_time_map)
            objs.append([x2, y2])
            # ps:len(res_confs)需要转为[]
            const.append([len(res_confs)])

        # fitness = []
        # for index1, [xi, yi] in enumerate(objs):
        #     intervals = [[xj, yj] for index2, [xj, yj] in enumerate(objs)
        #                  if index1 != index2]
        #     early_prob = get_early_prob([xi, yi], intervals)
        #     fitness.append([float(early_prob)])

        # size = len(objs) - 1
        # for index1, [x1, y1] in enumerate(objs):
        #     sum_prob = 0
        #     for index2, [x2, y2] in enumerate(objs):
        #         if index1 == index2:
        #             continue
        #         prob = finish_earlier([x1, y1], [x2, y2])
        #         sum_prob += sum_prob + prob

        #     # sum_prob需要转为float且需要转为[prob]
        #     fitness.append([float(sum_prob / size)])

        min_exec_time = min([x for [x, y] in objs])
        max_exec_time = max([y for [x, y] in objs])

        print('[min_exec_time, max_exec_time]:',
              [min_exec_time, max_exec_time])

        fitness = []
        for [x, y] in objs:
            prob = finish_earlier([x, y], [min_exec_time, max_exec_time])
            # 需要转为float
            prob = float(prob * 100)
            # ps:prob需要转为[prob]
            fitness.append([prob])

        print('fitness:', np.array(fitness))

        print('res_confs: ', res_confs)

        # disc = get_waiting_delay(solu_exec_path)
        # if x2 - x1 > y2 - y1:
        #     disc = x2 - x1
        # else:
        #     disc = y2 - y1
        # disc = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        # print('org_exec_time, solu_exec_time, disc:', [x1, y1], [x2, y2], disc)

        ObjV = np.array(fitness)
        CV = np.array(const)  # 计算违反约束程度

        return ObjV, CV

    problem = ea.Problem(
        name='SSGA',
        M=1,  # 目标维数
        maxormins=[-1],  # 目标最小最大化标记列表，1：最小化该目标；-1：最大化该目标
        Dim=size,  # 决策变量维数
        varTypes=varTypes,  # 决策变量的类型列表，0：实数；1：整数
        lb=lb,  # 决策变量下界
        ub=ub,  # 决策变量上界s
        lbin=lbin,
        ubin=ubin,
        evalVars=evalVars)

    # 构建算法soea_SEGA_templet
    algorithm = ea.soea_steadyGA_templet(
        problem,
        ea.Population(Encoding='RI', NIND=50),
        MAXGEN=200,  # 最大进化代数。
        logTras=0,  # 表示每隔多少代记录一次日志信息，0表示不记录。
        # trappedValue=1e-6,
        # maxTrappedCount=10
    )

    res = ea.optimize(
        algorithm,
        seed=1,
        verbose=True,
        drawing=1,  #不绘制最终结果图
        outputMsg=True,
        drawLog=False,
        saveFlag=False,
    )

    # # 可行解(ps:每个是非支配的但可能存在重复)
    best_solu = res['Vars'].tolist()[0]
    print('feasible_solus:', best_solu)

    exec_path_copy = copy.deepcopy(exec_path)
    resolved_exec_path = get_solu_exec_path(best_solu, pote_res_confs,
                                            exec_path_copy)
    # 获取已解决的执行路径
    return resolved_exec_path


# 获取解solu更新后的执行路径
def get_solu_exec_path(solu, pote_res_confs, exec_path_copy: nt.OpenNet):
    index = 0
    # print('test: ', solu, pote_res_confs)
    fire_time_map, exec_time = calc_fire_time(exec_path_copy)
    for k in range(len(solu)):
        [ti, tj] = pote_res_confs[k]
        [s_ti, e_ti] = fire_time_map[ti]
        [s_tj, e_tj] = fire_time_map[tj]
        if solu[k] == 0:
            continue
        elif solu[k] == -1:  #ti前面插入
            if e_tj - s_ti <= 0:
                continue
            interval = [e_tj - s_ti, e_tj - s_ti]
            exec_path_copy = insert_delay_tran(index, interval, ti,
                                               exec_path_copy)
            index += 1
        else:  #tj前面插入
            if e_ti - s_tj <= 0:
                continue
            interval = [e_ti - s_tj, e_ti - s_tj]
            exec_path_copy = insert_delay_tran(index, interval, tj,
                                               exec_path_copy)
            index += 1
    return exec_path_copy


def get_solu_exec_path_by_fire_time(solu, pote_res_confs, fire_time_map,
                                    exec_path_copy: nt.OpenNet):
    index = 0
    # print('test: ', solu, pote_res_confs)
    for k in range(len(solu)):
        [ti, tj] = pote_res_confs[k]
        [s_ti, e_ti] = fire_time_map[ti]
        [s_tj, e_tj] = fire_time_map[tj]
        if solu[k] == 0:
            continue
        elif solu[k] == -1:  #ti前面插入
            if e_tj - s_ti <= 0:
                continue
            interval = [e_tj - s_ti, e_tj - s_ti]
            exec_path_copy = insert_delay_tran(index, interval, ti,
                                               exec_path_copy)
            index += 1
        else:  #tj前面插入
            if e_ti - s_tj <= 0:
                continue
            interval = [e_ti - s_tj, e_ti - s_tj]
            exec_path_copy = insert_delay_tran(index, interval, tj,
                                               exec_path_copy)
            index += 1
    return exec_path_copy


# 在执行路径中变迁tran前插入一个延时变迁
def insert_delay_tran(index, interval, tran, exec_path_copy: nt.OpenNet):
    # Note:前集有多个
    places = nt.get_preset(exec_path_copy.flows, tran)
    for place in places:
        exec_path_copy.rov_flow(place, tran)
    delay_place = 'Pd{}'.format(index)
    delay_tran = 'Td{}'.format(index)
    exec_path_copy.label_map[delay_tran] = delay_tran
    exec_path_copy.tran_delay_map[delay_tran] = interval
    exec_path_copy.add_places([delay_place])
    exec_path_copy.add_trans([delay_tran])
    for place in places:
        exec_path_copy.add_flow(place, delay_tran)
    exec_path_copy.add_flow(delay_tran, delay_place)
    exec_path_copy.add_flow(delay_place, tran)
    return exec_path_copy


# 获取执行时间最短的执行路径
def get_exec_path_st(exec_paths):
    if len(exec_paths) > 1:
        exec_path1 = exec_paths[0]
        iter_num = 1
        while iter_num <= len(exec_paths) - 1:
            fire_time_map1, [a, b] = calc_fire_time(exec_path1)
            exec_path2 = exec_paths[iter_num]
            fire_time_map2, [c, d] = calc_fire_time(exec_path2)
            # Note:判断两个区间是否重叠
            overlap = min(b, d) - max(a, c)
            if overlap > 0:  # 若重叠则通过概率计算
                if finish_earlier_probability(exec_path2, exec_path1) > 0.5:
                    exec_path1 = exec_path2
            else:
                if a >= d:  # 若不重叠则直接比较
                    exec_path1 = exec_path2
            iter_num += 1
        return exec_path1
    else:
        return exec_paths[0]


def get_early_prob(interval, intervals):
    [x, y] = interval
    for [xi, yi] in intervals:
        if x >= yi:
            return 0
    falg = 0
    for [xi, yi] in intervals:
        if xi >= y:
            falg += 1
    if falg == len(intervals):
        return 1
    # 间隔不冗余,e.g.X<=[2,3] and X<= [4,6],则[4,6]是冗余的
    non_redu_intervals = []
    for index, [xi, yi] in enumerate(intervals):
        if not is_redu_interval(index, [xi, yi], intervals) and not xi >= y:
            non_redu_intervals.append([xi, yi])
    # print('non_redu_intervals:', non_redu_intervals)
    prob1 = 0
    min_start_intervals = min([xi for [xi, yi] in non_redu_intervals])
    if min_start_intervals > x:

        def f(w):
            return 1 / (y - x)

        prob1 = integrate.quad(f, x, min_start_intervals)[0]
    # print('prob1:', prob1)
    start_list = [xi for [xi, yi] in non_redu_intervals]
    start_list.append(x)
    max_start = max(start_list)
    end_list = [yi for [xi, yi] in non_redu_intervals]
    end_list.append(y)
    min_end = min(end_list)
    min_end_in_intervals = min([yi for [xi, yi] in non_redu_intervals])

    # print('test:', max_start, min_end, min_end_in_intervals)

    def f(w):
        fj = 1 / (y - x)
        for [xi, yi] in non_redu_intervals:
            if xi <= max_start and yi >= min_end:
                fj = fj * (min_end_in_intervals - w) / (yi - xi)
        return fj

    prob2 = integrate.quad(f, max_start, min_end)[0]

    return prob1 + prob2


def is_redu_interval(index, interval, intervals):
    [xi, yi] = interval
    for indext, [xt, yt] in enumerate(intervals):
        if index == indext:
            continue
        if yt <= xi:
            return True
    return False


# 计算[ai,bi]相对[aj,bj]完成早些的概率(考虑积分区间分段情况)
def finish_earlier(interval1, interval2):
    [ai, bi] = interval1
    [aj, bj] = interval2
    if bi <= aj:
        return 1
    if bj <= ai:
        return 0
    if ai <= aj and aj <= bi and bi <= bj:
        x = sp.Symbol('x')
        y = sp.Symbol('y')
        f = 1 / ((bi - ai) * (bj - aj))
        probability = sp.integrate(f, (y, x, bj), (x, aj, bi))
        return probability + (aj - ai) / (bi - ai)
    if aj <= ai and ai <= bj and bj <= bi:
        x = sp.Symbol('x')
        y = sp.Symbol('y')
        f = 1 / ((bi - ai) * (bj - aj))
        probability = sp.integrate(f, (y, x, bj), (x, ai, bj))
        return probability
    if ai <= aj and aj <= bj and bj <= bi:
        x = sp.Symbol('x')
        y = sp.Symbol('y')
        f = 1 / ((bi - ai) * (bj - aj))
        probability = sp.integrate(f, (y, x, bj), (x, aj, bj))
        return probability + (aj - ai) / (bi - ai)
    if aj <= ai and ai <= bi and bi <= bj:
        x = sp.Symbol('x')
        y = sp.Symbol('y')
        f = 1 / ((bi - ai) * (bj - aj))
        probability = sp.integrate(f, (y, x, bj), (x, ai, bi))
        return probability


# 计算[a,b]相对[c,d]完成早些的概率
def finish_earlier_pre(interval1, interval2):
    [a, b] = interval1
    [c, d] = interval2
    x = sp.Symbol('x')
    y = sp.Symbol('y')
    f = 1 / ((b - a) * (d - c))
    probability = sp.integrate(f, (y, x, d), (x, a, b))
    return probability


# 计算exec_path1完成早些的概率
def finish_earlier_probability(exec_path1, exec_path2):
    fire_time_map1, [a, b] = calc_fire_time(exec_path1)
    fire_time_map2, [c, d] = calc_fire_time(exec_path2)
    x = sp.Symbol('x')
    y = sp.Symbol('y')
    f = 1 / (b - a) * 1 / (d - c)
    probability = sp.integrate(f, (y, x, d), (x, a, b))
    return probability


# 获取已解决的执行路径(即将变迁和它前面插入的延时变迁合并)
def get_resolved_exec_path(exec_path: nt.OpenNet, exec_path_st: nt.OpenNet):
    resolved_exec_path = copy.deepcopy(exec_path)
    flows = exec_path.flows
    flows_st = exec_path_st.flows
    for tran in exec_path.trans:
        pre_place = nt.get_preset(flows, tran)[0]
        pre_place_st = nt.get_preset(flows_st, tran)[0]
        merge_trans = [tran]
        while pre_place_st != pre_place:
            delay_tran = nt.get_preset(flows_st, pre_place_st)[0]
            merge_trans.append(delay_tran)
            pre_place_st = nt.get_preset(flows_st, delay_tran)[0]
        print('merge_trans', tran, merge_trans)
        low_time = 0
        upper_time = 0
        for merge_tran in merge_trans:
            [a, b] = exec_path_st.tran_delay_map[merge_tran]
            low_time = low_time + a
            upper_time = upper_time + b
        print('time:', low_time, upper_time)
        resolved_exec_path.tran_delay_map[tran] = [low_time, upper_time]
    return resolved_exec_path


# 5.获取由延时变迁引入的等待延时--------------------------------------
def get_waiting_delay(exec_path: nt.OpenNet):
    exec_path_copy = copy.deepcopy(exec_path)
    for tran in exec_path_copy.trans:
        if not tran.startswith('Td'):
            exec_path_copy.tran_delay_map[tran] = [0, 0]
    [x, y] = calc_fire_time(exec_path_copy)[1]
    print('waiting delay: ', x, y)
    return y


# -------------------------------测试---------------------------------#

if __name__ == '__main__':

    # path = '/Users/moqi/Desktop/原始模型/原始数据/Ca-1.xml'

    # # 1. 打印CERP信息
    # nets = ng.gen_nets(path)
    # comp_net = erpu.get_compose_net(nets)
    # comp_net.net_to_dot('abc', True)
    # print('partner, places, trans, resources:', len(nets),
    #       len(comp_net.places) + len(comp_net.res_places),
    #       len(comp_net.trans), len(comp_net.res_places))

    # 2.测试是否能够实现无冲突执行
    # optimize_res_conf_exec_path(path)

    upper_bound = 31
    tran_number_map = {}
    for i in range(1, upper_bound):
        path = '/Users/moqi/Desktop/原始模型/原始数据/Ca-{}.xml'.format(i)
        nets = ng.gen_nets(path)
        comp_net = erpu.get_compose_net(nets)
        trans = comp_net.trans
        size = len(trans)
        if size in tran_number_map.keys():
            tran_number_map[size] = tran_number_map[size] + 1
        else:
            tran_number_map[size] = 1

    tran_time_map = {}
    for i in range(1, upper_bound):
        path = '/Users/moqi/Desktop/原始模型/原始数据/Ca-{}.xml'.format(i)
        nets = ng.gen_nets(path)
        comp_net = erpu.get_compose_net(nets)
        total_time = 0
        for j in range(10):
            start_time = time.time()  #开始时间
            gen_resolved_CERP(path)
            # optimize_res_conf_exec_path(path)
            end_time = time.time()  #结束时间
            total_time = total_time + (end_time - start_time) * 1000.0
        avg_run_time = total_time / 10
        size = len(comp_net.trans)
        if size in tran_time_map.keys():
            tran_time_map[size] = tran_time_map[size] + avg_run_time
        else:
            tran_time_map[size] = avg_run_time

    tran_avg_time_map = {}
    for key, val in tran_time_map.items():
        avg_time = val / tran_number_map[key]
        tran_avg_time_map[key] = avg_time

    csv_name = '/Users/moqi/Desktop/原始模型/实验结果/avg_time.csv'
    with open(csv_name, 'w') as f:
        # 1.2基于文件对象构建csv写入对象
        writer = csv.writer(f)
        # 1.4填入内容
        for key, val in tran_avg_time_map.items():
            row = []
            row.append(key)
            row.append(val)
            writer.writerow(row)

    # exec_paths = gen_exec_paths(path)
    # for exec_path in exec_paths:
    #     if res_suff_check(exec_path) == 'Resourced':
    #         continue
    #     start_time = time.time()  #开始时间
    #     resolved_exec_path = gen_resolved_exec_path_NSGAII(exec_path)
    #     end_time = time.time()  #结束时间
    #     total_time = (end_time - start_time) * 1000.0
    #     print('total_time:', total_time)
    #     print('res_confs:', get_res_confs(resolved_exec_path))
    #     print('RCA exec time: ', calc_fire_time(exec_path)[1])

    # for i in range(1, 15):
    #     if i in [5, 6, 7, 8]:
    #         continue
    #     path = '/Users/moqi/Desktop/原始模型/归档-扩展变迁和资源/Ca-{}.xml'.format(i)

    #     exec_path = gen_exec_paths(path)[0]
    #     start_time = time.time()  #开始时间
    #     resolved_exec_path = gen_resolved_exec_path_NSGAII(exec_path)
    #     end_time = time.time()  #结束时间
    #     total_time = (end_time - start_time) * 1000.0

    #     text_EPA = 'Ca-{}: {},{},{} ms'.format(
    #         i, len(get_res_confs(resolved_exec_path)),
    #         calc_fire_time(resolved_exec_path)[1], total_time)
    #     file = open(r'/Users/moqi/Desktop/原始模型/实验结果/EPA.txt',
    #                 mode='a',
    #                 encoding='utf-8')
    #     file.write(text_EPA + '\n')
    #     file.close()

    #     # 1.1创建文件对象
    #     csv_EPA = '/Users/moqi/Desktop/原始模型/实验结果/csv结果/Ca-{}.csv'.format(i)
    #     fire_time_map = calc_fire_time(resolved_exec_path)[0]
    #     with open(csv_EPA, 'w') as f:
    #         # 1.2基于文件对象构建csv写入对象
    #         writer = csv.writer(f)
    #         # 1.3构建列表头
    #         writer.writerow(['Tran', 'Min Firing Time', 'Max Firing Time'])
    #         # 1.4填入内容
    #         for key in fire_time_map:
    #             row = []
    #             row.append(key)
    #             row.append(fire_time_map[key][0])
    #             row.append(fire_time_map[key][1])
    #             writer.writerow(row)

    #     print('\n................................................')

    # optimal_exec_path.net_to_dot('optimal_exec_path', True)
    # fire_time_map, exec_time = calc_fire_time(optimal_exec_path)
    # print('non_dom fire_time_map: ', fire_time_map)
    # print('non_dom exec_time: ', exec_time)

    # resolved_CERP = gen_resolved_CERP(path)
    # resolved_CERP.net_to_dot('rCERP', True)

    # exec_paths = gen_exec_paths(path)
    # for number, exec_path in enumerate(exec_paths):
    #     exec_path.net_to_dot('ep{}'.format(number), True)
    #     resolved_exec_path = gen_resolved_exec_path_NSGAII(exec_path)
    #     print('EPA res conf: ', len(get_res_confs(resolved_exec_path)))
    #     print('EPA exec time: ', calc_fire_time(resolved_exec_path)[1])
    #     print('\n................................................')

    # path = '/Users/moqi/Desktop/临时文件/Net 1.xml'
    # path = '/Users/moqi/Desktop/Exam1 4.xml'
    # exec_paths = gen_exec_paths(path)
    # print(len(exec_paths))
    # for index, exec_path in enumerate(exec_paths):

    # exec_path = gen_resolved_exec_path_NSGAII(exec_path)
    # print('res_confs:', get_res_confs(exec_path))
    # print('exec time: ', calc_fire_time(exec_path)[1])
    # exec_path.net_to_dot('exec_path{}'.format(index), True)

    # res_confs = get_res_confs(exec_path)
    # fire_time_map, exec_time = calc_fire_time(exec_path)
    # # 深拷贝exec_path
    # exec_path_copy = copy.deepcopy(exec_path)
    # index = 0
    # for [ti, tj] in res_confs:
    #     [s_ti, e_ti] = fire_time_map[ti]
    #     [s_tj, e_tj] = fire_time_map[tj]
    #     # 利用Zeng论文中方法解决资源冲突
    #     first_tran = [ti, tj][random.randint(0, 1)]
    #     # print('first_tran: ', first_tran)
    #     if first_tran == tj:  #ti前面插入
    #         interval = [e_tj - s_ti, e_tj - s_ti]
    #         exec_path_copy = insert_delay_tran(index, interval, ti,
    #                                            exec_path_copy)
    #         index += 1
    #     else:  #tj前面插入
    #         interval = [e_ti - s_tj, e_ti - s_tj]
    #         exec_path_copy = insert_delay_tran(index, interval, tj,
    #                                            exec_path_copy)
    #         index += 1
    # # exec_path_copy.net_to_dot('exec_path{}'.format(number), True)
    # print('RCA res conf: ', len(get_res_confs(exec_path_copy)))
    # print('RCA exec time: ', calc_fire_time(exec_path_copy)[1])

    # exec_path1 = exec_paths[0]
    # start_time = time.time()  #开始时间
    # exec_path = gen_resolved_exec_path_NSGAII(exec_path1)
    # end_time = time.time()  #结束时间
    # total_time = (end_time - start_time) * 1000.0
    # print('total_time:', total_time)
    # print('res_confs:', get_res_confs(exec_path))
    # exec_path.net_to_dot('exec_path', True)
    # print('RCA exec time: ', calc_fire_time(exec_path)[1])

    # optimize_res_conf_exec_path(path)

    # # 打印CERP信息
    # nets = ng.gen_nets(path)
    # comp_net = erpu.get_compose_net(nets)
    # # comp_net.net_to_dot('abc', True)

    # res_confs_size = 0
    # exec_paths = gen_exec_paths(path)
    # for exec_path in exec_paths:
    #     res_confs = get_res_confs(exec_path)
    #     print('res_confs: ', res_confs)
    #     res_confs_size = res_confs_size + len(res_confs)

    # print('partner, places, trans:', len(nets),
    #       len(comp_net.places) + len(comp_net.res_places),
    #       len(comp_net.trans))
    # print('res_confs_size:', res_confs_size)

    # exec_path.net_to_dot('exec_path', True)
    # resol_exec_path = gen_resolved_exec_path_NSGAII(exec_path)
    # resol_exec_path = rename_exec_path(resol_exec_path)

    # resol_exec_path.net_to_dot('resol_exec_path', True)
    # fire_time_map, exec_time = calc_fire_time(exec_path)
    # print('pre fire_time_map: ', fire_time_map)
    # print('pre exec_time: ', exec_time)
    # res_map = get_res_map(exec_path)
    # print('res_map: ', res_map)
    # pote_res_confs = get_pote_res_confs(exec_path)
    # print('pote_res_confs: ', pote_res_confs)
    # res_confs = get_res_confs(exec_path)
    # print('res_confs: ', res_confs)
    # print(res_suff_check(exec_path))
    # pote_res_confs = [['T3', 'T5'], ['T4', 'T2']]
    # exec_path = get_solu_exec_path([1, 1], pote_res_confs, exec_path)
    # exec_path.net_to_dot('exec_path', True)
    # fire_time_map, exec_time = calc_fire_time(exec_path)
    # print('fire_time_map: ', fire_time_map)
    # print('exec_time: ', exec_time)
    # print(res_suff_check(exec_path))

    # non_dom_exec_paths = gen_non_dom_exec_paths_exhaustive(exec_path)
    # print('size:', len(non_dom_exec_paths))
    # for i, non_dom_exec_path in enumerate(non_dom_exec_paths):
    #     non_dom_exec_path.net_to_dot('non_dom_exec_path{}'.format(i), True)
    #     fire_time_map, exec_time = calc_fire_time(non_dom_exec_path)
    #     print('non_dom fire_time_map: ', fire_time_map)
    #     print('non_dom exec_time: ', exec_time)

    # non_dom_exec_paths = gen_non_dom_exec_paths_NSGAII(exec_path)
    # print('size:', len(non_dom_exec_paths))
    # for i, non_dom_exec_path in enumerate(non_dom_exec_paths):
    #     non_dom_exec_path.net_to_dot('non_dom_exec_path{}'.format(i), True)
    #     fire_time_map, exec_time = calc_fire_time(non_dom_exec_path)
    #     print('non_dom fire_time_map: ', fire_time_map)
    #     print('non_dom exec_time: ', exec_time)

    # optimal_exec_path = gen_optimal_exec_path(path)
    # optimal_exec_path.net_to_dot('optimal_exec_path', True)
    # fire_time_map, exec_time = calc_fire_time(optimal_exec_path)
    # print('non_dom fire_time_map: ', fire_time_map)
    # print('non_dom exec_time: ', exec_time)

    # start_time = time.time()  #开始时间
    # resol_CERP = gen_resolved_CERP(path)
    # end_time = time.time()  #结束时间
    # total_time = (end_time - start_time) * 1000.0
    # print('total_time:', total_time)

    # resol_CERP.print_infor()
    # resol_CERP.net_to_dot('resol_CERP', True)
