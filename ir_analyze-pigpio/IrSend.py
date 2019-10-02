#!/usr/bin/env -S python3 -u
#
# (c) 2019 Yoichi Tanibayashi
#
'''
IrSend.py

'''
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'

import pigpio
import time

#####
from MyLogger import MyLogger
my_logger = MyLogger(__file__)

#####
DEF_PIN = 22

#####
class IrSend:
    FREQ = 38000      # 38KHz
    DUTY = (1 / 3.0)  # 33.3%

    def __init__(self, pin, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('pin: %d', pin)

        self.pin = pin
        self.tick = 0

        self.pi = pigpio.pi()
        self.pi.set_mode(self.pin, pigpio.OUTPUT)

    def send(self, sig):
        self.logger.debug('')

    def end(self):
        self.logger.debug('')
        self.pi.wave_clear()
        self.pi.stop()
        self.logger.debug('done')
        
    def print_signal(self, signal):
        self.logger.debug('signal:%s', signal)

        for i, interval in enumerate(self.signal):
            print('%s %d' % (self.VAL_STR[i % 2], interval))
        
    def main(self):
        self.logger.debug('')

        self.pi.wave_add_new()

        p1 = []
        p1.append(pigpio.pulse(1 << self.pin, 0, 300000))
        p1.append(pigpio.pulse(0, 1 << self.pin, 700000))
        p1.append(pigpio.pulse(1 << self.pin, 0, 300000))
        p1.append(pigpio.pulse(0, 1 << self.pin, 700000))
        print(p1)
        
        self.pi.wave_add_generic(p1)
        q1 = self.pi.wave_create()
        print(q1)

        while True:
            print('a')
            self.pi.wave_send_once(q1)
            print('b')
            while self.pi.wave_tx_busy():
                print('-', end='')
                time.sleep(0.05)
            print()
        

#####
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('pin', type=int, default=DEF_PIN)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(pin, debug):
    logger = my_logger.get_logger(__name__, debug)
    logger.debug('pin: %d', pin)

    obj = IrSend(pin, debug)
    try:
        obj.main()
    finally:
        logger.debug('finally')
        obj.end()

if __name__ == '__main__':
    main()
