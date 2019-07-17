#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
import csv
import time

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
class App:
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
        
        ['デジタルテレビ',   'tv'],
        ['エアコン',         'aircon'],
        ['照明器具',         'light'],
        
        ['０',               '0'],
        ['１',               '1'],
        ['２',               '2'],
        ['３',               '3'],
        ['４',               '4'],
        ['５',               '5'],
        ['６',               '6'],
        ['７',               '7'],
        ['８',               '8'],
        ['９',               '9']
    ]
    CONV_BTN = [
        ['テレビ',     'tv'],
        ['ラジオ',     'radio'],
        ['データ',     'data'],
        ['電源',       'power'],
        ['運転 暖房 ', 'on_hot_'],
        ['運転 冷房 ', 'on_cool_'],
        ['運転 除湿',  'on_dry'],
        ['点灯',       'on'],
        ['消灯',       'off'],
        ['オフ',       'off'],
        ['一時停止',   'pause'],
        ['停止',       'off'],
        ['ホーム',     'home'],
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
        ['タイマー',   'timer'],
        ['＋',         '+'],
        ['－',         '-'],
        ['+',          '_plus'],
        ['-',          '_minus'],
        ['/',          '_'],

        ['℃',         ''],

        ['０',         '0'],
        ['１',         '1'],
        ['２',         '2'],
        ['３',         '3'],
        ['４',         '4'],
        ['５',         '5'],
        ['６',         '6'],
        ['７',         '7'],
        ['８',         '8'],
        ['９',         '9']
    ]
        
    def __init__(self, infile, slow=False, debug=False):
        self.logger = init_logger(__class__.__name__, debug)
        self.logger.debug('infile = %s', infile)

        self.infile = infile
        self.slow   = slow
        self.debug  = debug

    def main(self):
        data1 = {}
        with open(self.infile, 'r') as c:
            reader = csv.reader(c, delimiter=',', quotechar='"')
            for line in reader:
                self.logger.debug('')
                (manufacturer, device, button, code) = line
                self.logger.debug('%s', line)
                #self.logger.debug('%s:%s:%s', manufacturer, device, button)
                #self.logger.debug('%s', code)

                device2 = self.conv_dev('%s_%s' % (manufacturer, device))
                button2 = self.conv_btn(button)

                code2 = []
                for i in range(int(len(code)/4)):
                    hex_str = ''
                    for i2 in range(4):
                        hex_str += code[i*4+i2]
                    hex_str2 = hex_str[-2:] + hex_str[:2]
                    code2.append(int(hex_str2, 16) * 26)

                if device2 not in data1.keys():
                    data1[device2] = {
                        'manufacturer': manufacturer,
                        'device'      : device,
                        'button'      : {} }
                    self.logger.debug('data1[%s]=%s',
                                      device2, str(data1[device2]))

                data1[device2]['button'][button2] = {
                    'line'        : line,
                    'button'      : button,
                    'code'        : code,
                    'code2'       : code2 }
                self.logger.debug('data1[%s][\'button\']=%s',
                                  device2, str(data1[device2]['button']))

                self.sleep()

        for dev in sorted(data1.keys()):
            print('device %s' % dev)
            print('#\t%s:%s' % (
                data1[dev]['manufacturer'],
                data1[dev]['device']) )
            print('')
            
            for btn in sorted(data1[dev]['button']):
                print('\tname\t%s' % btn)
                print('#\t%s:%s' % (
                    data1[dev]['button'][btn]['button'],
                    data1[dev]['button'][btn]['code']) )
                print('')
                
                count = 0
                for d in data1[dev]['button'][btn]['code2']:
                    print('%5d ' % d, end='')
                    count += 1
                    if count == 2 or count % 8 == 2:
                        print()
                if count == 2 or count % 8 != 2:
                    print()
                print()
            print()

    def sleep(self):
        if self.debug and self.slow > 0:
            time.sleep(self.slow)

    def conv_dev(self, str_orig):
        str_new = str_orig
        for [src, dst] in self.CONV_DEV:
            str_new = str_new.replace(src, dst)
        self.logger.debug('\'%s\' -> \'%s\'', str_orig, str_new)
        return str_new

    def conv_btn(self, str_orig):
        str_new = str_orig
        for [src, dst] in self.CONV_BTN:
            str_new = str_new.replace(src, dst)
        self.logger.debug('\'%s\' -> \'%s\'', str_orig, str_new)
        return str_new
                    
#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('infile', metavar='<csv_file>', type=click.Path(exists=True))
@click.option('--slow', '-s', 'slow', type=int, default=0,
              help='slow mode')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(infile, slow, debug):
    logger = init_logger('', debug)
    logger.debug('infile = %s', infile)
    logger.debug('slow   = %d', slow)
    logger.debug('debug  = %s', debug)

    App(infile, slow, debug=debug).main()

if __name__ == '__main__':
    main()
