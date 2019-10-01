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
    def __init__(self, pin, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('pin: %d', pin)

        self.pin = pin

        self.pi = pigpio.pi()
        self.pi.set_mode(self.pin, pigpio.OUTPUT)

    def main(self):
        self.logger.debug('')

        for i in range(2):
            self.pi.write(self.pin, 1)
            time.sleep(1)
            self.pi.write(self.pin, 0)
            time.sleep(1)

    def end(self):
        self.logger.debug('')

        self.pi.stop()
        
#####
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('pin', type=int, default=20)
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
