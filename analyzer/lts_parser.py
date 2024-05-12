from lts import LTS, Tran


# 1.解析PAT的LTS---------------------------------------------
def parse_lts(input_txt, rec_tau):
    start = ''
    ends = set()
    states = set()
    trans = []
    acts = set()
    with open(input_txt, 'r', encoding='utf8') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if not line.startswith('Source'):
                continue
            else:
                print("line: ", line)
                left_bak_indexs = [
                    i for i in range(len(line)) if line[i] == '['
                ]
                right_bak_indexs = [
                    i for i in range(len(line)) if line[i] == ']'
                ]
                line_indexs = [
                    i for i in range(len(line)) if line[i:i + 5] == '-----'
                ]
                act = line[line_indexs[0] + 5:line_indexs[1]]
                if act == 'τ':
                    label = 'tau'
                elif '?' in act:
                    if rec_tau == 1:
                        label = 'tau'
                    else:
                        label = 'rec' + act[act.index("?") + 1:]
                elif '!' in act:
                    label = 'send' + act[act.index("!") + 1:]
                else:
                    label = act
                state_from = line[left_bak_indexs[0] + 1:right_bak_indexs[0]]
                state_to = line[left_bak_indexs[1] + 1:right_bak_indexs[1]]
                print(state_from, label, state_to)
                if label == "init":
                    states.add(state_to)
                    start = state_to
                elif label == "terminate":
                    states.add(state_from)
                    ends.add(state_from)
                else:
                    states.add(state_from)
                    states.add(state_to)
                    tran = Tran(state_from, label, state_to)
                    trans.append(tran)
                    if label != "tau":
                        acts.add(label)
        print(start, states, acts)
        return LTS(start, ends, states, trans), list(acts)


# 2.生成mCRL2文件---------------------------------------------
def gen_mcrl2(input_txt, mcrl2_file, rec_tau):

    lts, acts = parse_lts(input_txt, rec_tau)

    with open(mcrl2_file, 'w', encoding='utf8') as f:
        start, ends, states, trans = lts.get_infor()
        if ends:  #有终止状态,设为mCRL2中动作terminate
            act_str = 'act ' + ', '.join(acts) + ', terminate;' + '\n'
        else:
            act_str = 'act ' + ', '.join(acts) + ';' + '\n'
        f.write(act_str)
        f.write('proc \n')

        states = list(states)
        for state in states:
            to_trans = get_to_trans(state, trans)
            print('to_trans: ', states, to_trans)
            if len(to_trans) > 0:
                exp_str = []
                for to_tran in to_trans:
                    state_from, label, state_to = to_tran.get_infor()
                    exp_str.append(label + "." + 'P' + state_to)
                state_str = 'P' + state + " = " + ' + '.join(exp_str) + ';\n'
                f.write(state_str)
            else:
                # 死锁状态编码为delta,正常终止状态设为terminate
                if state not in ends:
                    state_str = 'P' + state + ' = delta;\n'
                    f.write(state_str)
                else:
                    state_str = 'P' + state + ' = terminate;\n'
                    f.write(state_str)
        f.write('init ' + 'P' + start + ';\n')


# 获取从state出发到达的迁移集
def get_to_trans(state, trans):
    to_trans = []
    for tran in trans:
        state_from, label, state_to = tran.get_infor()
        if state == state_from:
            to_trans.append(tran)
    return to_trans


# -------------------------------测试---------------------------------#

if __name__ == '__main__':

    # 'sys_k.txt'是输入lts文件, 'sys_k.mcrl2'是产生的mCRL2文件, '1'表示将接收动作设为tau
    gen_mcrl2('case_4_1.txt', 'case_4_1.mcrl2', 1)

# -------------------------------------------------------------------#
