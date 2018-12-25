#!/usr/bin/python3 -u
#
# (c) 2018 Yoichi Tanibayashi
#
# !!! IMPORTANT !!!
#	-u option for python command is required
#
import sys
import click
import builtins

import CmdOut

SIG_LONG	= 9999999 # usec

SIG_CH		= {
    'leader':	'-',
    'zero':	'0',
    'one':	'1',
    'trailer':	'/',
    'repeat':	'*',
    'misc':	'?'	}
SIG_STR_01	= SIG_CH['zero'] + SIG_CH['one']

DispFlag	= {
    'info': 	False,
    'hex':	False,
    'bit':	False,
    'raw':	False,
    'norm':	False	}

#####
#
# print()関数のラッパー
#
def print(*args, sep=' ', end='\n', file=None, force=False, disp='info'):
    global DispFlag

    if disp == '' or force or DispFlag[disp] or file == sys.stderr:
        builtins.print(*args, sep=sep, end=end, file=file)
    return

#
# 文字列<s>を<n>文字毎に分割
#
def split_str(s, n):
    s1 = ' '
    for i in range(0, len(s), n):
        s1 += s[i:i+n] + ' '
    s = s1.strip()
    return s
    
#####
#
# Signal Data Class
#
class SigData:
    #
    # load and initialize
    #
    def __init__(self, mode, infile='', btn='', forever=False):
        self.sig_line = None

        self.raw_data = []

        if mode == 'exec.mode2':
            f = CmdOut.CmdOut(['mode2'])
            f.start()
        else:
            if infile == '':
                print('Error: infile=\'\'', file=sys.stderr)
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
                tm_out = 0.7
                if forever:
                    tm_out = 0.3
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
                    self.raw_data.append([us])
                else:
                    self.raw_data[-1].append(us)
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
                        self.raw_data.append([us])
                        key = 'sleep'
                    else:
                        self.raw_data[-1].append(us)
                        key = 'pulse'
                continue

            # オシロ風？出力
            if mode == 'exec.mode2' and DispFlag['info']:
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

        if len(self.raw_data[-1]) == 1:
            self.raw_data[-1].append(SIG_LONG)

        print('# [pulse, space] * %d' % len(self.raw_data))

    #
    # analyze data
    #
    def analyze(self):
        if not self.raw_data:
            return
        
        #
        # 真のパルス+スリープ時間を t_p, t_s、誤差 td としたとき、
        # 一組のパルスとスリープの和は、ほぼ正確と仮定
        #
        # raw_data[pulse] + raw_data[sleep] = t_p + t_s
        # raw_data[pulse] = t_p + td
        # raw_data[sleep] = t_s - td
        # 

        # pulse + sleep の値のリスト
        self.sum_list = []
        for d1, d2 in self.raw_data:
            self.sum_list.append(d1 + d2)
        #print('self.sum_list =', self.sum_list)

        # self.sum_listの度数分布
        step = 0.2
        self.fq_list = [[]]
        for val in sorted(self.sum_list):
            if len(self.fq_list[-1]) > 0:
                if step < 1:
                    next_step = self.fq_list[-1][-1] * (1 + step)
                else:
                    next_step = self.fq_list[-1][-1] + step
                if self.fq_list[-1][-1] < SIG_LONG and val > next_step:
                    self.fq_list.append([])
            self.fq_list[-1].append(val)
        #print('self.fq_list =', self.fq_list)

        # 単位時間: 一番小さいグループの平均の半分
        self.T1 = (sum(self.fq_list[0]) / len(self.fq_list[0])) / 2
        print('# T1 = %.2f' % self.T1)

        # pulse + sleep = 2 * self.T1 の組を抽出して、
        # 誤差 td を求める
        self.sum_n_list = [t / self.T1  for t in self.sum_list]
        #print('self.sum_n_list =', self.sum_n_list)

        t1 = {'pulse': [], 'space': []}
        for i, s in  enumerate(self.sum_n_list):
            if round(s) == 2:
                t1['pulse'].append(self.raw_data[i][0])
                t1['space'].append(self.raw_data[i][1])
        #print(t1)
        for key in ['pulse', 'space']:
            t_ave = sum(t1[key]) / len(t1[key])
            print('# t1[%s] = %.2f' % (key, t_ave))
        self.td = abs(t_ave - self.T1)
        print('# td = %.2f' % self.td)

        # self.raw_dataの値が、self.T1の何倍か求める
        self.n_list_float = []  # 不要？ (検証用)
        self.n_list = []
        for p, s in self.raw_data:
            n_p = (p - self.td) / self.T1
            n_s = (s + self.td) / self.T1
            self.n_list_float.append([n_p, n_s])
            '''
            # 有効桁数1桁
            fmt = '{:.1g}'
            n_p = round(float(fmt.format(n_p)))
            n_s = round(float(fmt.format(n_s)))
            '''
            n_p = round(n_p)
            n_s = round(n_s)
            self.n_list.append([n_p, n_s])
        #print('self.n_list_float =', self.n_list_float)
        #print('self.n_list =', self.n_list)

        # 信号パターン抽出
        self.n_pattern = sorted(list(map(list, set(map(tuple, self.n_list)))))
        #print('# n_pattern =', self.n_pattern)

        # 信号パターンの解析、
        # 信号フォーマットの特定
        self.sig_format = []
        self.sig_format2 = []
        self.sig2n = {'leader':[],
                 'zero':[], 'one':[], 'trailer':[], 'repeat':[],
                 'misc':[]}
        for n1, n2 in self.n_pattern:
            p = [n1, n2]
            if p == [4, 1]:
                self.sig2n['leader'].append(p)
                self.sig_format.append('SONY')
                continue
            if n1 in [7, 8, 9] and n2 in [3, 4, 5]:
                self.sig2n['leader'].append(p)
                self.sig_format.append('AEHA')
                continue
            if n1 in [15, 16, 17] and n2 in [7, 8, 9]:
                self.sig2n['leader'].append(p)
                self.sig_format.append('NEC')
                continue
            if p == [1, 1]:
                self.sig2n['zero'].append(p)
                continue
            if p == [2, 1]:
                self.sig2n['one'].append(p)
                self.sig_format.append('SONY')
                continue
            if n1 == 1 and n2 in [3, 4]:
                self.sig2n['one'].append(p)
                self.sig_format2.append('NEC?')
                self.sig_format2.append('AEHA?')
                continue
            if n1 in [15, 16, 17] and n2 in [3, 4, 5]:
                self.sig2n['repeat'].append(p)
                self.sig_format.append('NEC')
                continue
            if n1 in [7, 8, 9] and n2 in [7, 8, 9]:
                self.sig2n['repeat'].append(p)
                self.sig_format.append('AEHA')
                continue
            if n1 == 2 and n2 > 10:
                self.sig2n['trailer'].append(p)
                self.sig_format2.append('SONY?')
                continue
            if n1 == 1 and n2 > 10:
                self.sig2n['trailer'].append(p)
                continue
            if n1 == self.n_list[0][0] and n2 == self.n_list[0][1]:
                self.sig2n['leader'].append(p)
                continue
            if len(self.sig2n['one']) == 0 and \
               ((n1 == 1 and n2 > 1) or (n1 > 1 and n2 == 1)):
                self.sig2n['one'].append(p)
                continue
            self.sig2n['misc'].append(p)

        if DispFlag['hex'] or DispFlag['bit']:
            print('# Signal Format: ', end='')
            if len(self.sig_format) > 0:
                self.sig_format = list(set(self.sig_format))
                for f in self.sig_format:
                    print(f + ' ', end='', force=True)
            elif len(self.sig_format2) > 0:
                self.sig_format2 = list(set(self.sig_format2))
                for f in self.sig_format2:
                    print(f + ' ', end='', force=True)
            else:
                print('??? ', end='', force=True)
            print(force=True)

        for key in ['leader', 'zero', 'one', 'trailer', 'repeat', 'misc']:
            print('## %-8s: %s' % (key, str(self.sig2n[key])))

        # 信号パターンのリストを生成
        self.sig_list = []
        for n1, n2 in self.n_list:
            for key in self.sig2n.keys():
                if [n1, n2] in self.sig2n[key]:
                    self.sig_list.append(key)
        #print('self.sig_list =', self.sig_list)

        # 信号の文字列<sig_str>を生成
        # 信号列毎の時間<sig_line_usec>も算出
        self.sig_str = ''
        self.sig_line_usec = []
        for i, sig in enumerate(self.sig_list):
            if sig == 'leader':
                self.sig_str += ' '
                self.sig_line_usec.append(0)
            self.sig_str += SIG_CH[sig]
            if self.sig_line_usec == []:
                self.sig_line_usec = [0]
            self.sig_line_usec[-1] += self.raw_data[i][0] + self.raw_data[i][0]
        if self.sig_line_usec[-1] == 0:
            self.sig_line_usec.pop(-1)
        #print(self.sig_str, force=True)

        # leaderを区切りとして、信号の列を区切る
        self.sig_line1 = self.sig_str.split()
        #print(len(self.sig_line1), self.sig_line1, force=True)
        #print(len(self.sig_line_usec), self.sig_line_usec, force=True)

        # 信号の列の中をさらに分割
        # 0,1の部分は分割しない
        self.sig_line = []
        for i, l1 in enumerate(self.sig_line1):
            #print(l1, force=True)
            for key in SIG_CH.keys():
                if SIG_CH[key] in SIG_STR_01:
                    continue
                l1 = l1.replace(SIG_CH[key], ' ' + SIG_CH[key] + ' ')
                #print('"%s"' % l1, force=True)
            self.sig_line.append([l1.split(), self.sig_line_usec[i]])

        #print(self.sig_line, force=True)

        return
    
    #
    #
    #
    def disp_sig(self):
        if not self.sig_line:
            return
        
        print('# MSB first')
        self.disp_bit('# bit pattern', '## BIT:MSB ')
        self.disp_hex('# Hex data',    '## HEX:MSB ')
        if DispFlag['info']:
            print()
            print('# LSB first')
            self.disp_bit('# bit pattern', '## BIT:LSB ', lsb_first=True)
            self.disp_hex('# Hex data',    '## HEX:LSB ', lsb_first=True)
        return

    #
    #
    #
    def disp_bit(self, title='', prefix='', lsb_first=False):
        global BitOnly

        if len(title) > 0:
            print(title)

        d = ['info', 'info']
        for sl in self.sig_line:
            print(prefix, end='')
            for s in sl[0]:
                if s[0] in SIG_STR_01:
                    if lsb_first:
                        s = s[::-1]
                    s = split_str(s[::-1], 4)
                    s = s[::-1]

                    if not DispFlag['info'] and d[1] != 'bit':
                        print(prefix, end='', disp='bit')
                    d = ['bit', 'bit']
                print('%s ' % s, end='', disp=d[0])
                d[0] = 'info'
            print(disp=d[1])
            d[1] = 'info'
        return

    #
    # display hex data
    #
    def disp_hex(self, title='', prefix='', lsb_first=False):
        global DispFlag

        if len(title) > 0:
            print(title)

        d = ['info', 'info']
        for sl in self.sig_line:
            print(prefix, end='')
            for s in sl[0]:
                if s[0] in SIG_STR_01:
                    if lsb_first:
                        s = s[::-1]
                    hex_len = int((len(s) - 1) / 4) + 1
                    s = ('0' * hex_len + '%X' % int(s, 2))[-hex_len:]
                    s = split_str(s[::-1], 2)
                    s = s[::-1]
                    
                    if not DispFlag['info'] and d[1] != 'hex':
                        print(prefix, end='', disp='hex')
                    d = ['hex', 'hex']
                print('%s ' % s, end='', disp=d[0])
                d[0] = 'info'
            print(disp=d[1])
            d[1] = 'info'
        return

    #
    # display raw data
    #
    def disp_raw(self):
        if len(self.raw_data) == 0:
            return
        print('# raw data', disp='raw')
        print('\tname\traw_data', disp='raw')
        sig_str = self.sig_str.replace(' ', '')
        n = 0
        for i, ch in enumerate(sig_str):
            n += 1
            tp = self.raw_data[i][0]
            ts = self.raw_data[i][1]
            print('%5d %5d ' % (tp, ts), end='', disp='raw')
            if ch not in SIG_STR_01 or n % 4 == 0:
                print(disp='raw')
                n = 0
        if n > 0:
            print(disp='raw')
        return

    #
    #
    #
    def disp_norm(self):
        if len(self.raw_data) == 0:
            return
        print('# normalized data', disp='norm')
        print('\tname\tnormalized_data', disp='norm')
        sig_str = self.sig_str.replace(' ', '')
        n = 0
        for i, ch in enumerate(sig_str):
            n += 1
            tp = self.n_list[i][0] * self.T1
            ts = self.n_list[i][1] * self.T1
            print('%5d %5d ' % (tp, ts), end='', disp='norm')
            if ch not in SIG_STR_01 or n % 4 == 0:
                print(disp='norm')
                n = 0
        if n > 0:
            print(disp='norm')
        return
    
####
#
# main
#
@click.command(help='LIRC analyzer')
@click.argument('infile', default='', type=click.Path())
@click.argument('button_name', default='')
@click.option('--forever', '-f', is_flag=True, default=False, help='loop forever')
@click.option('--disp_info', '-i', '-l', is_flag=True, default=False,
              help='output information')
@click.option('--disp_hex', '-h', is_flag=True, default=False,
              help='output hex data')
@click.option('--disp_bit', '-b', is_flag=True, default=False,
              help='output bit pattern')
@click.option('--disp_raw', '-r', is_flag=True, default=False,
              help='output raw data')
@click.option('--disp_normalize', '-n', is_flag=True, default=False,
              help='output normalized data')
def main(infile, button_name, forever,
         disp_info, disp_hex, disp_bit, disp_raw, disp_normalize):
    global DispFlag

    DispFlag = {
        'info':	disp_info,
        'hex':	disp_hex,
        'bit':	disp_bit,
        'raw':	disp_raw,
        'norm':	disp_normalize }

    if list(DispFlag.values()) == [False, False, False, False, False]:
        DispFlag['info'] = True
            
    if DispFlag['info']:
        DispFlag['hex'] = True
        DispFlag['bit'] = True
    
    if infile == '':
        mode = 'exec.mode2'
    elif button_name == '':
        mode = 'mode2.out'
    else:
        mode = 'lircd.conf'
    print('# Mode: %s' % mode)

    while True:
        sig_data = SigData(mode, infile, button_name, forever)
        if len(sig_data.raw_data) == 0:
            break
        
        sig_data.analyze()
        if DispFlag['hex'] or DispFlag['bit']:
            print()
            sig_data.disp_sig()
        if DispFlag['raw']:
            print(disp='raw')
            sig_data.disp_raw()
        if DispFlag['norm']:
            print(disp='norm')
            sig_data.disp_norm()
        
        if mode != 'exec.mode2':
            break

if __name__ == '__main__':
    main()
