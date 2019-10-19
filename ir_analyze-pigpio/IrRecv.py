#!/usr/bin/python3 -u
#
# (c) 2019 Yoichi Tanibayashi
#
'''
IrRecv.py

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
class IrRecv:
    GLITCH_USEC     = 100   # usec

    INTERVAL_MAX    = 999999 # usec

    WATCHDOG_MSEC   = INTERVAL_MAX / 1000    # msec
    WATCHDOG_CANCEL = 0

    VAL_ON          = 0
    VAL_OFF         = 1
    VAL_STR         = ['pulse', 'space', 'timeout']

    def __init__(self, pin, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('pin: %d', pin)

        self.pin = pin
        self.tick = 0

        self.pi = pigpio.pi()
        self.pi.set_mode(self.pin, pigpio.INPUT)
        self.pi.set_glitch_filter(self.pin, self.GLITCH_USEC)
        
        self.cb = self.pi.callback(self.pin, pigpio.EITHER_EDGE, self._cb)

        self.receving = False
        self.signal = []

    def set_watchdog(self, ms):
        self.logger.debug('ms=%d', ms)

        self.pi.set_watchdog(self.pin, ms)

    def _cb(self, pin, val, tick):
        self.logger.debug('pin: %d, val: %d, tick: %d', pin, val, tick)

        if not self.receving:
            self.logger.debug('ignore')
            return
        
        interval  = tick - self.tick
        self.tick = tick
        
        if val == pigpio.TIMEOUT:
            self.signal.append(interval)
            self.set_watchdog(self.WATCHDOG_CANCEL)
            self.receving = False
            self.logger.debug ('end   %d', interval)
            return

        if interval > self.INTERVAL_MAX:
            interval = self.INTERVAL_MAX

        self.set_watchdog(self.WATCHDOG_MSEC)

        if val == self.VAL_ON:
            if self.signal != []:
                self.signal.append(interval)
        else:
            self.signal.append(interval)
            
        self.logger.debug('%s %d' % (self.VAL_STR[val], interval))

    def recv(self):
        self.logger.debug('')

        self.signal   = []
        self.receving = True

        while self.receving:
            time.sleep(0.1)

        return self.signal

    def end(self):
        self.logger.debug('')
        self.cb.cancel()
        self.pi.stop()
        self.logger.debug('done')
        
    def print_signal(self, signal):
        self.logger.debug('signal:%s', signal)

        for i, interval in enumerate(self.signal):
            print('%s %d' % (self.VAL_STR[i % 2], interval))
        

    def main(self):
        self.logger.debug('')

        while True:
            print('# -')
            signal = self.recv()
            self.print_signal(signal)
            print('# /')
            time.sleep(1)

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

    obj = IrRecv(pin, debug)
    try:
        obj.main()
    finally:
        logger.debug('finally')
        obj.end()

if __name__ == '__main__':
    main()
