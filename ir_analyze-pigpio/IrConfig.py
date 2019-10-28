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

#####
from MyLogger import MyLogger
my_logger = MyLogger(__file__)

#####
class IrConfData:
    '''
    JSON format:
    {
      "header": {
        "name": "dev_name",
        "memo": "memo_str",
        "T":    T(us),
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
          "[prefix]": "(code)",  # prefix, postfix or else
          "[postfix]": "(code)"  # prefix, postfix or else
          "[postfix]": "(code)"  # prefix, postfix or else
          :
        }
        # optional
        "format:": "AEHA"
      }
      "buttons": {
        "button1": "-P(hex)Q/*/*/",
        "button2": "- P (hex) /",
        "button3": ["-", "(code)", "[postfix]", "/", "*/", "*/"]
        :
      }
    }
    '''
    HEADER_BIN = '(b)'

    def __init__(self, conf_data=None, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, self.debug)
        self.logger.debug("confdata=%s", conf_data)

        if conf_data is None:
            self.data = [{
                'header': {
                    'name': ['dev_name1', 'dev_name2'],
                    'T':    0,
                    'sym_tbl': {
                        '-': [], # leader
                        '=': [], # leader?
                        '0': [], # 0
                        '1': [], # 1
                        '/': [], # trailer
                        '*': [], # repeat
                        '?': []  # ???
                    },
                    'macro': {
                        '[prefix]':  '',
                        '[postfix]': ''
                    },
                    # optional
                    'format:': ''
                },
                'buttons': {
                    'button1': '',
                    'button2': ''
                }
            }]
        else:
            self.data = conf_data

    def get_dev_name(self, conf_data=None):
        self.logger.debug('conf_data=%s', conf_data)
        if conf_data is None:
            conf_data = self.data
            self.logger.debug('conf_data=%s', conf_data)

        return conf_data['dev_name']

    def get_button(self, button_name='', conf_data=None):
        self.logger.debug('button_name=%s, conf_data=%s', button_name,
                          conf_data)
        if conf_data is None:
            conf_data = self.data
            self.logger.debug('conf_data=%s', conf_data)

        if button_name == '':
            return conf_data['buttons']

        return conf_data['buttons'][button_name]

    def get_macro(self, macro_name='', conf_data=None):
        self.logger.debug('button_name=%s, conf_data=%s',
                          button_name, conf_data)
        if conf_data is None:
            conf_data = self.data
            self.logger.debug('conf_data=%s', conf_data)

        if macro_name == '':
            return conf_data['macro']

        return conf_data['macro'][macro_name]
        
    
class IrConfFile:
    DEF_CONF_DIR      = '/etc/ir.conf.d'
    DEF_CONF_PATH     = ['.', '@home', DEF_CONF_DIR]
    DEF_CONF_FILENAME = 'ir.conf'

    def __init__(self, file_name=None, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, self.debug)
        self.logger.debug('file_name=%s', file_name)

        self.file_name = file_name

        self.data = []

        if self.file_name is not None:
            self.load()

    def load(self, file_name=None):
        self.logger.debug('file_name=%s', file_name)

        if file_name is None:
            file_name = self.file_name

        if file_name is None:
            self.logger.warning('no file_name')
            return None

        try:
            with open(self.file_name, 'r') as f:
                data = json.load(f)
                self.logger.debug('data=%s', json.dumps(data))
        except json.JSONDecodeError as e:
            self.logger.error('%s, %s', type(e), e)
            return None

        if type(data) == list:
            for d in data:
                self.data.append(d)
        else:
            self.data.append(data)
                
        return self.data
        

    def save(self, file_name=None):
        self.logger.debug('')

        if file_name is None:
            file_name = self.file_name
            
        
#####
class App:
    '''
    '''
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('')

    def main(self, file_name=''):
        self.logger.debug('file_name=%s', file_name)

        self.conf = IrConfFile(debug=self.debug)
        self.conf.load(file_name)

        print(self.conf.data)
        print(self.conf.get_dev_name(self.conf.data[0]))

    def end(self):
        self.logger.debug('')

#### main
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS,
               help='IR config')
@click.argument('file_name')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(file_name, debug):
    logger = my_logger.get_logger(__name__, debug)

    app = App(debug=debug)
    try:
        app.main(file_name)
    finally:
        logger.debug('finally')
        app.end()

if __name__ == '__main__':
    main()
