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
    OFF       = 0
    ON        = 1
    ONOFF     = [OFF, ON]
    ONOFF_STR = ['OFF', 'ON']

    def __init__(self, pin, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('pin=%d', pin)

        self.__pin = pin
        self.clear()

    @property
    def value(self):
        self.logger.debug('')
        return self.__value

    @value.setter
    def value(self, value):
        self.logger.debug('value=%s', value)
        self.__value = value

    def clear(self):
        self.logger.debug('')
        self.value = []

    def append_pulse(self, onoff, usec):
        if onoff not in self.ONOFF:
            raise ValueError('onoff[' + str(onoff)
                             + '] must be WaveForm.ON or WaveForm.OFF')
        if usec <= 0:
            raise ValueError('usec[' + str(usec) + '] must be > 0')
        self.logger.debug('onoff:%-3s, usec=%s', self.ONOFF_STR[onoff], usec)

        if onoff == self.ON:
            self.__value.append(pigpio.pulse(1 << self.__pin, 0, usec))
        else:
            self.__value.append(pigpio.pulse(0, 1 << self.__pin, usec))

    def append_pulse_list(self, onoff_list):
        '''
        onoff_list: 
          [on_usec1, off_usec1, on_usec2, off_usec2, ...]
        '''
        verr_msg = 'onoff_list:' + str(onoff_list) + ' must be int list'
        if type(onoff_list) != list:
            raise ValueError(verr_msg)
        if type(onoff_list[0]) != int:
            raise ValueError(verr_msg)
        self.logger.debug('onoff_list=%s', onoff_list)

        for i, usec in enumerate(onoff_list):
            if i % 2 == 0:
                self.append_pulse(self.ON, usec)
            else:
                self.append_pulse(self.OFF, usec)

    def append_pulse_list_n(self, onoff_list, n=1):
        verr_msg = 'n:' + str(n) + ' must be > 1'
        if n < 1:
            raise ValueError(verr_msg)
        self.logger.debug('onoff_list=%s, n=%d', onoff_list, n)

        for i in range(n):
            self.append_pulse_list(onoff_list)

#####
class Wave:
    def __init__(self, pi, pin, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('pin: %d', pin)

        self.pi  = pi
        self.pin = pin

        self.waveform = WaveForm(self.pin, debug=self.debug)
        self.wave     = None
        
        #self.pi.wave_add_new()

    def create(self):
        self.logger.debug('')

        self.pi.wave_add_generic(self.waveform.value)
        self.wave = self.pi.wave_create()
        return self.wave

    def delete(self):
        self.debug('')

        if self.wave is not None:
            self.pi.wave_delete(self.wave)

    
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
        

    def carrier(self, pin, freq_KHz, len_usec):
        """
        Generate carrier square wave.
        """
        self.logger.debug('pin:%d, freq_KHz:%d, len_usec:%d',
                          pin, freq_KHz, len_usec)
        wf = []
        wave_len_usec = 1000.0 / freq_KHz # = 1/(kHz*1000) * 1000 * 1000
        wave_n        = int(round(len_usec/wave_len_usec))
        on_usec       = int(round(wave_len_usec * self.DUTY))
        
        cur_usec = 0
        for i in range(wave_n):
            target_usec = int(round((i+1) * wave_len_usec))
            cur_usec    += on_usec
            off_usec    = target_usec - cur_usec
            cur_usec    += off_usec
            wf.append(pigpio.pulse(1 << pin, 0, on_usec))
            wf.append(pigpio.pulse(0, 1 << pin, off_usec))
            
            return wf
        
        
    def main(self):
        self.logger.debug('')

        self.carrier(self.pin, 0.002, 800000)
        
        self.pi.wave_add_new()

        wf1 = WaveForm(self.pin, debug=self.debug)
        wf1.append_pulse_list_n([200000, 100000, 100000, 300000], 3)
        wf1.append_pulse_list_n([800000, 300000], 3)
        wf1.append_pulse_list_n([200000, 300000], 3)
        self.pi.wave_add_generic(wf1.value)
        q1 = self.pi.wave_create()
        
        wf2 = WaveForm(self.pin, debug=self.debug)
        wf2.append_pulse(WaveForm.OFF, 1000000)
        self.pi.wave_add_generic(wf2.value)
        q2 = self.pi.wave_create()

        w3 = Wave(self.pi, self.pin, debug=self.debug)
        w3.waveform.append_pulse_list([500000, 500000])
        q3 = w3.create()

        w4 = Wave(self.pi, self.pin, debug=self.debug)
        w4.waveform.append_pulse_list([500000, 1500000])
        q4 = w4.create()

        while True:
            print('a')
            #self.pi.wave_send_once(q1)
            self.pi.wave_chain([q1, q2, q3, q4])
            print('b')
            while self.pi.wave_tx_busy():
                print('.', end='')
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
