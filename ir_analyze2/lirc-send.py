#!/usr/bin/env python3
#
# (c) 2018 Yoichi Tanibayashi
#

import socket
import time
import click

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(INFO)
handler_fmt = Formatter('[%(levelname)s] %(message)s')
handler.setFormatter(handler_fmt)
logger.addHandler(handler)
logger.propagate = False

#####
class IrSend():
    '''
    Reference	http://www.lirc.org/html/lircd.html
    '''
    
    SOCK_PATH = '/var/run/lirc/lircd'
    
    def send1(self, dev, btn):
        ret = -1

        lircd = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        lircd.settimeout(0.5)
        lircd.connect(self.SOCK_PATH)
                
        data = 'SEND_ONCE %s %s\r\n' % (dev, btn)
        lircd.send(data.encode('utf-8'))
        logger.debug('send1> send:%s.', data.rstrip())

        wait_flag, wait_count, wait_max= True, 0, 1
        while wait_flag:
            try:
                recv_flag = True
                while recv_flag:
                    data = lircd.recv(1024).decode('utf-8').rstrip()
                    logger.debug('send1> data=%s', data)
                    wait_count = 0
                    if 'ERROR' in data:
                        wait_flag = False
                        ret = -1
                    if 'SUCCESS' in data:
                        wait_flag = False
                        ret = 0
                    if 'repeating' in data:
                        logger.warning('send1> %s', data)
                        wait_flag = False
                        ret = 0
                    if 'unknown' in data:
                        logger.error('send1> %s', data)
                        wait_flag = False
                        ret = -2
                    if 'END' in data:
                        recv_flag = False
                        
                
            except socket.timeout:
                wait_count += 1
                if wait_count > wait_max:
                    logger.error('send1> timeout')
                    ret = -1
                    wait_flag = False
                    break
                logger.debug('send1> waiting[%d/%d] %s %s ..',
                             wait_count, wait_max, dev, btn)
                time.sleep(0.3)

        return ret

    def send(self, dev, btn, interval=0.5):
        ret = -1
        retry = 5
        for b in btn:
            count = 0
            while True:
                count += 1
                ret = self.send1(dev, b)
                logger.debug('send> count=%d, send1(%s,%s):ret=%d',
                             count, dev, b, ret)
                if ret >= 0:
                    break	# success
                if ret <= -2:
                    break	# critical
                if count >= retry:
                    logger.error('send1> send1() fail')
                    break	# fail
                time.sleep(interval)

            time.sleep(interval)
        return ret

#####
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
    if debug:
        logger.setLevel(DEBUG)
        
    logger.debug('main> %s %s', device, button)

    irs = IrSend()
    ret = -1
    for i in range(count):
        logger.debug('main> i=%d', i + 1)
        ret = irs.send(device, button, interval)
        if ret < 0:
            logger.error('main> send(%s,%s,%.1f):ret=%d',
                         device, button, interval, ret)
            break

#####
if __name__ == '__main__':
    main()
