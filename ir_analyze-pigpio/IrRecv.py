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
import queue
import threading

#####
from MyLogger import MyLogger
my_logger = MyLogger(__file__)

#####
class IrRecv:
    GLITCH_USEC     = 250   # usec
    LEADER_MIN_USEC = 1000

    INTERVAL_MAX    = 999999 # usec

    WATCHDOG_MSEC   = INTERVAL_MAX / 1000    # msec
    WATCHDOG_CANCEL = 0

    VAL_ON          = 0
    VAL_OFF         = 1
    VAL_STR         = ['pulse', 'space', 'timeout']

    MSG_END         = ''
    
    def __init__(self, pin, glitch_usec=GLITCH_USEC, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, self.debug)
        self.logger.debug('pin=%d, glitch_usec=%d', pin, glitch_usec)

        self.pin = pin
        self.tick = 0

        self.pi = pigpio.pi()
        self.pi.set_mode(self.pin, pigpio.INPUT)
        self.pi.set_glitch_filter(self.pin, self.GLITCH_USEC)
        
        self.receiving = False
        self.raw_data = []

        self.msgq    = queue.Queue()

    def set_watchdog(self, ms):
        self.logger.debug('ms=%d', ms)
        self.pi.set_watchdog(self.pin, ms)

    def _cb(self, pin, val, tick):
        self.logger.debug('pin=%d, val=%d, tick=%d', pin, val, tick)

        if not self.receiving:
            self.logger.debug('reciving=%s .. ignore', self.receiving)
            return

        self.msgq.put([pin, val, tick])

        if val == pigpio.TIMEOUT:
            self.set_watchdog(self.WATCHDOG_CANCEL)
            self.cb.cancel()
            self.receiving = False

            self.msgq.put(self.MSG_END)

            self.logger.debug('timeout!')
            return

        self.set_watchdog(self.WATCHDOG_MSEC)
        
    def recv(self, verbose=False):
        self.logger.debug('')

        self.raw_data   = []
        self.receiving = True

        self.th_worker = threading.Thread(target=self.worker, daemon=True)
        self.th_worker.start()

        self.cb = self.pi.callback(self.pin, pigpio.EITHER_EDGE, self._cb)

        if verbose:
            print('Ready')
        while self.receiving:
            time.sleep(0.1)

        self.cb.cancel()
        self.th_worker.join()

        if verbose:
            print('Done')

        return self.raw_data

    def end(self):
        self.logger.debug('')
        self.cb.cancel()
        self.pi.stop()

        if self.th_worker.is_alive():
            self.msgq.put(self.MSG_END)
            self.logger.debug('join()')
            self.th_worker.join()
        
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

        print(self.raw2pulse_space(raw_data), end='')

    def worker(self):
        '''
        worker thread
        '''
        self.logger.debug('')

        while True:
            msg = self.msgq.get()
            self.logger.debug('msg=%s', msg)
            if msg == self.MSG_END:
                break

            self.proc_msg(msg)

        self.logger.debug('done')

    def proc_msg(self, msg):
        '''
        msg = [pin, val, tick]
        '''
        self.logger.debug('msg=%s', msg)

        if type(msg) != list:
            self.logger.waring('invalid msg:%s .. ignored', msg)
            return
        if len(msg) != 3:
            self.logger.waring('invalid msg:%s .. ignored', msg)
            return

        [pin, val, tick] = msg

        interval = tick - self.tick
        self.logger.debug('interval=%d', interval)
        self.tick = tick

        if val == pigpio.TIMEOUT:
            self.logger.debug('timeout!')
            if len(self.raw_data) > 0:
                if len(self.raw_data[-1]) == 1:
                    self.raw_data[-1].append(interval)
            self.logger.debug('end')
            return

        if interval > self.INTERVAL_MAX:
            interval = self.INTERVAL_MAX
            self.logger.debug('interval=%d', interval)

        if val == IrRecv.VAL_ON:
            if self.raw_data == []:
                '''
                if interval < self.INTERVAL_MAX:
                    self.logger.warning('%d: orphan space .. ignored',
                                        interval)
                '''
                self.logger.debug('start raw_data')
                return
            else:
                self.raw_data[-1].append(interval)

        else: # val == IrRecv.VAL_OFF
            if self.raw_data == [] and interval < self.LEADER_MIN_USEC:
                self.set_watchdog(self.WATCHDOG_CANCEL)
                self.logger.debug('%d: leader is too short .. ignored',
                                    interval)
                return
            else:
                self.raw_data.append([interval])

        self.logger.debug('raw_data=%s', self.raw_data)
            
#####
class App:
    def __init__(self, pin, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, self.debug)
        self.logger.debug('pin=%d', pin)

        self.r = IrRecv(pin, debug=self.debug)

    def main(self):
        self.logger.debug('')

        while True:
            print('# -')
            raw_data = self.r.recv(verbose=True)
            self.r.print_pulse_space(raw_data)
            print('# /')
            time.sleep(.5)

    def end(self):
        self.logger.debug('')
        self.r.end()

#####
DEF_PIN = 27

import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS,
               help='IR signal receiver')
@click.argument('pin', type=int, default=DEF_PIN)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(pin, debug):
    logger = my_logger.get_logger(__name__, debug)
    logger.debug('pin: %d', pin)

    app = App(pin, debug=debug)
    try:
        app.main()
    finally:
        logger.debug('finally')
        app.end()

if __name__ == '__main__':
    main()
