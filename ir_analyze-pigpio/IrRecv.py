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
        
        self.receiving = False
        self.raw_data = []

    def set_watchdog(self, ms):
        self.logger.debug('ms=%d', ms)

        self.pi.set_watchdog(self.pin, ms)

    def _cb(self, pin, val, tick):
        self.logger.debug('pin: %d, val: %d, tick: %d', pin, val, tick)

        if not self.receiving:
            self.logger.debug('ignore')
            return
        
        interval  = tick - self.tick
        self.tick = tick
        
        if val == pigpio.TIMEOUT:
            self.set_watchdog(self.WATCHDOG_CANCEL)
            
            if len(self.raw_data) > 0:
                if len(self.raw_data[-1]) == 1:
                    self.raw_data[-1].append(interval)
            self.receiving = False
            self.logger.debug ('end   %d', interval)
            return

        if interval > self.INTERVAL_MAX:
            interval = self.INTERVAL_MAX

        self.set_watchdog(self.WATCHDOG_MSEC)

        if val == self.VAL_ON:
            if self.raw_data != []:
                self.raw_data[-1].append(interval)
        else:
            self.raw_data.append([interval])
            
        self.logger.debug('%s %d' % (self.VAL_STR[val], interval))

    def recv(self):
        self.logger.debug('')

        self.raw_data   = []
        self.receiving = True

        self.cb = self.pi.callback(self.pin, pigpio.EITHER_EDGE, self._cb)

        self.logger.info('Ready')
        while self.receiving:
            time.sleep(0.1)

        self.cb.cancel()
        self.logger.info('Done')

        return self.raw_data

    def end(self):
        self.logger.debug('')
        self.cb.cancel()
        self.pi.stop()
        self.logger.debug('done')
        
    def raw2pulse_space(self, raw_data=None):
        self.logger.debug('row_data=%s', raw_data)
        
        if raw_data is None:
            raw_data = self.raw_data
            self.logger.debug('raw_data=%s', raw_data)

        pulse_space = ''
        
        for (p, s) in raw_data:
            pulse_space += '%s %d\n' %(self.VAL_STR[0], p)
            pulse_space += '%s %d\n' %(self.VAL_STR[1], s)

        return pulse_space
            

    def print_pulse_space(self, raw_data=None):
        self.logger.debug('raw_data=%s', raw_data)

        if raw_data is None:
            raw_data = self.raw_data
            self.logger.debug('raw_data=%s', raw_data)

        print(self.raw2pulse_space(raw_data))
        

    def main(self):
        self.logger.debug('')

        while True:
            print('# -')
            raw_data = self.recv()
            self.print_pulse_space(raw_data)
            print('# /')
            time.sleep(.5)

#####
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS,
               help='IR signal receiver')
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
