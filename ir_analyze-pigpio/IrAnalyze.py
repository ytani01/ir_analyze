#!/usr/bin/python3 -u
#
# (c) 2019 Yoichi Tanibayashi
#
'''
IrAnalyze.py
'''
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'

import json

#####
from MyLogger import MyLogger
my_logger = MyLogger(__file__)

#####
class IrAnalyze:
    '''
    raw_data = [[pulse1, space1], [pulse2, space2], ... ]
    '''
    RAW_DATA_LEN_MIN = 6
    
    SIG_LONG =  99999 # usec
    SIG_END  = 999999 # usec

    SIG_CH		= {
        'leader':	'-',
        'leader?':	'=',
        'zero':		'0',
        'one':		'1',
        'trailer':	'/',
        'repeat':	'*',
        'unknown':	'?'	}
    SIG_STR_01	= SIG_CH['zero'] + SIG_CH['one']

    def __init__(self, raw_data=[], debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('raw_data=%s', raw_data)

        self.get_raw_data(raw_data)

        
    def get_raw_data(self, raw_data):
        self.logger.debug('raw_data=%s', raw_data)

        self.raw_data = raw_data
        if self.raw_data == []:
            return
        
        if len(self.raw_data[0]) == 1:
            self.raw_data[-1].append(self.SIG_END)
            self.logger.debug('raw_data=%s', raw_data)

        
    def split_str(self, s, n):
        '''
        文字列<s>の<n>文字毎にスペースを挿入
        '''
        self.logger.debug('s=%s, n=%d', s, n)

        if n <= 0:
            self.logger.warning('n=%d .. ignored', n)
            return s
        
        s1 = ' '
        for i in range(0, len(s), n):
            s1 += s[i:i+n] + ' '
        s = s1.strip()
        return s

    def fq_dist(self, data, step=0.2):
        '''
        度数分布作成
        '''
        self.logger.debug('data=%s, step=%.1f', data, step)
        
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
    #
    def analyze(self, raw_data=[]):
        '''
        pulse, sleepの時間には、誤差があるが、
        一組のパルスとスリープの和は、ほぼ正確と仮定。
    
        真のパルス+スリープ時間を t_p, t_s、誤差 tdとしたとき、
          raw_data[pulse] + raw_data[sleep] = t_p + t_s
          raw_data[pulse] = t_p + td
          raw_data[sleep] = t_s - td
           
        '''
        self.logger.debug('raw_data=%s', raw_data)

        if raw_data != []:
            self.get_raw_data(raw_data)
            self.logger.debug('raw_data=%s', self.raw_data)

        if len(raw_data) < self.RAW_DATA_LEN_MIN:
            self.logger.warning('raw_data is too short ... ignored')
            return False

        # pulse + sleep の値のリスト
        self.sum_list = [(d1 + d2) for d1, d2 in self.raw_data]
        self.logger.debug('sum_list=%s', self.sum_list)

        # self.sum_listの度数分布
        self.fq_list = self.fq_dist(self.sum_list, 0.2)
        self.logger.debug('fq_list=%s', self.fq_list)

        # 単位時間<T> = 度数分布で一番小さいグループの平均の半分
        self.T = (sum(self.fq_list[0]) / len(self.fq_list[0])) / 2
        self.logger.debug('T=%.2f[us]', self.T)

        # 誤差 td を求める
        self.T1 = {'pulse': [], 'space': []}
        for i, s in enumerate(self.sum_list):
            if self.sum_list[i] in self.fq_list[0]:
                self.T1['pulse'].append(self.raw_data[i][0])
                self.T1['space'].append(self.raw_data[i][1])
        self.T1_ave = {'pulse':[], 'space':[]}
        # (pulse,spaceのTdの平均値を求めているが、pulseだけでも十分?)
        for key in ['pulse', 'space']:
            self.T1_ave[key] = sum(self.T1[key]) / len(self.T1[key])
        self.Td_p = abs(self.T1_ave['pulse'] - self.T)
        self.Td_s = abs(self.T1_ave['space'] - self.T)
        self.Td = (self.Td_p + self.Td_s) / 2
        self.logger.debug('Td=%.2f, Td_p=%.2f, Td_s=%.2f',
                          self.Td, self.Td_p, self.Td_s)

        # self.raw_dataのそれぞれの値(Tdで補正)が、self.Tの何倍か求める
        self.n_list_float = []  # for debug
        self.n_list = []
        for p, s in self.raw_data:
            n_p = (p - self.Td) / self.T
            n_s = (s + self.Td) / self.T
            self.n_list_float.append([n_p, n_s])
            n_p = round(n_p)
            n_s = round(n_s)
            self.n_list.append([n_p, n_s])
        self.logger.debug('n_list_float=%s', self.n_list_float)
        self.logger.debug('n_list=%s', self.n_list)

        # 信号パターン抽出
        self.n_pattern = sorted(list(map(list, set(map(tuple, self.n_list)))))
        self.logger.debug('n_pattern=%s', self.n_pattern)

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
                self.sig_format.append('DYSON')
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

        self.ch2sig = {}
        for key in self.SIG_CH.keys():
            self.ch2sig[self.SIG_CH[key]] = self.sig2n[key]
        self.logger.debug('ch2sig=%s', self.ch2sig)

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

        self.logger.debug('sig_format=%s', self.sig_format)
        self.logger.debug('sig_format2=%s', self.sig_format2)
        self.logger.debug('sig2n=%s', self.sig2n)

        # 信号名リストを生成
        self.sig_list = []
        for n1, n2 in self.n_list:
            for key in self.sig2n.keys():
                if [n1, n2] in self.sig2n[key]:
                    self.sig_list.append(key)
        self.logger.debug('sig_list=%s', self.sig_list)

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

            self.sig_str += self.SIG_CH[sig]
            
            if self.sig_line_usec == []:
                self.sig_line_usec = [0]
                
            self.sig_line_usec[-1] += self.raw_data[i][0] + self.raw_data[i][1]

        if self.sig_line_usec[-1] == 0:
            self.sig_line_usec.pop(-1)
        # 最後のspace時間を引く
        self.sig_line_usec[-1] -= self.raw_data[-1][1]

        self.logger.debug('sig_str=%s',       self.sig_str)
        self.logger.debug('sig_line_usec=%s', self.sig_line_usec)

        # leaderを区切りとして、信号文字列を区切る
        self.sig_line1 = self.sig_str.split()
        self.logger.debug('sig_line1=%s', self.sig_line1)

        # 信号文字列の中をさらに分割
        # 0,1の部分は分割しない
        self.sig_line = []
        for i, l1 in enumerate(self.sig_line1):
            for key in self.SIG_CH.keys():
                if self.SIG_CH[key] in self.SIG_STR_01:
                    continue
                l1 = l1.replace(self.SIG_CH[key],
                                ' ' + self.SIG_CH[key] + ' ')
            #self.sig_line.append([l1.split(), self.sig_line_usec[i]])
            self.sig_line.append(l1.split())
        self.logger.debug('sig_line=%s', self.sig_line)

        # sig_line を16進に変換
        self.sig_line_hex = []
        for sig in self.sig_line:
            sig2 = []
            for s in sig:
                if s[0] in self.SIG_STR_01:
                    sig2.append(self.bit2hex(s, 4))
                else:
                    sig2.append(s)
            #self.sig_line_hex.append([sig2, us])
            self.sig_line_hex.append(sig2)
        self.logger.debug('sig_line_hex=%s', self.sig_line_hex)

        # linear ( flat list ) .. [[a, b], c] -> [a, b, c]
        self.sig_linear = []
        for s1 in self.sig_line_hex:
            self.logger.debug('s1=%s', s1)
            if type(s1) == list:
                for s2 in s1:
                    self.logger.debug('s2=%s', s2)
                    self.sig_linear.append(s2)
            else:
                self.sig_linear.append(s1)
        self.logger.debug('sig_linear=%s', self.sig_linear)

        ### XXX
        # エラーチェック
        # T.B.D.

        ### 結果のまとめ
        self.sig_format_result = ''
        if len(self.sig_format) == 0:
            if len(self.sig_format2) == 0:
                self.sig_format_result = '?'
            if len(self.sig_format2) == 1:
                self.sig_format_result = self.sig_format2[0]
            else:
                self.sig_format_result = self.sig_format2
                
        elif len(self.sig_format) == 1:
            self.sig_format_result = self.sig_format[0]

        else:
            self.sig_format_result = self.sig_format
            
        self.result = {
            "header": {
                "name":     "dev_name",
                "memo":     "memo",
                "format":   self.sig_format_result,
                "T":        self.T,       # us
                "sig_tbl":  self.ch2sig,
                "macro": {
                    "P":    "",
                    "Q":    ""
                }
            },
            "buttons": {
                "button": self.sig_linear
            }
        }

        return True

          
    def bit2hex(self, b, n=2, lsb_first=False):
        '''
        bit pattern strings to hex strings
        '''
        if b[0] not in self.SIG_STR_01:
            return b

        if lsb_first:
            b = b[::-1] # 前後反転
        hex_len = int((len(b) - 1) / 4) + 1
        h = ('0' * hex_len + '%X' % int(b, 2))[-hex_len:]
        h = self.split_str(h[::-1], n)
        h = h[::-1]
        return h
        

    #
    # display normalized data
    #
    def disp_norm(self, button_num):
        if len(self.raw_data) == 0:
            return
        self.print('# normalized data')
        self.print('\tname\tbutton%d' % button_num)
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
            if ch not in self.SIG_STR_01 or n % 4 == 0:
                self.print()
                n = 0
        if n > 0:
            self.print()
        return


####
class App:
    TMP_JSON_FILE = '/tmp/IrAnalyze.json'

    def __init__(self, pin, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('pin=%d', pin)

        self.pin = pin

        self.rcvr     = IrRecv(self.pin, debug=self.debug)
        self.analyzer = IrAnalyze(debug=self.debug)

    def main(self):
        self.logger.debug('')

        while True:
            raw_data = self.rcvr.recv()
            if self.analyzer.analyze(raw_data):
                r = self.analyzer.result
                print('%s, %s' % (r['header']['format'],
                                  ''.join(r['buttons']['button']).replace(' ','')))
                with open(self.TMP_JSON_FILE, 'w') as f:
                    #json.dump(r, f, indent=2)
                    json.dump(r, f)
                    f.write('\n')
                break
        

    def end(self):
        self.logger.debug('')
    
#### main
import click
from IrRecv import IrRecv
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS,
               help='IR signal analyzer')
@click.argument('pin', type=int, default=27)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(pin, debug):
    logger = my_logger.get_logger(__name__, debug)
    logger.debug('pin=%d', pin)

    app = App(pin, debug=debug)
    try:
        app.main()
    finally:
        logger.debug('finally')
        app.end()
        

if __name__ == '__main__':
    main()
