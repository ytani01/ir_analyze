#!/usr/bin/python3 -u
#
# (c) 2018 Yoichi Tanibayashi
#
# !!! IMPORTANT !!!
#
#	-u option of python command is mandatory
#
import sys
import click
import builtins

import CmdOut

SIG_LONG	= 99999 # usec

SIG_CH		= {
    'leader':	'-',
    'zero':	'0',
    'one':	'1',
    'trailer':	'/',
    'repeat':	'*',
    'misc':	'?'
    }
SIG_STR_01	= SIG_CH['zero'] + SIG_CH['one']

BitOnly = False
HexOnly = False

#
# print()関数のラッパー
#
def print(*args, sep=' ', end='\n', file=None, force_out=False):
    global BitOnly
    global HexOnly
    
    if ( not HexOnly and not BitOnly ) or force_out:
        builtins.print(*args, sep=sep, end=end, file=file)
    return

#
# データ読み込み
#
def load_input(mode, infile='', btn='', forever=False):
    raw_data = []

    if mode == 'exec.mode2':
        f = CmdOut.CmdOut(['mode2'])
        f.start()
    else:
        if infile == '':
            print('Error: infile=\'\'')
            return None
        try:
            f = open(infile)
        except:
            print('Error: open(%s)' % infile, file=sys.stderr)
            return None

    data_start = False
    wait_count = 5
    while True:
        if mode == 'exec.mode2':
            tm_out = 0.6
            if forever:
                tm_out = 0.2
            line = f.readline(timeout = tm_out)
        else:
            line = f.readline()

        if not line:	# timeout
            if mode != 'exec.mode2':
                break

            # mode == 'exec.mode2'
            if data_start:
                # データ開始後のタイムアウトは終了
                break

            if forever:
                continue

            # カウントダウン
            wait_count -= 1
            if wait_count > 0:
                if wait_count <= 3:
                    print('%d..' % wait_count, end='', file=sys.stderr)
                    sys.stderr.flush()
                continue
            else:
                print('END', file=sys.stderr)
                sys.stderr.flush()
            break

        data = line.split()
        if not data_start:
            # データの開始地点を探す
            if len(data) == 0:
                continue
            if mode == 'lircd.conf':
                # 'name btn' の行を探す
                if data[0] == 'name' and data[1] == btn:
                    data_start = True
                    key = 'pulse'
            else:  # mode2 コマンドの出力形式
                if data[0] == 'space':
                    data_start = True
            continue

        # data_start = True
        if mode != 'lircd.conf':
            # mode2コマンドの出力形式
            #    pulse 600
            #    space 500
            #     :
            [key, us] = data
            us = int(us)
            if key == 'pulse':
                raw_data.append([us])
            else:
                raw_data[-1].append(us)
        else:
            # lircd.conf形式
            #    name btn
            # 500 400 500 400 ..
            #  :
            if len(data) == 0:
                continue
            if not data[0].isdigit():
                # data end
                break

            for us in data:
                if not us.isdigit():
                    print('! Error: Invalid data:', data)
                    return None

                us = int(us)
                if key == 'pulse':
                    raw_data.append([us])
                    key = 'sleep'
                else:
                    raw_data[-1].append(us)
                    key = 'pulse'
            continue

        # オシロ風？出力
        if mode == 'exec.mode2':
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

    if mode == 'exec.mode2':
        print(file=sys.stderr)
        
    f.close()
    if mode == 'exec.mode2':
        f.join()

    if not data_start:
        return None

    if len(raw_data[-1]) == 1:
        raw_data[-1].append(SIG_LONG)

    print('# [pulse, space] * %d' % len(raw_data))
    return raw_data

#
# データ解析
#
def analyze_data(raw_data):
    #
    # 真のパルス・スリープ時間を t_p, t_s、誤差 td としたとき、
    # 一組のパルスとスリープの和は、ほぼ正確と仮定
    #
    # raw_data[pulse] + raw_data[sleep] = t_p + t_s
    # raw_data[pulse] = t_p + td
    # raw_data[sleep] = t_s - td
    # 
    # 
    
    # pulse + sleep の値のリスト
    sum_list = []
    for d1, d2 in raw_data:
        sum_list.append(d1 + d2)
    #print('sum_list =', sum_list)

    # sum_listの度数分布
    step = 0.2
    fq_list = [[]]
    for val in sorted(sum_list):
        if len(fq_list[-1]) > 0:
            if step < 1:
                next_step = fq_list[-1][-1] * (1 + step)
            else:
                next_step = fq_list[-1][-1] + step
            if fq_list[-1][-1] < SIG_LONG and val > next_step:
                fq_list.append([])
        fq_list[-1].append(val)
    #print('fq_list =', fq_list)

    # 単位時間: 一番小さいグループの平均の半分
    T1 = (sum(fq_list[0]) / len(fq_list[0])) / 2
    print('# T1 = %.2f' % T1)

    # pulse + sleep = 2 * T1 の組を抽出して、
    # 誤差 td を求める
    n_list = [t / T1  for t in sum_list]
    #print('n_list =', n_list)

    t1 = {'pulse': [], 'space': []}
    for i, s in  enumerate(n_list):
        if round(s) == 2:
            t1['pulse'].append(raw_data[i][0])
            t1['space'].append(raw_data[i][1])
    #print(t1)
    for key in ['pulse', 'space']:
        t_ave = sum(t1[key]) / len(t1[key])
        print('# t1[%s] = %.2f' % (key, t_ave))
    td = abs(t_ave - T1)
    print('# td = %.2f' % td)

    # raw_dataの値が、T1の何倍か求める
    n_list_float = []  # 不要？ (検証用)
    n_list = []
    for p, s in raw_data:
        n_p = (p - td) / T1
        n_s = (s + td) / T1
        n_list_float.append([n_p, n_s])
        '''
        # 有効桁数1桁
        fmt = '{:.1g}'
        n_p = round(float(fmt.format(n_p)))
        n_s = round(float(fmt.format(n_s)))
        '''
        n_p = round(n_p)
        n_s = round(n_s)
        n_list.append([n_p, n_s])
    #print('n_list_float =', n_list_float)
    #print('n_list =', n_list)

    # 信号パターン抽出
    n_pattern = sorted(list(map(list, set(map(tuple, n_list)))))
    #print('# n_pattern =', n_pattern)

    # 信号パターンの解析、
    # 信号フォーマットの特定
    sig_format = []
    sig_format2 = []
    sig2n = {'leader':[], 'zero':[], 'one':[], 'trailer':[], 'repeat':[], 'misc':[]}
    for n1, n2 in n_pattern:
        p = [n1, n2]
        if p == [4, 1]:
            sig2n['leader'].append(p)
            sig_format.append('SONY')
            continue
        if n1 in [7, 8, 9] and n2 in [3, 4, 5]:
            sig2n['leader'].append(p)
            sig_format.append('AEHA')
            continue
        if n1 in [15, 16, 17] and n2 in [7, 8, 9]:
            sig2n['leader'].append(p)
            sig_format.append('NEC')
            continue
        if p == [1, 1]:
            sig2n['zero'].append(p)
            continue
        if p == [2, 1]:
            sig2n['one'].append(p)
            sig_format.append('SONY')
            continue
        if n1 == 1 and n2 in [3, 4]:
            sig2n['one'].append(p)
            sig_format2.append('NEC?')
            sig_format2.append('AEHA?')
            continue
        if n1 in [15, 16, 17] and n2 in [3, 4, 5]:
            sig2n['repeat'].append(p)
            sig_format.append('NEC')
            continue
        if n1 in [7, 8, 9] and n2 in [7, 8, 9]:
            sig2n['repeat'].append(p)
            sig_format.append('AEHA')
            continue
        if n1 == 2 and n2 > 10:
            sig2n['trailer'].append(p)
            sig_format2.append('SONY?')
            continue
        if n1 == 1 and n2 > 10:
            sig2n['trailer'].append(p)
            continue
        if n1 == n_list[0][0] and n2 == n_list[0][1]:
            sig2n['leader'].append(p)
            continue
        if len(sig2n['one']) == 0 and ((n1 == 1 and n2 > 1) or (n1 > 1 and n2 == 1)):
            sig2n['one'].append(p)
            continue
        sig2n['misc'].append(p)

    for key in ['leader', 'zero', 'one', 'trailer', 'repeat', 'misc']:
        print('# %-8s: %s' % (key, str(sig2n[key])))

    print('# Signal Format: ', end='')
    if len(sig_format) > 0:
        sig_format = list(set(sig_format))
        for f in sig_format:
            print(f + ' ', end='', force_out=True)
    elif len(sig_format2) > 0:
        sig_format2 = list(set(sig_format2))
        for f in sig_format2:
            print(f + ' ', end='', force_out=True)
    else:
        print('??? ', end='', force_out=True)
    print(force_out=True)

    # 信号のリストを生成
    sig_list = []
    for n1, n2 in n_list:
        for key in sig2n.keys():
            if [n1, n2] in sig2n[key]:
                sig_list.append(key)
    #print('sig_list =', sig_list)

    return sig_list

#
# print_sig
#
def mk_sig_line(sig_list, raw_data):
    sig_line_usec = [0]
    sig_str = ''
    for i, sig in enumerate(sig_list):
        if sig == 'leader':
            sig_str += ' '
        sig_str += SIG_CH[sig]
        sig_line_usec[-1] += raw_data[i][0] + raw_data[i][0]
        if sig == 'trailer':
            sig_str += ' '
            sig_line_usec.append(0)
    if sig_line_usec[-1] == 0:
        sig_line_usec.pop(-1)
    #print(sig_str)

    sig_line = sig_str.split()
    #print(len(sig_line), sig_line)
    #print(len(sig_line_usec), sig_line_usec)

    sig_line2 = []
    for i, l1 in enumerate(sig_line):
        l2 = l1.replace('-', '- ')
        l3 = l2.replace('/', ' /')
        sig_line2.append([l3.split(), sig_line_usec[i]])

    return sig_line2    

#
# 文字列<s>を<n>文字毎に分割
#
def split_str(s, n):
    s1 = ' '
    for i in range(0, len(s), n):
        s1 += s[i:i+n] + ' '
    s = s1.strip()
    return s
    
#
#
#
def print_sig(sig_line):
    print('# MSB first')
    print_bit_pattern(sig_line, '# bit pattern', '## BIT:MSB ')
    print_hex_data(sig_line, '# Hex data', '## HEX:MSB ')
    if HexOnly or BitOnly:
        return
    
    print()
    print('# LSB first')
    print_bit_pattern(sig_line, '# bit pattern', '## BIT:LSB ', lsb_first=True)
    print_hex_data(sig_line, '# Hex data', '## HEX:LSB ', lsb_first=True)
    return

#
#
#
def print_bit_pattern(sig_line, title='', prefix='', lsb_first=False):
    global BitOnly
    
    if len(title) > 0:
        print(title)

    f1 = False
    f2 = False
    for sl in sig_line:
        print(prefix, end='')
        for s in sl[0]:
            if s[0] in SIG_STR_01:
                if lsb_first:
                    s = s[::-1]
                s = split_str(s[::-1], 4)
                s = s[::-1]
                if BitOnly:
                    f1 = True
                    f2 = True
            print('%s ' % s, end='', force_out=f1)
            f1 = False
        print(force_out=f2)
        f2 = False
    return

#
#
#
def print_hex_data(sig_line, title='', prefix='', lsb_first=False):
    global HexOnly
    
    if len(title) > 0:
        print(title)

    f1 = False
    f2 = False
    for sl in sig_line:
        print(prefix, end='')
        for s in sl[0]:
            if s[0] in SIG_STR_01:
                if lsb_first:
                    s = s[::-1]
                hex_len = int((len(s) - 1) / 4) + 1
                s = ('0' * hex_len + '%X' % int(s, 2))[-hex_len:]
                s = split_str(s[::-1], 2)
                s = s[::-1]
                if HexOnly:
                    f1 = True
                    f2 = True
            print('%s ' % s, end='', force_out=f1)
            f1 = False
        print(force_out=f2)
        f2 = False
    return

#
# main
#
@click.command(help='LIRC analyzer')
@click.argument('infile', default='', type=click.Path())
@click.argument('button_name', default='')
@click.option('--forever', '-f', is_flag=True, default=False, help='loop forever')
@click.option('--bitonly', '-b', is_flag=True, default=False,
              help='output bit pattern only')
@click.option('--hexonly', '-h', is_flag=True, default=False,
              help='output hex data only')
def main(infile, button_name, forever, bitonly, hexonly):
    global BitOnly
    global HexOnly

    BitOnly = bitonly
    HexOnly = hexonly
    
    if infile == '':
        mode = 'exec.mode2'
    elif button_name == '':
        mode = 'mode2.out'
    else:
        mode = 'lircd.conf'
    print('# Mode: %s' % mode)

    raw_data = load_input(mode, infile, button_name, forever)
    #print(raw_data)
    while raw_data:
        sig_list = analyze_data(raw_data)
        print()
        sig_line = mk_sig_line(sig_list, raw_data)
        print_sig(sig_line)
        
        raw_data = None
        if mode == 'exec.mode2':
            raw_data = load_input(mode, infile, button_name, forever)

if __name__ == '__main__':
    main()
