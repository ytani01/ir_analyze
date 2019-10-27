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
class IrConfig:
    '''
    JSON format:
    {
      "header": {
        "name": "dev_name",
        "memo": "memo_str",
        "T":    T(us),
        "sig_tbl": {
          "-": [n, n], .. leader
          "=": [n, n], .. leader?
          "0": [n, n], .. 0
          "1": [n, n], .. 1
          "/": [n, n], .. trailer
          "*": [n, n], .. repeat
          "?": [n, n]  .. ???
        },
        "macro": {
          "P": "(hex)", .. prefix, postfix or else
          "Q": "(hex)"  .. prefix, postfix or else
          :
        }
        # optional
        "format:": "AEHA"
      }
      "buttons": {
        "button1": "-P(hex)Q/*/*/",
        "button2": "- P (hex) /",
        "button3": ["-", "(hex)", "Q", "/", "*/", "*/"]
        :
      }
    }
    '''

    DEF_CONF_DIR      = "/etc/ir.conf.d"
    DEF_CONF_PATH     = ['.', '@home', DEF_CONF_DIR]
    DEF_CONF_FILENAME = "ir.conf"

    DATA_HEADER_BIN   = '(b)'
    
    def __init__(self, filename='', debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, self.debug)
        self.logger.debug('')

        self.filename = filename

        self.data = []


    def load(self, filename=''):
        self.logger.debug('')

        if filename != '':
            self.filename = filename
        if filename == '':
            self.logger.warning('no filename')
            return None

        try:
            with open(self.filename, 'r') as f:
                data = json.load(f)
                data_str = json.dumps(data, indent=2)
                self.logger.debug('data=%s', data_str)
        except json.JSONDecodeError as e:
            self.logger.error("%s, %s", type(e), e)
            return None

        if type(data) == list:
            for d in data:
                self.data.append(d)
        else:
            self.data.append(data)
                
        return data
        

    def save(self, filename=''):
        self.logger.debug('')

        if filename != '':
            self.filename = filename
        if filename == '':
            self.logger.warning('no filename')
            return None
            
        
#####
class App:
    '''
    '''
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('')

    def main(self, filename=''):
        self.logger.debug('filename=%s', filename)

        self.conf = IrConfig(debug=self.debug)
        self.conf.load(filename)

        print(self.conf.data)

    def end(self):
        self.logger.debug('')

#### main
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS,
               help='IR config')
@click.argument('filename')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(filename, debug):
    logger = my_logger.get_logger(__name__, debug)

    app = App(debug=debug)
    try:
        app.main(filename)
    finally:
        logger.debug('finally')
        app.end()

if __name__ == '__main__':
    main()
