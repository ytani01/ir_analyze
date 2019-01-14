#!/usr/bin/env python3

import subprocess
import time
import click

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
handler_fmt = Formatter('[%(levelname)s] %(message)s')
handler.setFormatter(handler_fmt)
logger.addHandler(handler)
logger.propagate = False

#####
class IrSend():
    CMDNAME	='irsend'
    WAIT_SEC	= 1.0
    
    def send1(self, dev, btn):
        ret = -1
        cmdline = [__class__.CMDNAME, 'SEND_ONCE', dev, btn]
        proc = subprocess.Popen(cmdline)

        wait_flag, wait_count = True, 0
        while wait_flag:
            try:
                ret = proc.wait(__class__.WAIT_SEC)
                logger.debug('send1> ret=%d', ret)
                wait_flag = False
                
            except subprocess.TimeoutExpired:
                wait_count += 1
                if wait_count > 5:
                    ret = -2
                    wait_flag = False
                    break
                logger.debug('send1> waiting[%d] %s %s ..',
                             wait_count, dev, btn)

        return ret

    def send(self, dev, btn, interval=0.5):
        ret = -1
        for b in btn:
            logger.debug('send> %s %s', dev, b)
            ret = self.send1(dev, b)
            if ret != 0:
                logger.error('send> send1(%s,%s):ret=%d', dev, b, ret)
                break
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
def main(device, button, interval, count):
    logger.debug('main> %s %s', device, button)

    irs = IrSend()
    ret = -1
    for i in range(count):
        logger.debug('main> i=%d', i + 1)
        ret = irs.send(device, button, interval)
        if ret != 0:
            logger.error('main> send(%s,%s,%.1f):ret=%d',
                         device, button, interval, ret)
            time.sleep(2)
            break

#####
if __name__ == '__main__':
    main()
