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
class WaveForm:
    ON  = 1
    OFF = 0

    def __init__(self, pin, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('pin: %d', pin)

        self.pin = pin
        self.clear()

    def clear(self):
        self.logger.debug('')
        self.wf = []

    def append(self, sw, usec):
        self.logger.debug('sw:%s, usec=%d', sw, usec)
        if sw == self.ON:
            self.wf.append(pigpio.pulse(1 << self.pin, 0, usec))
        else:
            self.wf.append(pigpio.pulse(0, 1 << self.pin, usec))

    def value(self):
        return self.wf
        

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

        wf1 = WaveForm(self.pin, debug=self.debug)
        wf1.append(WaveForm.ON,  200000)
        wf1.append(WaveForm.OFF, 800000)
        wf1.append(WaveForm.ON,  200000)
        wf1.append(WaveForm.OFF, 800000)
        print(wf1.value())

        wf2 = WaveForm(self.pin, debug=self.debug)
        wf2.append(WaveForm.ON,  1000000)
        wf2.append(WaveForm.OFF, 1000000)
        print(wf2.value())

        pulse_n =  self.pi.wave_add_generic(wf1.value())
        print('number of pulses: %d' % pulse_n)

        pulse_n =  self.pi.wave_add_generic(wf2.value())
        print('number of pulses: %d' % pulse_n)

        
        q1 = self.pi.wave_create()
        print(q1)

        while True:
            print('a')
            self.pi.wave_send_once(q1)
            print('b')
            while self.pi.wave_tx_busy():
                print('-', end='')
                time.sleep(0.1)
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

    app = IrSend(pin, debug)
    try:
        app.main()
    finally:
        logger.debug('finally')
        app.end()
        logger.debug('done')

if __name__ == '__main__':
    main()
