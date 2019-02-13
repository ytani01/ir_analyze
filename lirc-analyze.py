#!/usr/bin/python3 -u
#
# (c) 2018 Yoichi Tanibayashi
#
import os, sys
import click
import builtins

import CmdOut
from OledClient import OledClient

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN
logger = getLogger(__name__)
logger.setLevel(DEBUG)
handler = StreamHandler()
handler.setLevel(DEBUG)
handler_fmt = Formatter('%(asctime)s %(levelname)s %(funcName)s> %(message)s',
                        datefmt='%H:%M:%S')
handler.setFormatter(handler_fmt)
logger.addHandler(handler)
logger.propagate = False

#####
oledFlag = False

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
        'leader?':	'=',
        'zero':		'0',
        'one':		'1',
        'trailer':	'/',
        'repeat':	'*',
        'unknown':	'?'	}
    SIG_STR_01	= SIG_CH['zero'] + SIG_CH['one']

    #
    # load and initialize
    #
    def __init__(self):
        self.disp_flag = {
            'all':	False,
            'info':	True,
            'hex':	False,
            'bit':	False,
            'raw':	False,
            'norm':	False,
            'lsb':	False	}

        self.raw_data = None
        self.timeout = 0

        self.sum_list = []
        self.fq_list =[]
        self.T = 0
        self.T1 = {'pulse': [], 'space': []}
        self.T1_ave = {'pulse':[], 'space':[]}
        self.Td = 0
        self.n_list = []
        self.n_list_float = []
        self.n_pattern = []
        self.sig_format = []
        self.sig_format2 = []
        self.sig_format_str = ''
        self.sig2n = {}
        self.sig_list = []
        self.sig_str = ''
        self.sig_line_usec = None
        self.sig_line1 = None
        self.sig_line = None

    #
    def set_timeout(self, sec):
        self.timeout = sec

    #
    def count_disp_flags(self, true_false):
        return list(self.disp_flag.values()).count(true_false)
        
    #
    # print()関数のラッパー
    #
    def print(self, *args, sep=' ', end='\n', file=None, force=False,
              disp=''):
        builtins.print(*args, sep=sep, end=end, file=file)
        if file == sys.stderr or file == sys.stdout:
            file.flush()
        return

    #
    # 文字列<s>の<n>文字毎にスペースを挿入
    #
    def split_str(self, s, n):
        s1 = ' '
        for i in range(0, len(s), n):
            s1 += s[i:i+n] + ' '
        s = s1.strip()
        return s

    #
    # データ読み込み
    #    <infile>,<btn>が無指定''の場合、mode2コマンドを起動し、その出力を取得
    #    <infile>が指定された場合、mode2コマンド出力形式のファイルを読み込み
    #    <infile>と<btn>が指定された場合、lircd.conf形式のファイルを読み込み
    #
    def load_data(self, mode, infile='', btn='', forever=False, oscillo=False):
        self.sig_line = None
        self.raw_data = []

        if mode == 'exec.mode2':
            f = CmdOut.CmdOut(['mode2'])
            f.start()
        else:
            if infile == '':
                self.print('Error: infile=\'\'', file=sys.stderr)
                return 0
            try:
                f = open(infile)
            except:
                self.print('Error: open(%s)' % infile, file=sys.stderr)
                return 0

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
                        self.print('%d..' % wait_count, end='',
                                   file=sys.stderr)
                    continue

                self.print('END', file=sys.stderr)
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
                        return 0

                    us = int(us)
                    if key == 'pulse':
                        self.raw_data.append([us])
                        key = 'sleep'
                    else:
                        self.raw_data[-1].append(us)
                        key = 'pulse'
                continue

            # オシロ風？出力
            if oscillo:
                try:
                    sig_len = int(us / 500)
                    if sig_len == 0:
                        sig_len = 1
                    if sig_len > 20:
                        sig_len = 20
                    for i in range(sig_len):
                        ch = '_'
                        if key == 'pulse':
                            ch = '-'
                        self.print(ch, end='', file=sys.stderr)
                except BrokenPipeError:
                    break

        if oscillo:
            self.print(file=sys.stderr)

        f.close()
        if mode == 'exec.mode2':
            f.join()

        if not data_start:
            return 0

        if len(self.raw_data) == 0:
            return 0
        
        if len(self.raw_data[-1]) == 1:
            self.raw_data[-1].append(SigData.SIG_LONG)

        return len(self.raw_data)

    # 度数分布作成
    def fq_dist(self, data, step=0.2):
        fq_list = [[]]
        for val in sorted(data):
            if len(fq_list[-1]) > 0:
                if step < 1:
                    # 比率
                    next_step = fq_list[-1][-1] * (1 + step)
                else:
                    # 差
                    next_step = fq_list[-1][-1] + step
                if val >= next_step:
                    fq_list.append([])
            fq_list[-1].append(val)
        return fq_list

    #
    # 信号フォーマット取得
    #
    # 事前にself.analyze()する必要がある
    #
    def get_sig_format(self):
        return self.sig_format_str
            
    #
    # analyze data
    #
    #    pulse, sleepの時間には、誤差があるが、
    #    一組のパルスとスリープの和は、ほぼ正確と仮定。
    #
    #    真のパルス+スリープ時間を t_p, t_s、誤差 tdとしたとき、
    #      raw_data[pulse] + raw_data[sleep] = t_p + t_s
    #      raw_data[pulse] = t_p + td
    #      raw_data[sleep] = t_s - td
    #
    def analyze(self):
        if not self.raw_data:
            return
        
        # pulse + sleep の値のリスト
        self.sum_list = [(d1 + d2) for d1, d2 in self.raw_data]

        # self.sum_listの度数分布
        self.fq_list = self.fq_dist(self.sum_list, 0.2)

        # 単位時間<T> = 度数分布で一番小さいグループの平均の半分
        self.T = (sum(self.fq_list[0]) / len(self.fq_list[0])) / 2

        # 誤差 td を求める
        self.T1 = {'pulse': [], 'space': []}
        for i, s in enumerate(self.sum_list):
            if self.sum_list[i] in self.fq_list[0]:
                self.T1['pulse'].append(self.raw_data[i][0])
                self.T1['space'].append(self.raw_data[i][1])
        self.T1_ave = {'pulse':[], 'space':[]}
        # (pulse,spaceのTdの平均値を求めているが… pulseだけでも十分)
        for key in ['pulse', 'space']:
            self.T1_ave[key] = sum(self.T1[key]) / len(self.T1[key])
        self.Td_p = abs(self.T1_ave['pulse'] - self.T)
        self.Td_s = abs(self.T1_ave['space'] - self.T)
        self.Td = (self.Td_p + self.Td_s) / 2

        # self.raw_dataのそれぞれの値(Tdで補正)が、self.Tの何倍か求める
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
        self.sig_format = []	# 確定
        self.sig_format2 = []	# 未確定(推定)
        self.sig2n = {'leader':	[],
                      'leader?':[],
                      'zero':	[],
 	              'one':	[],
                      'trailer':[],
	              'repeat':	[],
                      'unknown':	[] }
        for i, [n1, n2] in enumerate(self.n_pattern):
            p = [n1, n2]
            # leader
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
            if p == [3, 1]:
                self.sig2n['leader?'].append(p)
                self.sig_format2.append('Dyson?')
                continue
            # zero
            if p == [1, 1]:
                self.sig2n['zero'].append(p)
                continue
            # one
            if p == [2, 1]:
                self.sig2n['one'].append(p)
                self.sig_format.append('SONY')
                continue
            if p in [[1, 3], [1, 4]]:
                self.sig2n['one'].append(p)
                self.sig_format2.append('NEC?')
                self.sig_format2.append('AEHA?')
                continue
            # repeat
            if n1 in [15, 16, 17] and n2 in [3, 4, 5]:
                self.sig2n['repeat'].append(p)
                self.sig_format.append('NEC')
                continue
            if n1 in [7, 8, 9] and n2 in [7, 8, 9]:
                self.sig2n['repeat'].append(p)
                self.sig_format.append('AEHA')
                continue
            # trailer
            if n1 in [1, 2] and n2 > 10:
                self.sig2n['trailer'].append(p)
                if n1 == 2:
                    self.sig_format2.append('SONY?')
                continue
            # ???
            if len(self.sig2n['one']) == 0 and \
               ((n1 == 1 and n2 > 1) or (n1 > 1 and n2 == 1)):
                self.sig2n['one'].append(p)
                continue
            if n1 == self.n_list[0][0] and n2 == self.n_list[0][1]:
                self.sig2n['leader?'].append(p)
                continue
            # 判断できない
            self.sig2n['unknown'].append(p)

        # self.sig2nの['key']と['key?']の整理
        for key in self.sig2n.keys():
            if key[-1] == '?':
                continue
            if key + '?' in self.sig2n.keys():
                if len(self.sig2n[key]) == 0:
                    self.sig2n[key] = self.sig2n[key + '?'][:]
                for sig in self.sig2n[key]:
                    if sig in self.sig2n[key + '?']:
                        self.sig2n[key + '?'].remove(sig)

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
        self.sig_format_str = self.sig_format_str.strip()

        # 信号名リストを生成
        self.sig_list = []
        for n1, n2 in self.n_list:
            for key in self.sig2n.keys():
                if [n1, n2] in self.sig2n[key]:
                    self.sig_list.append(key)

        # 信号の文字列<sig_str>を生成
        # 信号列毎(leaderから)の時間<sig_line_usec>も算出(意味ない？)
        # (最後のtrailerのspace時間は、省く)
        # leader毎に' 'を挿入しておく
        self.sig_str = ''
        self.sig_line_usec = []
        for i, sig in enumerate(self.sig_list):
            if sig == 'leader' or sig == 'leader?':
                # 前の信号の時間から最後のspace時間を引く
                if len(self.sig_line_usec) > 0:
                    self.sig_line_usec[-1] -= self.raw_data[i-1][1]
                    
                self.sig_str += ' '
                self.sig_line_usec.append(0)

            self.sig_str += SigData.SIG_CH[sig]
            
            if self.sig_line_usec == []:
                self.sig_line_usec = [0]
                
            self.sig_line_usec[-1] += self.raw_data[i][0] + self.raw_data[i][1]

        if self.sig_line_usec[-1] == 0:
            self.sig_line_usec.pop(-1)
        # 最後のspace時間を引く
        self.sig_line_usec[-1] -= self.raw_data[-1][1]

        # leaderを区切りとして、信号文字列を区切る
        self.sig_line1 = self.sig_str.split()

        # 信号文字列の中をさらに分割
        # 0,1の部分は分割しない
        self.sig_line = []
        for i, l1 in enumerate(self.sig_line1):
            for key in SigData.SIG_CH.keys():
                if SigData.SIG_CH[key] in SigData.SIG_STR_01:
                    continue
                l1 = l1.replace(SigData.SIG_CH[key],
                                ' ' + SigData.SIG_CH[key] + ' ')
            self.sig_line.append([l1.split(), self.sig_line_usec[i]])

        ### XXX
        # エラーチェック
        # T.B.D.
        
        return

    #
    #
    #
    def disp_info(self):
        if not self.sig_line:
            return

        self.print('# T = %.2f' % self.T)
        self.print('## Td = %.2f' % self.Td)
        self.print('## T1_ave[pulse] = %.2f' % self.T1_ave['pulse'])
        self.print('## T1_ave[space] = %.2f' % self.T1_ave['space'])
        self.print('# Signal Format: %s' % self.sig_format_str)
        for key in ['leader', 'leader?',
                    'zero', 'one',
                    'trailer', 'repeat', 'unknown']:
            if len(self.sig2n[key]):
                self.print('## [%s] %-8s: %s' % (self.SIG_CH[key],
                                                 key,
                                                 str(self.sig2n[key])))
        return
          
    #
    #
    #
    def disp_bit(self, title='', prefix='', lsb_first=False):
        if len(title) > 0:
            self.print(title)

        for sl in self.sig_line:
            self.print(prefix, end='')
            for s in sl[0]:
                if s[0] in SigData.SIG_STR_01:
                    self.print('[%d] ' % len(s), end='')
                    # 4桁毎に区切る
                    if lsb_first:
                        s = s[::-1]
                    s = self.split_str(s[::-1], 4)
                    s = s[::-1]
                self.print('%s ' % s, end='')
            self.print('(%d usec)' % sl[1])
        return

    # bit pattern string to hex string
    def bit2hex(self, b, lsb_first=False):
        if b[0] not in SigData.SIG_STR_01:
            return b

        if lsb_first:
            b = b[::-1]
        hex_len = int((len(b) - 1) / 4) + 1
        h = ('0' * hex_len + '%X' % int(b, 2))[-hex_len:]
        h = self.split_str(h[::-1], 2)
        h = h[::-1]
        return h
        
    #
    # display hex data
    #
    def disp_hex(self, title='', prefix='', lsb_first=False):
        if len(title) > 0:
            self.print(title)

        for sl in self.sig_line:
            self.print(prefix, end='')
            for s in sl[0]:
                if s[0] in SigData.SIG_STR_01:
                    self.print('[%d] ' % len(s), end='')
                    if lsb_first:
                        s = s[::-1]
                    s = self.bit2hex(s)
                self.print('%s ' % s, end='')
            self.print('(%d usec)' % sl[1])
        return

    #
    # display raw data
    #
    def disp_raw(self):
        if len(self.raw_data) == 0:
            return
        self.print('# raw data')
        self.print('\tname\tbutton')
        sig_str = self.sig_str.replace(' ', '')
        n = 0
        for i, ch in enumerate(sig_str):
            n += 1
            tp = self.raw_data[i][0]
            ts = self.raw_data[i][1]
            if i < len(sig_str) - 1:
                self.print('%5d %5d ' % (tp, ts), end='')
            else:
                self.print('%5d' % tp, end='')
            if ch not in SigData.SIG_STR_01 or n % 4 == 0:
                self.print()
                n = 0
        if n > 0:
            self.print(n)
        return

    #
    # display normalized data
    #
    def disp_norm(self):
        if len(self.raw_data) == 0:
            return
        self.print('# normalized data')
        self.print('\tname\tbutton')
        sig_str = self.sig_str.replace(' ', '')
        n = 0
        for i, ch in enumerate(sig_str):
            n += 1
            tp = self.n_list[i][0] * self.T
            ts = self.n_list[i][1] * self.T
            if i < len(sig_str) -1:
                self.print('%5d %5d ' % (tp, ts), end='')
            else:
                self.print('%5d' % tp, end='')
            if ch not in SigData.SIG_STR_01 or n % 4 == 0:
                self.print()
                n = 0
        if n > 0:
            self.print()
        return

#
# output OLED display
#
def oled_out(sig_data, host='localhost', port=12345):
    out_str = ''

    for line in [l[0] for l in sig_data.sig_line]:
        for s in line:
            if s[0] in SigData.SIG_STR_01:
                s = sig_data.bit2hex(s)
            out_str += s
        out_str += '\n'

    with OledClient(host, port) as oc:
        oc.part('body')
        oc.crlf(True)
        oc.zenkaku(True)
        oc.send('<< %s >>' % sig_data.get_sig_format())
        #oc.zenkaku(False)
        oc.send('%s' % out_str.rstrip())

####
#
# main
#
@click.command(help='LIRC analyzer')
@click.argument('infile', default='', type=click.Path())
@click.argument('button_name', default='')
@click.option('--forever', '-f', 'forever', is_flag=True, default=False,
              help='loop forever')
@click.option('--disp_all', '--all', '-a', 'disp_all',
              is_flag=True, default=False, help='display all')
@click.option('--disp_info', '--info', '-i', 'disp_info',
              is_flag=True, default=False,
              help='display information (default)')
@click.option('--disp_hex', '--hex', '-h', 'disp_hex',
              is_flag=True, default=False, help='display hex data (default)')
@click.option('--disp_bit', '--bit', '-b', 'disp_bit',
              is_flag=True, default=False,
              help='display bit pattern (default)')
@click.option('--disp_raw', '--raw', '-r', 'disp_raw',
              is_flag=True, default=False, help='display raw data')
@click.option('--disp_normalize', '--norm', '-n', 'disp_normalize',
              is_flag=True, default=False, help='display normalized data')
@click.option('--disp_lsb', '--lsb', '-l', 'disp_lsb',
              is_flag=True, default=False, help='display LSB first')
@click.option('--oled', '-o', 'oled', is_flag=True, default=False,
              help='OLED output')
@click.option('--timeout', '-t', 'timeout', type=float, default=0,
              help='timeout (sec)')
def main(infile, button_name,
         forever,
         disp_all, disp_info,
         disp_hex, disp_bit, disp_raw, disp_normalize, disp_lsb,
         oled,
         timeout):
    global oledFlag

    oledFlag = oled

    sig_data = SigData()

    if timeout > 0:
        sig_data.set_timeout(timeout)
        
    sig_data.disp_flag = {
        'all':	disp_all,
        'info':	disp_info,
        'hex':	disp_hex,
        'bit':	disp_bit,
        'raw':	disp_raw,
        'norm':	disp_normalize,
        'lsb':	disp_lsb }

    if sig_data.disp_flag['all']:
        sig_data.disp_flag = {
            'all':	True,
            'info':	True,
            'hex':	True,
            'bit':	True,
            'raw':	True,
            'norm':	True,
            'lsb':	True	}
        
    if sig_data.count_disp_flags(True) == 0:
        sig_data.disp_flag['info'] = True
        sig_data.disp_flag['hex'] = True
        sig_data.disp_flag['bit'] = True
    
    if infile == '':
        mode = 'exec.mode2'
    elif button_name == '':
        mode = 'mode2.out'
    else:
        mode = 'lircd.conf'

    oscillo = False
    if sig_data.disp_flag['info']:
        oscillo = True
        sig_data.print('# Mode: %s' % mode)
        if mode == 'mode2.out' or mode == 'lircd.conf':
            sig_data.print('# File: %s' % infile)
        if mode == 'lircd.conf':
            sig_data.print('# Button: %s' % button_name)
        sig_data.print()

    if oled:
        with OledClient('localhost', 12345) as oc:
            oc.part('body')
            oc.crlf(True)
            oc.zenkaku(False)
            oc.send('== %s ==' % os.path.basename(__file__))
            oc.zenkaku(True)
            oc.send('Ready')
        

    while True:
        if sig_data.load_data(mode, infile, button_name,
                              forever, oscillo) == 0:
            # no data
            if forever:
                continue
            else:
                break
        
        sig_data.analyze()

        # OLED
        if oled:
            oled_out(sig_data, 'localhost', 12345)

        #
        if sig_data.disp_flag['info']:
            sig_data.disp_info()
            sig_data.print()
        else:
            sig_data.print('# Format: %s' % sig_data.get_sig_format())

        if sig_data.disp_flag['bit']:
            if sig_data.disp_flag['info']:
                sig_data.print('# bit pattern')

            sig_data.disp_bit('', '## bit:MSB ')
            sig_data.print()
            
            if sig_data.disp_flag['lsb']:
                sig_data.disp_bit('', '## bit:LSB ', True)
                sig_data.print()

        if sig_data.disp_flag['hex']:
            if sig_data.disp_flag['info']:
                sig_data.print('# Hex data')

            sig_data.disp_hex('', '## hex:MSB ')
            sig_data.print()

            if sig_data.disp_flag['lsb']:
                sig_data.disp_hex('', '## hex:LSB ', True)
                sig_data.print()

        if sig_data.disp_flag['raw']:
            sig_data.disp_raw()
            sig_data.print()

        if sig_data.disp_flag['norm']:
            sig_data.disp_norm()
            sig_data.print()
        
        if mode != 'exec.mode2':
            break

if __name__ == '__main__':
    try:
        main()
    finally:
        if oledFlag:
            with OledClient('localhost', 12345) as oc:
                oc.part('body')
                oc.crlf(True)
                oc.zenkaku(False)
                oc.send('-- %s:end --' % os.path.basename(__file__))
