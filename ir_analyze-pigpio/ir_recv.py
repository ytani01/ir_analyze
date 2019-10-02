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
DEF_PIN = 27

#####
class App:
    BOUNCE_USEC = 10
    INTERVAL_MAX = 99999
    VAL_ON = 0
    VAL_OFF = 1

    def __init__(self, pin, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('pin: %d', pin)

        self.pin = pin
        self.tick = 0

        self.pi = pigpio.pi()
        self.pi.set_mode(self.pin, pigpio.INPUT)
        
        self.cb = self.pi.callback(self.pin, pigpio.EITHER_EDGE, self._cb)

    def main(self):
        self.logger.debug('')

        while True:
            self.logger.debug('*')
            time.sleep(5)

    def _cb(self, pin, val, tick):
        self.logger.debug('pin: %d, val: %d, tick: %d', pin, val, tick)
        if tick - self.tick < self.BOUNCE_USEC:
            self.logger.debug('ignore')
            return

        interval = tick - self.tick
        
        if interval > self.INTERVAL_MAX:
            interval = self.INTERVAL_MAX

        if val == self.VAL_ON:
            header = 'space'
        else:
            header = 'pulse'
            
        print('%s %d' % (header, interval))
        self.tick = tick

    def end(self):
        self.logger.debug('')
        self.cb.cancel()
        self.pi.stop()
        self.logger.debug('done')
        
#####
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('pin', type=int, default=27)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(pin, debug):
    logger = my_logger.get_logger(__name__, debug)
    logger.debug('pin: %d', pin)

    obj = App(pin, debug)
    try:
        obj.main()
    finally:
        logger.debug('finally')
        obj.end()

if __name__ == '__main__':
    main()
