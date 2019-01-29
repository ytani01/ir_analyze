#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
import csv

import click

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN
logger = getLogger(__name__)
logger.setLevel(INFO)
handler = StreamHandler()
handler.setLevel(DEBUG)
handler_fmt = Formatter(
    '%(asctime)s %(levelname)s %(name)s.%(funcName)s> %(message)s',
    datefmt='%H:%M:%S')
handler.setFormatter(handler_fmt)
logger.addHandler(handler)
logger.propagate = False
def init_logger(name, debug):
    l = logger.getChild(name)
    if debug:
        l.setLevel(DEBUG)
    else:
        l.setLevel(INFO)
    return l

#####
class ConvertCode:
    def __init__(self, in_code, debug=False):
        self.logger = init_logger(__class__.__name__, debug)
        self.logger.debug('')
        self.debug = debug

        self.in_code = in_code
        self.out = []

    # for 'with' statement
    def __enter__(self):
        self.logger.debug('')
        self.open()
        return self
    def __exit__(self, ex_type, ex_value, trace):
        self.logger.debug('(%s,%s,%s)', ex_type, ex_value, trace)
        self.close()

    def open(self):
        self.logger.debug('')

    def close(self):
        self.logger.debug('')

    def conv(self):
        self.logger.debug('')

        

##### sample application
class Sample:
    CONV_DEV = [
        ['ソニー',           'sony'],
        ['東芝',             'toshiba'],
        ['日立',             'hitachi'],
        ['パナソニック',     'panasonic'],
        ['ビクター',         'victor'],
        ['ダイキン',         'daikin'],
        ['パイオニア',       'pioneer'],
        ['サンヨー',         'sanyo'],
        ['シャープ',         'sharp'],
        ['三菱',             'mitsubishi'],
        ['重工',             'juko'],
        ['富士通ゼネラル',   'fujitsu'],
        ['アイリスオーヤマ', 'iris'],
        ['コロナ',           'corona'],
        ['タキズミ',         'takizumi'],
        ['コイズミ',         'koizumi'],
        ['デジタルテレビ', 'tv'],
        ['エアコン',       'aircon'],
        ['照明器具',       'light'],
        ['１','1'],
        ['２','2'],
        ['３','3'],
        ['４','4'],
        ['５','5'],
        ['０','0']
    ]
    CONV_BTN = [
        ['電源',       'power'],
        ['運転 暖房 ', 'on_hot_'],
        ['運転 冷房 ', 'on_cool_'],
        ['点灯',       'on'],
        ['消灯',       'off'],
        ['一時停止',   'pause'],
        ['停止',       'off'],
        ['メニュー',   'menu'],
        ['チャンネル', 'ch'],
        ['音量',       'vol'],
        ['消音',       'mute'],
        ['入力切換',   'input'],
        ['青',         'blue'],
        ['赤',         'red'],
        ['緑',         'green'],
        ['黄',         'yellow'],
        ['決定',       'ok'],
        ['戻る',       'back'],
        ['↑',         'up'],
        ['↓',         'down'],
        ['←',         'left'],
        ['→',         'right'],
        ['音量',       'vol'],
        ['＋',         '+'],
        ['－',         '-'],
        ['+',          '_plus'],
        ['-',          '_minus'],
        ['０','0']
    ]
        
    def __init__(self, infile, debug=False):
        self.logger = init_logger(__class__.__name__, debug)
        self.logger.debug('infile = %s', infile)

        self.infile = infile
        self.debug = debug

    def main(self):
        data1 = {}
        with open(self.infile, 'r') as c:
            reader = csv.reader(c, delimiter=',', quotechar='"')
            for line in reader:
                (manufacturer, device, button, code) = line
                #self.logger.debug('manufacturer : %s', manufacturer)
                #self.logger.debug('device       : %s', device)
                #self.logger.debug('button       : %s', button)
                #self.logger.debug('code         : %s', code)

                device2 = self.conv_dev('%s_%s' % (manufacturer, device))
                button = self.conv_btn(button)

                code2 = []
                for i in range(int(len(code)/4)):
                    hex_str = ''
                    for i2 in range(4):
                        hex_str += code[i*4+i2]
                    hex_str2 = hex_str[-2:] + hex_str[:2]
                    code2.append(int(hex_str2, 16) * 26)

                #print('%s:%s:%s' % (device2, button, code2))

                if device2 not in data1.keys():
                    data1[device2] = {}

                data1[device2][button] = code2

        for dev in sorted(data1.keys()):
            print('device %s' % dev)
            for btn in sorted(data1[dev].keys()):
                print('\tname\t%s' % btn)
                count = 0
                for d in data1[dev][btn]:
                    print('%5d ' % d, end='')
                    count += 1
                    if count == 2 or count % 8 == 2:
                        print()
                if count == 2 or count % 8 != 2:
                    print()
                print()
            print()

    def conv_dev(self, str):
        for [src, dst] in self.CONV_DEV:
            str = str.replace(src, dst)
        self.logger.debug('str = %s', str)
        return str

    def conv_btn(self, str):
        for [src, dst] in self.CONV_BTN:
            str = str.replace(src, dst)
        return str
                    
#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('infile', metavar='<csv_file>', type=click.Path(exists=True))
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(infile, debug):
    logger = init_logger('', debug)
    logger.debug('infile = %s', infile)
    logger.debug('debug  = %s', debug)

    Sample(infile, debug=debug).main()

if __name__ == '__main__':
    main()
