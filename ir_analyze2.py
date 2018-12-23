#!/usr/bin/python3 -u
#
import sys, os
import click
import subprocess, threading, queue
import time

SIG_LONG	= 99999 # usec

SIG_CH		= {
    'zero':	'0',
    'one':	'1',
    'leader':	'-',
    'trailer':	'/',
    'repeat':	'*',
    'misc':	'?'
}

#####
##
class CmdOut(threading.Thread):
    def __init__(self, cmd):
        self.cmd = cmd
        self.lineq = queue.Queue()
        self.proc = subprocess.Popen(self.cmd,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     universal_newlines=True, bufsize=0)
        super().__init__()

    def run(self):
        #print('start: ', self.cmd, file=sys.stderr)
        while True:
            try:
                line = self.proc.stdout.readline()
                if not line:
                    break
                self.lineq.put(line)
            except:
                break

    def __del__(self):
        pass

    def readline(self, t=1):
        try:
            line = self.lineq.get(block=True, timeout=t)
        except queue.Empty:
            line = None
        return line

    def close(self):
        #print('stop: ', self.cmd, file=sys.stderr)
        self.proc.terminate()
        self.proc.wait()

## データ読み込み
def load_input(file, mode2, cmd_name=''):
    raw_data = {'pulse':[], 'space':[]}
    
    file_flag = False
    if len(file) > 0:
        f =open(file)
        file_flag = True
    elif mode2:
        f = CmdOut(['mode2'])
        f.start()
    else:
        f = sys.stdin

    data_start = False
    n = 0
    w_count = 5
    while True:
        line = f.readline()
        if not line:
            if mode2:
                if data_start:
                    break
                w_count -= 1
                if w_count > 0 and w_count <= 3:
                    print('%d!..' % w_count, end='', file=sys.stderr)
                    sys.stderr.flush()
                if w_count > 0:
                    continue
                else:
                    print('END', file=sys.stderr)
                    sys.stderr.flush()
            break
        data = line.split()
        if not data_start:
            if len(data) == 0:
                continue
            if data[0] == 'space':
                data_start = True
                print('', file=sys.stderr)
                sys.stderr.flush()
            continue

        [key, usec] = data
        usec = int(usec)
        raw_data[key].append(usec)

        try:
            n += 1
            if mode2:
                sig_len = int(usec / 500)
                if sig_len == 0:
                    sig_len = 1
                if sig_len > 20:
                    sig_len = 20
                for i in range(sig_len):
                    ch = '_'
                    if key == 'pulse':
                        ch = '*'
                    print(ch, end='', file=sys.stderr)
                sys.stderr.flush()
        except BrokenPipeError:
            break

    if file_flag:
        f.close()
    if mode2:
        f.close()
        f.join()

    if not data_start:
        return None

    raw_data['space'].append(SIG_LONG)

    print(' [%d]' % n, file=sys.stderr)
    sys.stderr.flush()
    
    if len(raw_data['pulse']) == len(raw_data['space']):
        return raw_data
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
def print_data(data, pair_list, pair_to_sig):
    sig_str = ''
    sig_usec = 0
    idx = 0
    for [t1, t2] in pair_list:
        ch = SIG_CH[pair_to_sig[t1, t2]]
        sig_usec += data['pulse'][idx] + data['space'][idx]
        #print('%4d, %4d: %d' % (data['pulse'][idx], data['space'][idx], sig_usec))
        if ch == SIG_CH['trailer']:
            sig_usec -= data['pulse'][idx] + data['space'][idx]
            sig_str += ' %s%dus%s ' % (':', sig_usec, ch)
            sig_usec = 0
        else:
            sig_str += ch
        idx += 1

    for key in ['leader', 'repeat', 'misc']:
        sig_str = sig_str.replace(SIG_CH[key], ' ' + SIG_CH[key] + ' ')

    sig_str_list = sig_str.split()

    print_bit_pattern(sig_str_list, '# bit pattern', '## BIT: ')
    print_hex_data(sig_str_list, '# hex data', '## HEX: ')

## ビットパターン出力
def print_bit_pattern(list, title='', prefix=''):
    if len(title) > 0:
        print(title)
    n = 0
    for s in list:
        n += 1
        if s == SIG_CH['leader']:
            if n > 1:
                print()
            print(prefix, end='')
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
def print_hex_data(list, title='', prefix=''):
    if len(title) > 0:
        print(title)
    n = 0
    for s in list:
        n += 1
        if s == SIG_CH['leader']:
            if n > 1:
                print()
            print(prefix, end='')
        if s[0] in SIG_CH['zero'] + SIG_CH['one']:
            hex_len = int(len(s) / 4 + 0.99)
            s = ('0' * hex_len + '%X' % int(s, 2))[-hex_len:]
            #s = split_str(s, 4)
        print(s + ' ', end='')
    print()
        
    
##### main
@click.command(help='IR Analyzer')
@click.option('--mode2', '-m', is_flag=True, default=False,
              help='input from mode2 command')
@click.argument('infile', metavar='[input_file]', default='')
def main(infile, mode2):
    raw_data = load_input(infile, mode2)
    while raw_data:
        decode_sig(raw_data, mode2)
        print(file=sys.stderr)
        raw_data = None
        if mode2:
            raw_data = load_input(infile, mode2)
        
def decode_sig(raw_data, mode2):
    fq_dist		= {'pulse':[], 'space':[]}
    T1			= {'pulse': 0, 'space': 0}
    idx_list		= {'pulse':[], 'space':[]}
    pair_list		= []
    normalized_pair	= []
    sig_pattern		= []
    pair_to_sig		= {(1, 1): 'zero'}
    sig_format		= '???'

    for key in ['pulse', 'space']:
        #
        # 度数分布を元に、T1を求める
        #
        fq_dist[key] = freq_dist(raw_data[key], .2)
        T1[key] = get_t1(raw_data[key])

        #
        # T1を元に、係数のリストを作成: idx_list
        #
        for v in raw_data[key]:
            for idx in range(len(fq_dist[key])):
                l = fq_dist[key][idx]
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
                    idx_list[key].append(t_val)
                    break
    print('# T1[pulse, space] = [%d,%d]' % (T1['pulse'], T1['space']))

    #
    # [pulse, space]ペアのリスト(係数と正規化した値)を作成
    #
    for idx in range(len(idx_list['pulse'])):
        t_pair = [idx_list['pulse'][idx], idx_list['space'][idx]]
        v_pair = [round(T1['pulse'] * t_pair[0]),
                  round(T1['space'] * t_pair[1])]
        pair_list.append(t_pair)
        normalized_pair.append(v_pair)
    #print(pair_list)
    #print(normalized_pair)

    #
    # 信号パターンを抽出
    #
    sig_pattern = sorted(list(map(list, set(map(tuple, pair_list)))))    
    #print(sig_pattern)
    if sig_pattern[0] != [1, 1]:
        print('! Error: [1, 1] is not found')

    #
    # 信号パターンを解析
    # 信号フォーマットの種類も判別
    #
    for [p1, p2] in sig_pattern:
        p = [round(p1), round(p2)]
        # zero ?
        if p == [1, 1]:
            pair_to_sig[p1, p2] = 'zero'
            continue
        # one ?
        if p in [[2, 1], [1, 2], [1, 3], [1, 4], [1, 5]]:
            pair_to_sig[p1, p2] = 'one'
            if p[0] == 2:
                sig_format = 'SONY'
            continue
        # leader ?
        if  p in [[3, 1], [4, 1], [5, 1]] or \
            p[0] >= 3 and p[1] >= 3:
            t1 = p1 * T1['pulse']
            t2 = p2 * T1['space']

            # if SONY
            if sig_format == 'SONY':
                if p[0] in [3, 4, 5] and p[1] == 1:
                    pair_to_sig[p1, p2] = 'leader'
                    continue
                
            # NEC ?
            if abs(t1 - 9000) <= 1000 and abs(t2 - 4500) <= 500:
                pair_to_sig[p1, p2] = 'leader'
                sig_format = 'NEC'
                continue

            # AHEA ?
            if abs(t1 - (425*8)) <= 800 and abs(t2 - (425*4)) <= 300:
                pair_to_sig[p1, p2] = 'leader'
                sig_format = 'AEHA'
                continue

        # trailer ?
        if sig_format == 'SONY':
            if p[0] == 2 and p[1] > 10:
                pair_to_sig[p1, p2] = 'trailer'
                continue

        if p[0] == 1 and p[1] > 10:
            pair_to_sig[p1, p2] = 'trailer'
            continue

        # repeat ?
        if p[0] > 3 and p[1] > 3:
            pair_to_sig[p1, p2] = 'repeat'
            continue

        # unknown
        pair_to_sig[p1, p2] = 'misc'

    print('# sig_format = %s' % sig_format)
    print('#', pair_to_sig)

    # leader が見つからなかった場合、他の信号パターンで代用
    if 'leader' not in pair_to_sig.values():
        print('# !?')
        for key in pair_to_sig.keys():
            if pair_to_sig[key] == 'misc':
                pair_to_sig[key] = 'leader'
        print('#', pair_to_sig)    

    #
    # 解析に基づいて、信号を解読
    #
    print_data(raw_data, pair_list, pair_to_sig)

#####
if __name__ == '__main__':
    main()
