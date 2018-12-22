#!/usr/bin/python3 -u
#
import sys, os
import click
import subprocess

SIG_LONG	= 99999 # usec

InData		= {'pulse':[], 'space':[]}
FqDist		= {'pulse':[], 'space':[]}
T1		= {'pulse': 0, 'space': 0}
IdxList		= {'pulse':[], 'space':[]}
TPairList	= []
NormalizedPair	= []
SigPattern	= []

SIG_CH		= {
    'zero':	'0',
    'one':	'1',
    'leader':	'-',
    'trailer':	'/',
    'repeat':	'*',
    'misc':	'?'
}

PairToSig	= {(1, 1): 'zero'}

SigFormat	= '???'

#####
##
def mode2_start():
    proc = subprocess.Popen('mode2', stdout=subprocess.PIPE,
                            universal_newlines=True, bufsize=0)
    return proc

def mode2_stop(proc):
    proc.terminate()
    proc.wait()
    
def mode2_get(proc):
    pass

## データ読み込み
def load_input(file, mode2):
    file_flag = False
    if len(file) > 0:
        f =open(file)
        file_flag = True
    else:
        if mode2:
            proc = mode2_start()
        else:
            f = sys.stdin

    data_start = False
    n = 0
    while True:
        if mode2:
            line = mode2_get(proc)
        else:
            line = f.readline()
        if not line:
            if mode2:
                mode2_stop(proc)
            break
        data = line.split()
        if not data_start:
            if len(data) == 0:
                continue
            if data[0] == 'space':
                data_start = True
            continue

        data[1] = int(data[1])
        InData[data[0]].append(data[1])

        try:
            print('.', end='')
            n += 1
            if n % 100 == 0:
                print('[%d]' % n, end='')
        except BrokenPipeError:
            break

    if file_flag:
        f.close()

    if not data_start:
        return None

    InData['space'].append(SIG_LONG)
    
    print('[%d]' % len(InData['pulse']))
    
    if len(InData['pulse']) == len(InData['space']):
        return InData
    return None

## 度数分布
def freq_dist(data, step):
    newlist = []

    newlist.append([])
    for val in sorted(data):
        if len(newlist[-1]) > 0:
            if step < 1:
                next_step = newlist[-1][-1] * ( 1 + step )
            else:
                next_step = newlist[-1][-1] + step
            if newlist[-1][-1] < SIG_LONG and val > next_step:
                newlist.append([])
        newlist[-1].append(val)

    return newlist

## T1の計算
def get_t1(data):
    t1_list = freq_dist(data, .1)[0]
    if len(t1_list) > 10:
        t1_list.pop()
        t1_list.pop(0)
    return round(sum(t1_list) / len(t1_list))

## データ出力
def print_data():
    global InData
    
    sig_str = ''
    sig_usec = 0
    idx = 0
    for [t1, t2] in TPairList:
        ch = SIG_CH[PairToSig[t1, t2]]
        sig_usec += InData['pulse'][idx] + InData['space'][idx]
        #print('%4d, %4d: %d' % (InData['pulse'][idx], InData['space'][idx], sig_usec))
        if ch == SIG_CH['trailer']:
            sig_usec -= InData['space'][idx]
            sig_str += ' %s%d%s ' % (ch, sig_usec, ch)
            sig_usec = 0
        else:
            sig_str += ch
        idx += 1

    for key in ['leader', 'repeat', 'misc']:
        sig_str = sig_str.replace(SIG_CH[key], ' ' + SIG_CH[key] + ' ')

    sig_str_list = sig_str.split()

    print_bit_pattern(sig_str_list)
    print_hex_data(sig_str_list)

## ビットパターン出力
def print_bit_pattern(list):
    for s in list:
        if s == SIG_CH['leader']:
            print()
        if s[0] in SIG_CH['zero'] + SIG_CH['one']:
            s = split_str(s, 4)
        print(s + ' ', end='')
    print()

## 文字列<s>を指定した文字数<n>毎に分割
def split_str(s, n):
    s1 = ''
    s = s[::-1]
    for i in range(0, len(s), n):
        s1 += s[i:i + n] + ' '
    s = s1.strip()
    s = s[::-1]
    return s

## 16進データ出力
def print_hex_data(list):
    for s in list:
        if s == SIG_CH['leader']:
            print()
        if s[0] in SIG_CH['zero'] + SIG_CH['one']:
            hex_len = int(len(s) / 4 + 0.99)
            s = ('0' * hex_len + '%X' % int(s, 2))[-hex_len:]
            #s = split_str(s, 4)
        print(s + ' ', end='')
    print()
        
    
##### main
@click.command(help='IR Analyzer')
@click.option('--mode2', '-m', is_flag=True, default=False)
@click.argument('infile', metavar='<input_file>', default='')
def main(infile, mode2):
    global InData, SigFormat

    # データ読み込み
    InData = load_input(infile, mode2)
    if not InData:
        print('Error: no data')
        return

    for key in ['pulse', 'space']:
        #
        # 度数分布を元に、T1を求める
        #
        FqDist[key] = freq_dist(InData[key], .2)
        T1[key] = get_t1(InData[key])

        #
        # T1を元に、係数のリストを作成: IdxList
        #
        for v in InData[key]:
            for idx in range(len(FqDist[key])):
                l = FqDist[key][idx]
                if v >= min(l) and v <= max(l):
                    t_val = (sum(l) / len(l)) / T1[key]
                    f = 1
                    if t_val > 50:
                        f = 0.1
                    if t_val < 15:
                        f = 10
                    t_val = round(t_val * f) / f
                    if t_val > 99:
                        t_val = 99
                    IdxList[key].append(t_val)
                    break
    print('T1[pulse, space] = [%d,%d]' % (T1['pulse'], T1['space']))

    #
    # [pulse, space]ペアのリスト(係数と正規化した値)を作成
    #
    for idx in range(len(IdxList['pulse'])):
        t_pair = [IdxList['pulse'][idx], IdxList['space'][idx]]
        v_pair = [round(T1['pulse'] * t_pair[0]),
                  round(T1['space'] * t_pair[1])]
        TPairList.append(t_pair)
        NormalizedPair.append(v_pair)
    #print(TPairList)
    #print(NormalizedPair)

    #
    # 信号パターンを抽出
    #
    SigPattern = sorted(list(map(list, set(map(tuple, TPairList)))))    
    #print(SigPattern)
    if SigPattern[0] != [1, 1]:
        print('Error')

    #
    # 信号パターンを解析
    # 信号フォーマットの種類も判別
    #
    for [p1, p2] in SigPattern:
        p = [round(p1), round(p2)]
        # zero ?
        if p == [1, 1]:
            PairToSig[p1, p2] = 'zero'
            continue
        # one ?
        if p in [[2, 1], [1, 2], [1, 3], [1, 4], [1, 5]]:
            PairToSig[p1, p2] = 'one'
            if p[0] == 2:
                SigFormat = 'SONY'
            continue
        # leader ?
        if  p in [[3, 1], [4, 1], [5, 1]] or \
            p[0] >= 3 and p[1] >= 3:
            t1 = p1 * T1['pulse']
            t2 = p2 * T1['space']

            # if SONY
            if SigFormat == 'SONY':
                if p[0] in [3, 4, 5] and p[1] == 1:
                    PairToSig[p1, p2] = 'leader'
                    continue
                
            # NEC ?
            if abs(t1 - 9000) <= 1000 and abs(t2 - 4500) <= 500:
                PairToSig[p1, p2] = 'leader'
                SigFormat = 'NEC'
                continue

            # AHEA ?
            if abs(t1 - (425*8)) <= 800 and abs(t2 - (425*4)) <= 300:
                PairToSig[p1, p2] = 'leader'
                SigFormat = 'AEHA'
                continue

        # trailer ?
        if SigFormat == 'SONY':
            if p[0] == 2 and p[1] > 10:
                PairToSig[p1, p2] = 'trailer'
                continue

        if p[0] == 1 and p[1] > 10:
            PairToSig[p1, p2] = 'trailer'
            continue

        # repeat ?
        if p[0] > 3 and p[1] > 3:
            PairToSig[p1, p2] = 'repeat'
            continue

        # unknown
        PairToSig[p1, p2] = 'misc'

    print('SigFormat = %s' % SigFormat)
    print(PairToSig)

    # leader が見つからなかった場合、他の信号パターンで代用
    if 'leader' not in PairToSig.values():
        print('!!')
        for key in PairToSig.keys():
            if PairToSig[key] == 'misc':
                PairToSig[key] = 'leader'
        print(PairToSig)    

    #
    # 解析に基づいて、信号を解読
    #
    print_data()

#####
if __name__ == '__main__':
    main()
