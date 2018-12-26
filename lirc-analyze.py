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

#####
#
# Signal Data Class
#
class SigData:
    DEF_TIMEOUT		= 1.0
    DEF_TIMEOUT_FOREVER = 0.3
    
    SIG_LONG	= 999999 # usec

    SIG_CH		= {
        'leader':	'-',
        'zero':		'0',
        'one':		'1',
        'trailer':	'/',
        'repeat':	'*',
        'misc':		'?'	}
    SIG_STR_01	= SIG_CH['zero'] + SIG_CH['one']

    #
    # load and initialize
    #
    def __init__(self):
        self.disp_flag = {
            'info':	True,
            'hex':	False,
            'bit':	False,
            'raw':	False,
            'norm':	False,
            'lsb':	False	}

        self.sig_line = None
        self.raw_data = []
        self.timeout = 0

    #
    #
    #
    def set_timeout(self, sec):
        self.timeout = sec
        
    #
    #
    #
    def true_count_of_disp_flags(self):
        return list(self.disp_flag.values()).count(True)
        
    #
    # print()関数のラッパー
    #
    def print(self, *args, sep=' ', end='\n', file=None, force=False,
              disp='info'):
        if disp == '' or force or self.disp_flag[disp] or file == sys.stderr:
            builtins.print(*args, sep=sep, end=end, file=file)
        return

    #
    # 文字列を<n>文字毎に分割
    #
    def split_str(self, s, n):
        s1 = ' '
        for i in range(0, len(s), n):
            s1 += s[i:i+n] + ' '
        s = s1.strip()
        return s

    #
    # データ読み込み
    #
    def load_data(self, mode, infile='', btn='', forever=False):
        self.sig_line = None
        self.raw_data = []

        if mode == 'exec.mode2':
            f = CmdOut.CmdOut(['mode2'])
            f.start()
        else:
            if infile == '':
                self.print('Error: infile=\'\'', file=sys.stderr)
                return None
            try:
                f = open(infile)
            except:
                self.print('Error: open(%s)' % infile, file=sys.stderr)
                return None

        data_start = False
        wait_count = 5
        while True:
            if mode == 'exec.mode2':
                tm_out = SigData.DEF_TIMEOUT
                if self.timeout > 0:
                    tm_out = self.timeout
                elif forever:
                    tm_out = SigData.DEF_TIMEOUT_FOREVER
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
                        self.print('%d..' % wait_count, end='', file=sys.stderr)
                        sys.stderr.flush()
                    continue
                else:
                    self.print('END', file=sys.stderr)
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
                        self.print('! Error: Invalid data:', data)
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
            if mode == 'exec.mode2' and self.disp_flag['info']:
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
                        self.print(ch, end='', file=sys.stderr)
                        sys.stderr.flush()
                except BrokenPipeError:
                    break

        if mode == 'exec.mode2':
            self.print(file=sys.stderr)

        f.close()
        if mode == 'exec.mode2':
            f.join()

        if not data_start:
            return None

        if len(self.raw_data[-1]) == 1:
            self.raw_data[-1].append(SigData.SIG_LONG)

        return

    #
    # analyze data
    #
    def analyze(self):
        if not self.raw_data:
            return
        
        # 真のパルス+スリープ時間を t_p, t_s、誤差 td としたとき、
        # 一組のパルスとスリープの和は、ほぼ正確と仮定
        #
        # raw_data[pulse] + raw_data[sleep] = t_p + t_s
        # raw_data[pulse] = t_p + td
        # raw_data[sleep] = t_s - td

        # pulse + sleep の値のリスト
        #
        self.sum_list = []
        for d1, d2 in self.raw_data:
            self.sum_list.append(d1 + d2)

        # self.sum_listの度数分布
        step = 0.2
        self.fq_list = [[]]
        for val in sorted(self.sum_list):
            if len(self.fq_list[-1]) > 0:
                if step < 1:
                    next_step = self.fq_list[-1][-1] * (1 + step)
                else:
                    next_step = self.fq_list[-1][-1] + step
                if self.fq_list[-1][-1] < SigData.SIG_LONG and val > next_step:
                    self.fq_list.append([])
            self.fq_list[-1].append(val)

        # 単位時間: 一番小さいグループの平均の半分
        self.T = (sum(self.fq_list[0]) / len(self.fq_list[0])) / 2

        # pulse + sleep = 2 * self.T の組を抽出して、誤差 td を求める
        self.sum_n_list = [t / self.T  for t in self.sum_list]

        self.T1 = {'pulse': [], 'space': []}
        for i, s in  enumerate(self.sum_n_list):
            if round(s) == 2:
                self.T1['pulse'].append(self.raw_data[i][0])
                self.T1['space'].append(self.raw_data[i][1])
        self.T1_ave = {}
        for key in ['pulse', 'space']:
            self.T1_ave[key] = sum(self.T1[key]) / len(self.T1[key])
        self.Td = abs(self.T1_ave['pulse'] - self.T)

        # self.raw_dataの値が、self.Tの何倍か求める
        #
        self.n_list_float = []  # 不要？ (検証用)
        self.n_list = []
        for p, s in self.raw_data:
            n_p = (p - self.Td) / self.T
            n_s = (s + self.Td) / self.T
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

        # 信号パターン抽出
        self.n_pattern = sorted(list(map(list, set(map(tuple, self.n_list)))))

        # 信号パターンの解析
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

        # 信号フォーマットのリスト<sig_format>から、
        # 文字列<sig_format_str>を生成
        self.sig_format_str = ''
        if len(self.sig_format) > 0:
            self.sig_format = list(set(self.sig_format))
            for f in self.sig_format:
                self.sig_format_str += f + ' '
        elif len(self.sig_format2) > 0:
            self.sig_format2 = list(set(self.sig_format2))
            for f in self.sig_format2:
                self.sig_format_str += f + ' '
        else:
            self.sig_format_str = '??? '

        # 信号パターンのリストを生成
        self.sig_list = []
        for n1, n2 in self.n_list:
            for key in self.sig2n.keys():
                if [n1, n2] in self.sig2n[key]:
                    self.sig_list.append(key)
        #self.print('self.sig_list =', self.sig_list)

        # 信号の文字列<sig_str>を生成
        # 信号列毎の時間<sig_line_usec>も算出
        self.sig_str = ''
        self.sig_line_usec = []
        for i, sig in enumerate(self.sig_list):
            if sig == 'leader':
                self.sig_str += ' '
                self.sig_line_usec.append(0)
            self.sig_str += SigData.SIG_CH[sig]
            if self.sig_line_usec == []:
                self.sig_line_usec = [0]
            self.sig_line_usec[-1] += self.raw_data[i][0] + self.raw_data[i][0]
        if self.sig_line_usec[-1] == 0:
            self.sig_line_usec.pop(-1)
        #self.print(self.sig_str, force=True)

        # leaderを区切りとして、信号の列を区切る
        self.sig_line1 = self.sig_str.split()
        #self.print(len(self.sig_line1), self.sig_line1, force=True)
        #self.print(len(self.sig_line_usec), self.sig_line_usec, force=True)

        # 信号の列の中をさらに分割
        # 0,1の部分は分割しない
        self.sig_line = []
        for i, l1 in enumerate(self.sig_line1):
            #self.print(l1, force=True)
            for key in SigData.SIG_CH.keys():
                if SigData.SIG_CH[key] in SigData.SIG_STR_01:
                    continue
                l1 = l1.replace(SigData.SIG_CH[key],
                                ' ' + SigData.SIG_CH[key] + ' ')
                #self.print('"%s"' % l1, force=True)
            self.sig_line.append([l1.split(), self.sig_line_usec[i]])

        #self.print(self.sig_line, force=True)
        return

    #
    #
    #
    def disp_info(self):
        if not self.sig_line:
            return

        self.print('# T = %.2f, Td = %.2f' % (self.T, self.Td))
        self.print('## T1_ave[pulse] = %.2f' % self.T1_ave['pulse'])
        self.print('## T1_ave[space] = %.2f' % self.T1_ave['space'])
        self.print('# Signal Format: %s' % self.sig_format_str)
        for key in ['leader', 'zero', 'one', 'trailer', 'repeat', 'misc']:
            self.print('## [%s] %-8s: %s' % (self.SIG_CH[key], key, str(self.sig2n[key])))
                       
        
        return
      
    #
    #
    #
    def disp_sig(self):
        if not self.sig_line:
            return
        
        self.print('# MSB first')
        self.disp_bit('# bit pattern', '## bit:MSB ')
        self.disp_hex('# Hex data',    '## hex:MSB ')
        if self.disp_flag['lsb']:
            self.print()
            self.print('# LSB first')
            self.disp_bit('# bit pattern', '## bit:LSB ', lsb_first=True)
            self.disp_hex('# Hex data',    '## hex:LSB ', lsb_first=True)
        return

    #
    #
    #
    def disp_bit(self, title='', prefix='', lsb_first=False):
        if len(title) > 0:
            self.print(title)

        d = ['info', 'info']
        for sl in self.sig_line:
            self.print(prefix, end='')
            for s in sl[0]:
                if s[0] in SigData.SIG_STR_01:
                    if lsb_first:
                        s = s[::-1]
                    s = self.split_str(s[::-1], 4)
                    s = s[::-1]

                    if not self.disp_flag['info'] and d[1] != 'bit':
                        self.print(prefix, end='', disp='bit')
                    d = ['bit', 'bit']
                self.print('%s ' % s, end='', disp=d[0])
                d[0] = 'info'
            self.print(disp=d[1])
            d[1] = 'info'
        return

    #
    # display hex data
    #
    def disp_hex(self, title='', prefix='', lsb_first=False):
        if len(title) > 0:
            self.print(title)

        d = ['info', 'info']
        for sl in self.sig_line:
            self.print(prefix, end='')
            for s in sl[0]:
                if s[0] in SigData.SIG_STR_01:
                    if lsb_first:
                        s = s[::-1]
                    hex_len = int((len(s) - 1) / 4) + 1
                    s = ('0' * hex_len + '%X' % int(s, 2))[-hex_len:]
                    s = self.split_str(s[::-1], 2)
                    s = s[::-1]
                    
                    if not self.disp_flag['info'] and d[1] != 'hex':
                        self.print(prefix, end='', disp='hex')
                    d = ['hex', 'hex']
                self.print('%s ' % s, end='', disp=d[0])
                d[0] = 'info'
            self.print(disp=d[1])
            d[1] = 'info'
        return

    #
    # display raw data
    #
    def disp_raw(self):
        if len(self.raw_data) == 0:
            return
        self.print('# raw data', disp='raw')
        self.print('\tname\tbutton', disp='raw')
        sig_str = self.sig_str.replace(' ', '')
        n = 0
        for i, ch in enumerate(sig_str):
            n += 1
            tp = self.raw_data[i][0]
            ts = self.raw_data[i][1]
            if i < len(sig_str) - 1:
                self.print('%5d %5d ' % (tp, ts), end='', disp='raw')
            else:
                self.print('%5d' % tp, end='', disp='raw')
            if ch not in SigData.SIG_STR_01 or n % 4 == 0:
                self.print(disp='raw')
                n = 0
        if n > 0:
            self.print(n, disp='raw')
        return

    #
    #
    #
    def disp_norm(self):
        if len(self.raw_data) == 0:
            return
        self.print('# normalized data', disp='norm')
        self.print('\tname\tbutton', disp='norm')
        sig_str = self.sig_str.replace(' ', '')
        n = 0
        for i, ch in enumerate(sig_str):
            n += 1
            tp = self.n_list[i][0] * self.T
            ts = self.n_list[i][1] * self.T
            if i < len(sig_str) -1:
                self.print('%5d %5d ' % (tp, ts), end='', disp='norm')
            else:
                self.print('%5d' % tp, end='', disp='norm')
            if ch not in SigData.SIG_STR_01 or n % 4 == 0:
                self.print(disp='norm')
                n = 0
        if n > 0:
            self.print(disp='norm')
        return
    
####
#
# main
#
@click.command(help='LIRC analyzer')
@click.argument('infile', default='', type=click.Path())
@click.argument('button_name', default='')
@click.option('--forever', '-f', is_flag=True, default=False, help='loop forever')
@click.option('--disp_info', '--info', '-i', '-l', is_flag=True, default=False,
              help='output information (default)')
@click.option('--disp_hex', '--hex', '-h', is_flag=True, default=False,
              help='output hex data (default)')
@click.option('--disp_bit', '--bit', '-b', is_flag=True, default=False,
              help='output bit pattern (default)')
@click.option('--disp_raw', '--raw', '-r', is_flag=True, default=False,
              help='output raw data')
@click.option('--disp_normalize', '--norm', '-n', is_flag=True, default=False,
              help='output normalized data')
@click.option('--disp_lsb', '--lsb', '-L', is_flag=True, default=False,
              help='output LSB first')
@click.option('--timeout', '-t', type=float, default=0,
              help='timeout (sec)')
def main(infile, button_name,
         forever,
         disp_info, disp_hex, disp_bit, disp_raw, disp_normalize, disp_lsb,
         timeout):

    sig_data = SigData()

    if timeout > 0:
        sig_data.set_timeout(timeout)
        
    sig_data.disp_flag = {
        'info':	disp_info,
        'hex':	disp_hex,
        'bit':	disp_bit,
        'raw':	disp_raw,
        'norm':	disp_normalize,
        'lsb':	disp_lsb }

    if sig_data.true_count_of_disp_flags() == 0:
        sig_data.disp_flag['info'] = True
        sig_data.disp_flag['hex'] = True
        sig_data.disp_flag['bit'] = True
    
    if infile == '':
        mode = 'exec.mode2'
    elif button_name == '':
        mode = 'mode2.out'
    else:
        mode = 'lircd.conf'
    sig_data.print('# Mode: %s' % mode)
    if mode == 'mode2.out' or mode == 'lircd.conf':
        sig_data.print('# File: %s' % infile)
    if mode == 'lircd.conf':
        sig_data.print('# Button: %s' % button_name)
    sig_data.print()

    while True:
        sig_data.load_data(mode, infile, button_name, forever)
        if len(sig_data.raw_data) == 0:
            break
        
        sig_data.analyze()
        sig_data.disp_info()
        if sig_data.disp_flag['hex'] or sig_data.disp_flag['bit']:
            sig_data.print()
            sig_data.disp_sig()
        if sig_data.disp_flag['raw']:
            sig_data.print(disp='raw')
            sig_data.disp_raw()
        if sig_data.disp_flag['norm']:
            sig_data.print(disp='norm')
            sig_data.disp_norm()
        
        if mode != 'exec.mode2':
            break

if __name__ == '__main__':
    main()
