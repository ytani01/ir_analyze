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
        cmdline = [__class__.CMDNAME, 'SEND_ONCE', dev, btn]
        proc = subprocess.Popen(cmdline)

        wait_flag, wait_count = True, 0
        while wait_flag:
            try:
                proc.wait(__class__.WAIT_SEC)
                wait_flag = False
                
            except subprocess.TimeoutExpired:
                wait_count += 1
                logger.debug('waiting[%d] %s ..', wait_count, btn)

    def send(self, dev, btn):
        for b in btn:
            logger.debug('%s %s', dev, b)
            self.send1(dev, b)
            time.sleep(.5)

#####
@click.command(help='irsend python')
@click.argument('device', type=str, nargs=1)
@click.argument('button', type=str, nargs=-1, required=True)
def main(device, button):
    logger.debug('%s %s', device, button)

    irs = IrSend()
    irs.send(device, button)

#####
if __name__ == '__main__':
    main()
