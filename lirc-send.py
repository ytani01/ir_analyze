#!/usr/bin/env python3
#
# (c) 2018 Yoichi Tanibayashi
#

import socket
import time

##### logger
from MyLogger import MyLogger
my_logger = MyLogger(__file__)

#####
class IrSend():
    '''
    LIRC Reference	http://www.lirc.org/html/lircd.html
    '''
    
    SOCK_PATH = '/var/run/lirc/lircd'
    
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, self.debug)
        self.logger.debug('debug = %s', self.debug)

    def send1(self, dev, btn):
        self.logger.debug('dev=%s, btn=%s', dev, btn)
        
        ret = -1

        lircd = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        lircd.settimeout(0.5)
        lircd.connect(self.SOCK_PATH)
                
        data = 'SEND_ONCE %s %s\r\n' % (dev, btn)
        lircd.send(data.encode('utf-8'))
        self.logger.debug('send:%s.', data.rstrip())

        wait_flag, wait_count, wait_max= True, 0, 1
        while wait_flag:
            try:
                recv_flag = True
                while recv_flag:
                    data = lircd.recv(1024).decode('utf-8').rstrip()
                    self.logger.debug('data=%s', data)
                    wait_count = 0
                    if 'ERROR' in data:
                        wait_flag = False
                        ret = -1
                    if 'SUCCESS' in data:
                        wait_flag = False
                        ret = 0
                    if 'repeating' in data:
                        self.logger.warning('%s', data)
                        wait_flag = False
                        ret = 0
                    if 'unknown' in data:
                        self.logger.error('%s', data)
                        wait_flag = False
                        ret = -2
                    if 'END' in data:
                        recv_flag = False
                        
                
            except socket.timeout:
                wait_count += 1
                if wait_count > wait_max:
                    self.logger.error('timeout')
                    ret = -1
                    wait_flag = False
                    break
                self.logger.debug('waiting[%d/%d] %s %s ..',
                                  wait_count, wait_max, dev, btn)
                time.sleep(0.3)

        return ret

    def send(self, dev, btn, interval=0.5):
        self.logger.debug('dev=%s, btn=%s, interval=%.1f',
                          dev, btn, interval)
        
        ret = -1
        retry = 5
        for b in btn:
            count = 0
            while True:
                count += 1
                ret = self.send1(dev, b)
                self.logger.debug('count=%d, send1(%s,%s):ret=%d',
                                  count, dev, b, ret)
                if ret >= 0:
                    break	# success
                if ret <= -2:
                    break	# critical
                if count >= retry:
                    self.logger.error('send1() fail')
                    break	# fail
                time.sleep(interval)

            time.sleep(interval)
        return ret

#####
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(help='irsend python')
@click.argument('device', type=str, nargs=1)
@click.argument('button', type=str, nargs=-1, required=True)
@click.option('--interval', '-i', '-t', type=float, default=0.5,
              help='interval time(sec)')
@click.option('--count', '-c', type=int, default=1,
              help='count')
@click.option('--debug', '-d', is_flag=True, default=False,
              help='debug flag')
def main(device, button, interval, count, debug):
    logger = my_logger.get_logger(__name__, debug)

    logger.debug('%s %s', device, button)

    irs = IrSend(debug=debug)
    ret = -1
    for i in range(count):
        logger.debug('i=%d', i + 1)
        ret = irs.send(device, button, interval)
        if ret < 0:
            logger.error('send(%s,%s,%.1f):ret=%d',
                         device, button, interval, ret)
            break

#####
if __name__ == '__main__':
    main()
