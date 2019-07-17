#!/usr/bin/env python3
#
# (C) 2018 Yoichi Tanibayashi
#
import sys
import os
import time
import re
import click
from CmdOut import CmdOut

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
class SysMon:
    DEF_SERVER = 'localhost'
    DEF_PORT = 12345

    def __init__(self, cmd, keyword, server='', port=0):
        logger.debug('cmd=%s', cmd)
        logger.debug('keyword=%s', keyword)
        
        self.myname = os.path.basename(sys.argv[0])
        logger.debug('self.myname=%s', self.myname)
        self.cmd = cmd
        self.keyword = keyword
        
        self.server, self.port = __class__.DEF_SERVER, __class__.DEF_PORT
        if server != '':
            self.server = server
        if port != 0:
            self.port = port

    def loop(self):
        while True:
            self.co = CmdOut(self.cmd)
            self.co.start()

            if len(self.keyword):
                found_flag = {}
                for k in self.keyword:
                    found_flag[k] = False
                
            print('-----')
            while True:
                line = self.co.readline(timeout=0.1)
                if not line:
                    break

                #line = ' '.join(line.split()[10:12])
                #logger.debug(line)
                
                if self.myname in line:
                    continue
                
                if len(self.keyword) > 0:
                    for k in self.keyword:
                        if re.search(k, line):
                            found_flag[k] = True
                else:
                    logger.debug(line)

            if len(self.keyword) > 0:
                for k in self.keyword:
                    ch = ' '
                    if found_flag[k]:
                        ch = '*'
                    print('[%s] %s' % (ch, k))
                    
            time.sleep(.3)
        
    
#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS, help='Template program')
@click.argument('cmd', type=str, default='ps auxww')
@click.argument('keyword', type=str, nargs=-1)
@click.option('--oled_server', '-os', 'oled_server', type=str, default='localhost',
              help='server\'s hostname or IP address')
@click.option('--oled_port', '-op', 'oled_port', type=int, default=0,
              help='server\'s port number')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(cmd, keyword, oled_server, oled_port, debug):
    logger.setLevel(INFO)
    if debug:
        logger.setLevel(DEBUG)

    logger.debug('cmd=\'%s\', oled_server=\'%s\', oled_port=%d',
                 cmd, oled_server, oled_port)

    cmd = cmd.split()
    obj = SysMon(cmd, keyword, oled_server, oled_port)
    obj.loop()

if __name__ == '__main__':
    main()
