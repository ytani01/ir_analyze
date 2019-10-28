#!/usr/bin/python3 -u
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
      "header": {
        "dev_name": ["dev_name1", "dev_name2"],
        "format:": "{AEHA|NEC|AEHA|DYSON}"      # optional
        "T":    t,     # us
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

        ### XXX

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
                d_nlist = d_ent['data']['header']['dev_name']
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
