#!/usr/bin/python3 -u
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
        
        self.pin = pin
        self.waveform = []
        
    def clear(self):
        self.logger.debug('')
        self.waveform = []

    def append_null(self, usec):
        self.waveform.append(pigpio.pulse(0, 0, usec))

    def append_pulse(self, onoff, usec):
        if onoff not in self.ONOFF:
            raise ValueError('onoff[' + str(onoff)
                             + '] must be WaveForm.ON or WaveForm.OFF')
        if usec <= 0:
            raise ValueError('usec[' + str(usec) + '] must be > 0')
        self.logger.debug('onoff:%-3s, usec=%s', self.ONOFF_STR[onoff], usec)

        if onoff == self.ON:
            self.waveform.append(pigpio.pulse(1 << self.pin, 0, usec))
        else:
            self.waveform.append(pigpio.pulse(0, 1 << self.pin, usec))

    def append_pulse_list1(self, onoff_list):
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

    def append_pulse_list(self, onoff_list, n=1):
        verr_msg = 'n:' + str(n) + ' must be > 1'
        if n < 1:
            raise ValueError(verr_msg)
        self.logger.debug('onoff_list=%s, n=%d', onoff_list, n)

        for i in range(n):
            self.append_pulse_list1(onoff_list)

    def append_carrier(self, freq_KHz, duty, len_us):
        """
        append carrier wave.
        """
        self.logger.debug('freq_KHz:%d, len_us:%d', freq_KHz, len_us)

        wave_len_us = 1000000.0 / freq_KHz      # = 1/(Hz) * 1000 * 1000
        wave_n        = int(round(len_us/wave_len_us))
        on_usec       = int(round(wave_len_us * duty))
        self.logger.debug('wave_lan_usec: %d, wave_n: %d, on_usec: %d',
                          wave_len_us, wave_n, on_usec)
        
        cur_usec = 0
        for i in range(wave_n):
            target_usec = int(round((i+1) * wave_len_us))
            cur_usec    += on_usec
            off_usec    = target_usec - cur_usec
            cur_usec    += off_usec
            self.append_pulse_list1([on_usec, off_usec])
            
        
#####
class Wave(WaveForm):
    PIN_PWM = [12, 13, 18]

    def __init__(self, pi, pin, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('pin: %d', pin)

        self.pi  = pi
        self.pin = pin

        if pin in self.PIN_PWM:
            msg = 'pin:%d is one of PWM audio pins:%s' % (pin, self.PIN_PWM)
            raise ValueError(msg)
        
        super().__init__(self.pin, debug=self.debug)
        self.wave     = None
        
        #self.pi.wave_add_new()

    def create_wave(self):
        self.logger.debug('len(waveform): %d', len(self.waveform))

        self.pi.wave_add_generic(self.waveform)
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

        self.pulse_wave_hash = {}
        self.space_wave_hash = {}


    def send(self, dev_name, btn_name):
        self.logger.debug('dev_name: %s, btn_name: %s', dev_name, btn_name)

    def end(self):
        self.logger.debug('')
        self.clear_wave_hash()
        self.pi.wave_clear()
        self.pi.stop()
        self.logger.debug('done')
        
    def print_signal(self, signal):
        self.logger.debug('signal:%s', signal)

        for i, interval in enumerate(self.signal):
            print('%s %d' % (self.VAL_STR[i % 2], interval))


    def clear_wave_hash(self):
        self.logger.debug('')
        self.clear_pulse_wave_hash()
        self.clear_space_wave_hash()

    def create_pulse_wave1(self, usec):
        self.logger.debug('usec: %d', usec)
        wave = Wave(self.pi, self.pin, debug=self.debug)
        wave.append_carrier(self.FREQ, self.DUTY, usec)
        return wave.create_wave()

    def clear_pulse_wave_hash(self):
        self.logger.debug('')

        for usec in self.pulse_wave_hash:
            self.pi.wave_delete(self.pulse_wave_hash[usec])

        self.pulse_wave_hash = {}
        
    def create_pulse_wave(self, usec):
        self.logger.debug('usec: %d', usec)

        if usec not in self.pulse_wave_hash:
            self.pulse_wave_hash[usec] = self.create_pulse_wave1(usec)
            self.logger.debug('pulse_wave_hash: %s', self.pulse_wave_hash)

        return self.pulse_wave_hash[usec]


    def clear_space_wave_hash(self):
        self.logger.debug('')

        for usec in self.space_wave_hash:
            self.pi.wave_delete(self.space_wave_hash[usec])

        self.space_wave_hash = {}
        
    def create_space_wave1(self, usec):
        self.logger.debug('usec: %d', usec)
        wave = Wave(self.pi, self.pin, debug=self.debug)
        wave.append_null(int(round(usec)))
        return wave.create_wave()
    
    def create_space_wave(self, usec):
        self.logger.debug('usec: %d', usec)

        if usec not in self.space_wave_hash:
            self.space_wave_hash[usec] = self.create_space_wave1(usec)
            self.logger.debug('space_wave_hash: %s', self.space_wave_hash)

        return self.space_wave_hash[usec]

    
    def send_ir_pulse_space(self, sig):
        self.logger.debug('sig: %s', sig)

        if len(sig) <= 10:
            self.logger.warning("sig is too short: %s .. ignored", sig)
            return

        self.clear_wave_hash()
        w = []

        total_us = 0
        for i, us in enumerate(sig):
            total_us += us
            
            if i % 2 == 0:
                w.append(self.create_pulse_wave(us))
            else:
                w.append(self.create_space_wave(us))
        self.logger.debug('total_us: %d', total_us)

        self.pi.wave_chain(w)
        '''
        sleep_sec = (total_us / 1000.0 / 1000.0) + 0.5
        self.logger.debug('sleep_sec: %f', sleep_sec)
        time.sleep(sleep_sec)
        '''
        wait_tick = ''
        while self.pi.wave_tx_busy():
            wait_tick += '*'
            time.sleep(0.01)
        self.logger.debug('wait_tick: %s', wait_tick)
        time.sleep(0.1)

    def button_info2pulse_space(self, button_info, button_name):
        '''
        button_info = {
          "header": {
            "T": us
            "sig_tbl": {
              "-": [n, n],
              "=": [n, n],
              "0": [n, n],
              "1": [n, n],
              "/": [n, n],
              "*": [n, n],
              "?": [n, n]
            },
            "macro": {
              "P": "hex",
              "Q": "hex"
            }
          },
          "buttons": {
            "button1": "-P(hex)Q/*/*/",
            "button2": "- P (hex) /",
            "button3": ["-", "(hex)", "Q", "/", "*/", "*/"]
            :
          }
        }
        '''
        self.logger.debug("button_info=%s, button_name=%s",
                          button_info, button_name)

        #
        # sig_list -> sig_str
        # リスト構造を単一文字列に変換
        #
        sig_str = ''

        sig_list = button_info['buttons'][button_name]
        self.logger.debug("sig_list=%s", sig_list)

        if type(sig_list) == str:
            sig_str = sig_list
        elif type(sig_list) == list:
            for s in sig_list:
                self.logger.debug("s=%s", s)
                sig_str += s
        else:
            self.logger.error("invalid sig_list: %s", sig_list)
            return []

        self.logger.debug("sig_str=%s", sig_str)

        #
        # マクロ(prefix, postfix etc.)展開
        #
        for ch in sig_str:
            if ch in button_info['header']['macro']:
                sig_str = sig_str.replace(ch,
                                          button_info['header']['macro'][ch])
                self.logger.debug("sig_str=%s", sig_str)

        #
        # スペース削除
        #
        sig_str = sig_str.replace(' ', '')
        
        #
        # hex -> bin
        #
        bin_str = ''
        for ch in sig_str:
            if ch in '0123456789ABCDEF':
                bin_str += format(int(ch, 16), '04b')
            else:
                bin_str += ch
            self.logger.debug("bin_str=%s", bin_str)
        
        #
        # make pulse,space list
        #
        pulse_space_list = []
        t0 = button_info['header']['T']
        for ch in bin_str:
            sig = button_info['header']['sig_tbl'][ch][0]
            pulse_space_list.append(sig[0] * t0)
            pulse_space_list.append(sig[1] * t0)
        self.logger.debug('pulse_space_list=%s', pulse_space_list)
        
        return pulse_space_list


    def send_ir(self, button_info, button_name):
        self.logger.debug('button_info=%s, button_name=%s',
                          button_info, button_name)

        pulse_space = self.button_info2pulse_space(button_info, button_name)
        self.logger.debug("pulse_space=%s", pulse_space)

        self.send_ir_pulse_space(pulse_space)
        

    def sample(self):
        '''
        for test and sample
        '''
        self.logger.debug('')

        self.pi.wave_add_new()

        '''
        wf0 = []
        wf0.append(pigpio.pulse(1 << self.pin, 0, 500000))
        wf0.append(pigpio.pulse(0, 1 << self.pin, 800000))
        wf0.append(pigpio.pulse(1 << self.pin, 0, 500000))
        wf0.append(pigpio.pulse(0, 1 << self.pin, 800000))
        self.pi.wave_add_generic(wf0)
        q0 = self.pi.wave_create()

        wf1 = WaveForm(self.pin, debug=self.debug)
        wf1.append_pulse(WaveForm.ON,  300000)
        wf1.append_pulse(WaveForm.OFF, 800000)
        wf1.append_pulse_list([300000, 800000, 300000, 800000])
        self.pi.wave_add_generic(wf1.waveform)
        q1 = self.pi.wave_create()
        
        w1 = Wave(self.pi, self.pin, debug=self.debug)
        w1.append_pulse(WaveForm.ON,  100000)
        w1.append_pulse(WaveForm.OFF, 500000)
        w1.append_pulse_list([100000, 500000, 300000, 500000], 2)
        w1.append_pulse(WaveForm.OFF, 1000000)
        q2 = w1.create_wave()
        
        w2 = Wave(self.pi, self.pin, debug=self.debug)
        w2.append_carrier(3, self.DUTY, 1.51 *1000*1000)
        w2.append_null(500000)
        q3 = w2.create_wave()

        w3 = Wave(self.pi, self.pin, debug=self.debug)
        w3.append_carrier(self.FREQ, self.DUTY, 0.07185526 *1000*1000)
        # ↑
        # 0.71...をこれより大きくすると create_wave() できない？
        w3.append_null(1500000)
        q4 = w3.create_wave()


        self.clear_wave_hash()
        q5 = []
        q5.append(self.create_pulse_wave(0.05 *1000*1000))
        q5.append(self.create_space_wave(0.5 *1000*1000))
        q5.append(self.create_pulse_wave(0.03 *1000*1000))
        q5.append(self.create_space_wave(0.5 *1000*1000))
        q5.append(self.create_pulse_wave(0.03 *1000*1000))
        q5.append(self.create_space_wave(1 *1000*1000))

        while True:
            print('-')
            #self.pi.wave_chain([q0, q1, q2, q3])
            #self.pi.wave_send_once(q4)
            #self.pi.wave_chain(q5)

            print('/')
            while self.pi.wave_tx_busy():
                print('.', end='')
                time.sleep(0.1)
            print()
        '''
        
        self.clear_wave_hash()
        q6 = []

        # tv-light power
        u1 = [9050,  4525,
              565,   565,   565,   565,   565,   565,   565,   565,
              565,   565,   565,   565,   565,   565,   565,   565,
              565,  1696,   565,  1696,   565,  1696,   565,  1696,
              565,  1696,   565,  1696,   565,  1696,   565,  1696,
              565,   565,   565,   565,   565,   565,   565,   565,
              565,   565,   565,   565,   565,  1696,   565,   565,
              565,  1696,   565,  1696,   565,  1696,   565,  1696,
              565,  1696,   565,  1696,   565,   565,   565,  1696,
              565, 39593,
              9050,  2262,
              565]

        '''
        # ball-lamp on
        u1 = [8933,  4466,
                558,   558,   558,   558,   558,   558,   558,   558,
                558,   558,   558,   558,   558,   558,   558,   558,
                558,  1675,   558,  1675,   558,  1675,   558,  1675,
                558,   558,   558,  1675,   558,  1675,   558,  1675,
                558,  1675,   558,  1675,   558,   558,   558,   558,
                558,   558,   558,   558,   558,   558,   558,   558,
                558,   558,   558,   558,   558,  1675,   558,  1675,
                558,  1675,   558,  1675,   558,  1675,   558,  1675,
                558, 40760,
               8933,  2233,
                558, 60303,
               8933,  4466,
                558,   558,   558,   558,   558,   558,   558,   558,
                558,   558,   558,   558,   558,   558,   558,   558,
                558,  1675,   558,  1675,   558,  1675,   558,  1675,
                558,   558,   558,  1675,   558,  1675,   558,  1675,
                558,  1675,   558,  1675,   558,   558,   558,   558,
                558,   558,   558,   558,   558,   558,   558,   558,
                558,   558,   558,   558,   558,  1675,   558,  1675,
                558,  1675,   558,  1675,   558,  1675,   558,  1675,
                558, 39643,
               8933,  2233,
                558]
        '''

        bi_tv_light = {
            "header": {
                "name": "dev_name",
                "memo": "memo",
                "format": "NEC",
                "T": 565.625,
                "sig_tbl": {
                    "-": [
                        [
                            16,
                            8
                        ]
                    ],
                    "=": [],
                    "0": [
                        [
                            1,
                            1
                        ]
                    ],
                    "1": [[1,3]],
                    "/": [[1,70],  [1,763],[1,1768]],
                    "*": [[16,4]],
                    "?": []
                },
                "macro": {
                    "P": "00FF",
                    "Q": ""
                }
            },
            "buttons": {
                "button": [
                    "-",
                    "P 02FD",
                    "/",
                    "*",
                    "/",
                    "-",
                    "P 22DD",
                    "/",
                    "*",
                    "/"
                ]
            }
        }

        bi_aircon ={
            "header": {
                "name": "dev_name",
                "memo": "memo",
                "format": "AEHA",
                "T": 417.66161616161617,
                "sig_tbl": {
                    "-": [
                        [
                            8,
                            4
                        ]
                    ],
                    "=": [],
                    "0": [
                        [
                            1,
                            1
                        ]
                    ],
                    "1": [
                        [
                            1,
                            3
                        ]
                    ],
                    "/": [
                        [
                            1,
                            2395
                        ]
                    ],
                    "*": [],
                    "?": []
                },
                "macro": {
                    "P": "-28C6 0008 08",
                    "Q": "7F 900C 8",
                    "R": "80 0000 0000 047"
                }
            },
            "buttons": {
                "off":     ["P 40BF/"],
                "on_cool_25": ["PQ 9 R 8 /"],
                "on_cool_26": ["PQ 5 R 0 /"],
                "on_cool_27": ["PQ D R F /"],
                "on_cool_28": ["PQ 3 R 7 /"],
                "button2": ["P Q 0980 4000 R/"]
            }
        }

        
        '''
        while True:
            self.logger.debug('send')
            #self.send_ir_pulse_space(u1)
            self.send_ir(bi1, "button")
            print('-', end='')
            time.sleep(3)
        '''
        self.logger.debug('send')
        #self.send_ir(bi_aircon, "button1")
        self.send_ir(bi_aircon, "on_cool_25")
        time.sleep(3)
        self.send_ir(bi_aircon, "off")
        


#####
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS,
               help='IR signal transmitter')
@click.argument('pin', type=int, default=DEF_PIN)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(pin, debug):
    logger = my_logger.get_logger(__name__, debug)
    logger.debug('pin: %d', pin)

    app = IrSend(pin, debug)
    try:
        app.sample()
    finally:
        logger.debug('finally')
        app.end()
        logger.debug('done')

if __name__ == '__main__':
    main()
