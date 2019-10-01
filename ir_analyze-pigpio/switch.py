#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
'''
LED
'''
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'

import pigpio
import time

#####
from MyLogger import MyLogger
my_logger = MyLogger(__file__)

#####
class App:
    BOUNCE_USEC = 200000

    def __init__(self, pin, vcc, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('pin: %d, vcc: %d', pin, vcc)

        self.pin = pin
        self.vcc = vcc
        self.tick = 0

        self.pi = pigpio.pi()
        self.pi.set_mode(self.pin, pigpio.INPUT)
        self.pi.set_mode(self.vcc, pigpio.OUTPUT)
        self.pi.write(self.vcc, 1)
        
        self.cb = self.pi.callback(self.pin, pigpio.EITHER_EDGE, self._cb)

    def main(self):
        self.logger.debug('')

        while True:
            self.logger.debug('*')
            time.sleep(5)

    def _cb(self, pin, val, tick):
        self.logger.debug('pin: %d, val: %d, tick: %d', pin, val, tick)
        if self.tick != 0 and tick - self.tick < self.BOUNCE_USEC:
            self.logger.debug('ignore')
            return

        print('%d: %f' % (val, tick / 1000000))
        self.tick = tick

    def end(self):
        self.logger.debug('')

        self.pi.stop()
        
#####
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('pin', type=int, default=21)
@click.argument('vcc', type=int, default=26)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(pin, vcc, debug):
    logger = my_logger.get_logger(__name__, debug)
    logger.debug('pin: %d, vcc: %d', pin, vcc)

    obj = App(pin, vcc, debug)
    try:
        obj.main()
    finally:
        logger.debug('finally')
        obj.end()

if __name__ == '__main__':
    main()
