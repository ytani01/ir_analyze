#!/usr/bin/python3 -u
#
# (c) 2018 Yoichi Tanibayashi
#
# !!! IMPORTANT !!!
#
#	-u option of python command is mandatory
#
import sys, os
import click
import subprocess, threading, queue
import time
import builtins

SIG_LONG	= 99999 # usec

SIG_CH		= {
    'zero':	'0',
    'one':	'1',
    'leader':	'-',
    'trailer':	'/',
    'repeat':	'*',
    'misc':	'?'
}

Mode		= 'mode2.out'

HexOnly		= False
BinOnly		= False

#####
##
def print(*args, sep=' ', end='\n', file=None, force_out=False):
    if ( not HexOnly and not BinOnly ) or force_out:
        builtins.print(*args, sep=sep, end=end, file=file)
    
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

    def readline(self, tout=0.6):
        try:
            line = self.lineq.get(block=True, timeout=tout)
        except queue.Empty:
            line = None
        return line

    def close(self):
        #print('stop: ', self.cmd, file=sys.stderr)
        self.proc.terminate()
        self.proc.wait()

## データ読み込み
def load_input(file, cmd_name='', mode2=False, forever=False):
    global Mode

    tout = 0.6
    if forever:
        tout = 0.1
        
    raw_data = {'pulse':[], 'space':[]}
    
    file_flag = False
    if Mode == 'mode2':
        f = CmdOut(['mode2'])
        f.start()
    elif file != '':
        try:
            f =open(file)
        except FileNotFoundError:
            print('Error: No such file:%s' % file, file=sys.stderr)
            return None
        file_flag = True
    else:
        f = sys.stdin

    data_start = False
    n = 0
    w_count = 5
    while True:
        line = f.readline(tout = tout)
        if not line:
            # mode2 の場合
            if Mode == 'mode2':
                if data_start:
                    break

                if forever:
                    continue

                # 入力をしばらく待ち、何も入力がなければ終了
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
            # データ部分の最初を探す
            if len(data) == 0:
                continue

            if Mode != 'lircd.conf':
                if data[0] == 'space':
                    data_start = True
                    print(file=sys.stderr)
                    sys.stderr.flush()
            else: # lircd.conf
                #print(data)
                if data[0] == 'name' and data[1] == cmd_name:
                    data_start = True
                    key = 'pulse'
                    print(file=sys.stderr)
                    sys.stderr.flush()
            continue

        if Mode == 'lircd.conf':
            # 以下のような数値の羅列
            # name on
            #   4000 3000 2000 1000 500 1000 500 ..
            if len(data) == 0:
                continue
            
            if not data[0].isdigit():
                # data end
                break
            
            for us in data:
                if not us.isdigit():
                    print('Error:Invalid data:', data)
                    return None

                raw_data[key].append(int(us))
                
                n += 1
                key = ['pulse', 'space'][n % 2]
                #print(key, ' ', end='')
        
        else: # mode2, mode2.out
            # mode2コマンドの出力形式
            #	pulse 600
            #   space 500
            #   :
            [key, us] = data
            us = int(us)
            raw_data[key].append(us)
            n += 1

        if Mode == 'mode2':
            try:
                sig_len = int(us / 500)
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

    if Mode == 'mode2':
        f.close()
        f.join()
    elif file_flag:
        f.close()

    if not data_start:
        return None

    raw_data['space'].append(SIG_LONG)
    if len(raw_data['pulse']) != len(raw_data['space']):
        print('! Error: invalid data', raw_data, file=sys.stderr)
        return None

    print('# Ndata: %d' % n)
    
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
def print_data(raw_data, pair_list, pair_to_sig, sig_to_pair, T1, raw_out):
    sig_str = ''
    sig_usec = 0
    idx = 0
    for [t1, t2] in pair_list:
        ch = SIG_CH[pair_to_sig[t1, t2]]
        sig_usec += raw_data['pulse'][idx] + raw_data['space'][idx]
        if ch == SIG_CH['trailer']:
            sig_usec -= raw_data['pulse'][idx] + raw_data['space'][idx]
            sig_str += ' %s%dus%s ' % (':', sig_usec, ch)
            sig_usec = 0
        else:
            sig_str += ch
        idx += 1

    for key in ['leader', 'repeat', 'misc']:
        sig_str = sig_str.replace(SIG_CH[key], ' ' + SIG_CH[key] + ' ')

    sig_str_list = [[]]
    for s in sig_str.split():
        sig_str_list[-1].append(s)
        if s[-1] == '/':
            sig_str_list.append([])
    if len(sig_str_list[-1]) == 0:
        sig_str_list.pop(-1)

    print_bit_pattern(sig_str_list, '# bit pattern', '## BIT: ')
    print()
    print_hex_data(sig_str_list, '# hex data', '## HEX: ')

    if raw_out:
        print()
        print_raw_data(sig_str_list, raw_data, pair_list, T1,
                       '# raw data for lircd.conf')

## 文字列<s>を指定した文字数<n>毎に分割
def split_str(s, n):
    s1 = ''
    s = s[::-1]
    for i in range(0, len(s), n):
        s1 += s[i:i + n] + ' '
    s = s1.strip()
    s = s[::-1]
    return s

## ビットパターン出力
def print_bit_pattern(sig_list, title='', prefix=''):
    if title != '':
        print(title)

    f1 = False
    f2 = False
    for line in sig_list:
        print(prefix, end='')
        for s in line:
            if s[0] in SIG_CH['zero'] + SIG_CH['one']:
                s = split_str(s, 4)
                if BinOnly:
                    f1 = True
                    f2 = True
            print(s + ' ', end='', force_out=f1)
            f1 = False
        print(force_out=f2)
        f2 = False

## 16進データ出力
def print_hex_data(sig_list, title='', prefix=''):
    if title != '':
        print(title)
    f1 = False
    f2 = False
    for line in sig_list:
        print(prefix, end='')
        for s in line:
            if s[0] in SIG_CH['zero'] + SIG_CH['one']:
                hex_len = int(len(s) / 4 + 0.99)
                s = ('0' * hex_len + '%X' % int(s, 2))[-hex_len:]
                if HexOnly:
                    f1 = True
                    f2 = True
            print(s + ' ', end='', force_out=f1)
            f1 = False
        print(force_out=f2)
        f2 = False

## lircd.conf raw形式の出力
def print_raw_data(sig_str_list, raw_data, pair_list, T1, title=''):
    if title != '':
        print(title)

    print('\tname\tcommand')
    idx = 0
    for line in sig_str_list:
        for sig in line:
            if sig[0] in SIG_CH['zero'] + SIG_CH['one']:
                n = 0
                for s in sig:
                    if n % 4 == 0 and n != 0:
                        print()
                    t1 = raw_data['pulse'][idx]
                    t2 = raw_data['space'][idx]
                    print('%5d %5d ' % (t1, t2), end='')
                    idx += 1
                    n += 1
            else:
                t1 = raw_data['pulse'][idx]
                t2 = raw_data['space'][idx]
                print('%5d %5d ' % (t1, t2), end='')
                idx += 1
            print()
    
##### main
@click.command(help='LIRC IR Analyzer')
@click.argument('infile', metavar='[input_file]', default='',
                type=click.Path())
@click.argument('cmd_name', metavar='[cmd]', default='')
@click.option('--mode2', '-m', is_flag=True, default=False,
              help='input from mode2 command')
@click.option('--raw', '-r', is_flag=True, default=False,
              help='output raw data for lircd.conf')
@click.option('--forever', '-f', is_flag=True, default=False,
              help='loop forever')
@click.option('--hexonly', '-h', is_flag=True, default=False,
              help='output hex code only')
@click.option('--binonly', '--bitonly', '-b', is_flag=True, default=False,
              help='output bit pattern code only')
def main(infile, cmd_name, mode2, raw, forever, hexonly, binonly):
    global Mode
    global HexOnly
    global BinOnly

    HexOnly = hexonly
    BinOnly = binonly
    
    if infile != '':
        print('# infile   :', infile)
    if cmd_name != '':
        print('# cmd_name :', cmd_name)
    if mode2:
        print('# mode2    :', mode2)
    if raw:
        print('# raw      :', raw)

    Mode = 'mode2.out'
    if mode2:
        Mode = 'mode2'
    elif len(infile) > 0:
        Mode = 'mode2.out'
        if len(cmd_name) > 0:
            Mode = 'lircd.conf'
    print('# Mode     :', Mode)

    raw_data = load_input(infile, cmd_name, mode2, forever)
    while raw_data:
        decode_sig(raw_data, mode2, raw)
        print()

        raw_data = None
        if Mode == 'mode2':
            raw_data = load_input(infile, cmd_name, mode2, forever)
        
def decode_sig(raw_data, mode2, raw):
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
    if [round(sig_pattern[0][0]), round(sig_pattern[0][1])] != [1, 1]:
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

    #print('#', pair_to_sig)

    sig_to_pair = {}
    for pair in pair_to_sig.keys():
        sig = pair_to_sig[pair]
        if sig not in sig_to_pair.keys():
            sig_to_pair[sig] = []
        sig_to_pair[sig].append(pair)
    for sig in sig_to_pair.keys():
        print('## %-8s:' % sig, end='')
        for p in sig_to_pair[sig]:
            print(p, ' ', end='')
        print()

    print('# Signal Format: %s' % sig_format)
    print()

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
    print_data(raw_data, pair_list, pair_to_sig, sig_to_pair, T1, raw)

#####
if __name__ == '__main__':
    main()
