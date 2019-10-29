#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
'''
IrConfig.py
'''
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'

import os
import json
from pathlib import Path

#####
from MyLogger import MyLogger
my_logger = MyLogger(__file__)

#####
class IrConfig:
    '''
    data      := [{data_ent1}, {data_ent2}, ..}
    data_ent  := {'file': 'file_name1', 'data': 'conf_data1'}
    conf_data := 
    {
      "comment": "comment text",
      "dev_name": ["dev_name1", "dev_name2"],
      "format:": "{AEHA|NEC|AEHA|DYSON}"      # optional
      "T": t,        # us
      "sym_tbl": {
        "-": [n, n], # leader
        "=": [n, n], # leader?
        "0": [n, n], # 0
        "1": [n, n], # 1
        "/": [n, n], # trailer
        "*": [n, n], # repeat
        "?": [n, n]  # ???
      },
      "macro": {
        "[prefix]": "- {hex|(0b)bin} ",
        "[suffix]": "{hex|bin} /",
        "[repeat]": "*/"
      }
      "buttons": {
        "button1": "[prefix] {hex|bin} [suffix] [repeat] [repeat]",
        "button2": ["[prefix] {hex|bin} [suffix] [repeat] [repeat]", n]
      }
    }
    '''
    HEADER_BIN   = '(0b)'
    CONF_SUFFIX  = '.irconf'
    DEF_CONF_DIR = ['.',
                    str(Path.home()) + '/.irconf.d',
                    '/etc/irconf.d']

    def __init__(self, conf_dir=None, load_all=False, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, self.debug)
        self.logger.debug('conf_dir=%s', conf_dir)

        if conf_dir is None:
            self.conf_dir = self.DEF_CONF_DIR
        else:
            if type(conf_dir) == list:
                self.conf_dir = conf_dir
            else:
                self.conf_dir = [conf_dir]
        self.logger.debug('conf_dir=%s', self.conf_dir)

        self.data = []

        if load_all:
            self.load_all()
            
    def get_pulse_space(self, dev_name, button_name):
        self.logger.debug('dev_name=%s, button_name=%s', dev_name, button_name)

        dev_data = self.get_dev_data(dev_name)
        try:
            button_data = dev_data['buttons'][button_name]
        except KeyError:
            self.logger.warning('no such button: %s,%s', dev_name, button_name)
            return []
        self.logger.debug('button_data=%s', button_data)

        sig_str = ''
        #
        # 繰り返し回数展開
        #
        if type(button_data) == str:
            sig_str = button_data
        elif type(button_data) == list:
            if len(button_data) == 2:
                (s, n) = button_data
                for i in range(n):
                    sig_str += s
        self.logger.debug('sig_str=%s', sig_str)
        if sig_str == '':
            self.logger.error('invalid button_data:%s', button_data)
            return []

        #
        # マクロ(prefix, suffix etc.)展開
        #
        for m in dev_data['macro']:
            sig_str = sig_str.replace(m, dev_data['macro'][m])
        #
        # スペース削除
        #
        sig_str = sig_str.replace(' ', '')
        self.logger.debug('sig_str=%s', sig_str)

        #
        # 記号、数値部の分割
        #
        for ch in dev_data['sym_tbl']:
            if ch in '01':
                continue
            sig_str = sig_str.replace(ch, ' ' + ch + ' ')
        self.logger.debug('sig_str=%s', sig_str)
        sig_list1 = sig_str.split()
        self.logger.debug('sig_list1=%s', sig_list1)

        #
        # hex -> bin
        #
        sig_list2 = []
        for sig in sig_list1:
            if sig in dev_data['sym_tbl']:
                if sig not in '01':
                    sig_list2.append(sig)
                    continue

            if sig.startswith(self.HEADER_BIN):
                # '(0b)0101' -> '0101'
                sig_list2.append(sig[len(self.HEADER_BIN):])
                continue

            # hex -> bin
            bin_str = ''
            for ch in sig:
                if ch in '0123456789ABCDEFabcdef':
                    bin_str += format(int(ch, 16), '04b')
                else:
                    bin_str += ch
            sig_list2.append(bin_str)
        self.logger.debug('sig_list2=%s', sig_list2)

        #
        # 一つの文字列に再結合
        #
        sig_str2 = ''.join(sig_list2)
        self.logger.debug('sig_str2=%s', sig_str2)
                    
        #
        # make pulse,space list (p_s_list)
        #
        p_s_list = []
        t = dev_data['T']
        for ch in sig_str2:
            if ch not in dev_data['sym_tbl']:
                self.logger.warning('ch=%s !? .. ignored', ch)
                continue
            (pulse, space) = dev_data['sym_tbl'][ch][0]
            p_s_list.append(pulse * t)
            p_s_list.append(space * t)
        self.logger.debug('p_s_list=%s', p_s_list)

        return p_s_list


    def get_button_data(self, dev_name, button_name):
        self.logger.debug('dev_name=%s, button_name=%s', dev_name, button_name)

        buttons = self.get_buttons(dev_name)
        try:
            return buttons[button_name]
        except KeyError:
            return None

    def get_buttons(self, dev_name):
        self.logger.debug('dev_name=%s', dev_name)

        data_ent = self.get_dev(dev_name)
        self.logger.debug('data_ent=%s', data_ent)

        if data_ent is None:
            self.logger.waring('%s: no such device', dev_name)
            return []

        # found
        try:
            buttons = data_ent['data']['buttons']
        except KeyError:
            self.logger.waring('no button !?')
            return []

        return buttons
            
    def get_dev_data(self, dev_name):
        self.logger.debug('dev_name=%s', dev_name)

        data_ent = self.get_dev(dev_name)
        if data_ent is None:
            return None

        return data_ent['data']

    def get_dev(self, dev_name):
        self.logger.debug('dev_name=%s', dev_name)

        for d_ent in self.data:
            try:
                d_nlist = d_ent['data']['dev_name']
                self.logger.debug('d_nlist=%s', d_nlist)
            except KeyError:
                self.logger.warning('KeyError .. ignored: %s', d_ent)
                continue
                
            if type(d_nlist) != list:
                d_nlist = [d_nlist]
                self.logger.debug('d_nlist=%s', d_nlist)
            for d_name in  d_nlist:
                self.logger.debug('d_name=%s', d_name)

                if d_name == dev_name:
                    self.logger.debug('%s: found', dev_name)
                    return d_ent

        self.logger.debug('%s: not found', dev_name)
        return None

    def load_all(self):
        self.logger.debug('')

        files = []
        for d in self.conf_dir:
            self.logger.debug('d=%s', d)
            for f in list(Path(d).glob('*' + self.CONF_SUFFIX)):
                files.append(str(f))
        self.logger.debug('files=%s', files)

        for f in files:
            self.load(f)

    def load(self, file_name):
        self.logger.debug('file_name=%s', file_name)

        try:
            with open(file_name, 'r') as f:
                data = json.load(f)
                self.logger.debug('data=%s', json.dumps(data))
        except json.JSONDecodeError as e:
            self.logger.error('%s: %s, %s', file_name, type(e), e)
            return None
        except Exception as e:
            self.logger.error('%s, %s', type(e), e)
            return None

        if type(data) == list:
            for d in data:
                data_ent = {'file': file_name, 'data': d}
                self.data.append(data_ent)
        else:
            data_ent = {'file': file_name, 'data': data}
            self.data.append(data_ent)
        self.logger.debug('data=%s', self.data)
                
        return self.data

    def save(self, file_name=None):
        self.logger.debug('file_name=%s', file_name)

        
#####
class App:
    '''
    '''
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('')

    def main(self, dev_name, button_name, conf_file):
        self.logger.debug('dev_name=%s, button_name=%s, conf_file=%s',
                          dev_name, button_name, conf_file)

        irconf = IrConfig(debug=self.debug)
        print(irconf.conf_dir)

        if len(conf_file) == 0:
            irconf.load_all()
        else:
            irconf.load(conf_file)

        conf_data_ent = irconf.get_dev(dev_name)
        print('conf_data_ent=%s' % conf_data_ent)

        if conf_data_ent is not None:
            conf_data = conf_data_ent['data']
            print('conf_data=%s' % conf_data)
            buttons = irconf.get_buttons(dev_name)
            for b in buttons:
                print('%s: %s' % (b, buttons[b]))

            if button_name != '':
                button_data = irconf.get_button_data(dev_name, button_name)
                print('%s,%s: %s' % (dev_name, button_name, button_data))

                irconf.get_pulse_space(dev_name, button_name)

    def end(self):
        self.logger.debug('')

#### main
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS,
               help='IR config')
@click.argument('dev_name', type=str)
@click.option('--button', '-b', 'button', type=str, default='',
              help='button name')
@click.option('--conf_file', '-c', '-f', 'conf_file', type=str, default='',
              help='config file')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(dev_name, button, conf_file, debug):
    logger = my_logger.get_logger(__name__, debug)
    logger.debug('dev_name=%s, file=%s', dev_name, conf_file)

    app = App(debug=debug)
    try:
        app.main(dev_name, button, conf_file)
    finally:
        logger.debug('finally')
        app.end()

if __name__ == '__main__':
    main()
