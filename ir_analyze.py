#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 日本語

import sys
import os
import re
import pprint

MYNAME		= os.path.basename(sys.argv[0])

SIG_LONG	= 59999

DEF_FACTOR	= 1.7
FIX_FACTOR	= 1.3

STAT_OK		= 0
STAT_UNKNOWN	= 1
STAT_WARN	= 10
STAT_ERR	= 100
stat_num	= STAT_OK

SIG_CH		= {
    'zero':	'0',
    'one':	'1',
    'leader': 	'-',
    'trailer':	'/',
    'repeat':	'*',
    'misc':	'?'
    }
SIG_CH_01	= SIG_CH['zero'] + SIG_CH['one']

#####
## usage
def usage():
    print()
    print('Usage:')
    print()
    print('$ sudo service lircd stop')
    print('$ mode2 | tee filename')
    print('< Push remocon button(s) >')
    print('[Ctrl]-[C]')
    print('$ %s filename [factor]' % MYNAME)
    print()


## sig[][] -> sig_raw[]
def sig_to_sig_raw(sig):
    sig_raw = []

    for idx in range(len(sig['pulse'])):
        sig_raw.append(sig['pulse'][idx])
        try:
            sig_raw.append(sig['space'][idx])
        except IndexError:
            break

    return sig_raw


## get_mode
def get_mode(data, step):
    #if len(data) <= 20:
    #    print('  data[] =', data)

    data2 = [d for d in data]

    if len(data2) <= 5:
        return int(round(sum(data2) / len(data2)))
    
    data2.remove(min(data2))
    data2.remove(max(data2))
    
    n = int((max(data2) - min(data2)) / step) + 1
    freq_list = [0] * n
    sum_list = [0] * n
    for  d in data2:
        idx = int((d - min(data2)) / step)
        freq_list[idx] += 1
        sum_list[idx] += d

    #if len(freq_list) <= 20:
    #    print('  freq_list[] =', freq_list)
    idx = freq_list.index(max(freq_list))
    ret = sum_list[idx] / freq_list[idx]
    return int(round(ret))


## mk_sig_str
def mk_sig_str(sig_list, ir_sig):
    sig_str = ''
    for [t1, t2] in sig_list:
        sig_str += SIG_CH[ir_sig[t1, t2]]

    return sig_str
    
## print bit pattern
def print_bit_pattern(sig_list, prefix='', msb_first=True):
    for line in sig_list:
        print(prefix, end='')
        for s in line:
            if s[0] in SIG_CH_01:
                if msb_first:
                    s = s[::-1]
                s = re.sub('(\d{8})', '\\1 ', s)
                s = s.strip()
                s = s[::-1]
            print(s + ' ', end='')
        print()

## print hex code
def print_hex_code(sig_list, prefix='', msb_first=True):
    for line in sig_list:
        print(prefix, end='')
        for s in line:
            if s[0] in SIG_CH_01:
                if not msb_first:
                    s = s[::-1]
                hex_len = int(len(s) / 4 + 0.99)
                s = ('0' * hex_len + '%X' % int(s, 2))[-hex_len:]
            print(s + ' ', end='')
        print()

## decode signal
def decode_signal(sig_list):
    print('## MSB first')

    ## print bit pattern
    print('# bit pattern: MSB first')
    print_bit_pattern(sig_list, '#BIT:MSB ', True);

    ## print hex code
    print('# Hex code: MSB first')
    print_hex_code(sig_list, '#HEX:MSB ', True)

    print('## LSB first')

    ## print bit pattern
    print('# bit pattern: LSB first')
    print_bit_pattern(sig_list, '#BIT:LSB ', False)

    ## print hex code
    print('# Hex code: LSB first')
    print_hex_code(sig_list, '#HEX:LSB ', False)
    

##### main
def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        usage()
        exit(1)

    filename = sys.argv[1]
    factor = DEF_FACTOR
    if len(sys.argv) == 3:
        factor = float(sys.argv[2])

    with open(filename, "r") as f:
        line = f.readline()
        while not 'space ' in line:
            line = f.readline()
            if not line:
                sys.exit(1)

        sig_raw = []
        sig = { 'pulse': [], 'space': [] }
        for line in f:
            [key, value] = line.split()
            v = int(value)
            if int(v) > SIG_LONG:
                v = SIG_LONG
            sig[key].append(int(v))

    sig_raw = sig_to_sig_raw(sig)

    #print(sig)
    #print(min(sig['pulse']), min(sig['space']))

    # normalize
    sig_t = {'pulse': [[], []], 'space': [[], []]}
    sig_mode = {'pulse': [], 'space': []}

    for key in ['pulse', 'space']:
        stat_num = STAT_UNKNOWN
        while stat_num != STAT_OK:
            stat_num = STAT_OK

            sig_t[key] = [[], [], []]
            sig2 = []
            for s in sig[key]:
                if s < min(sig[key]) * factor:
                    sig_t[key][0].append(s)
                else:
                    sig2.append(s)

            for s in sig2:
                if s < min(sig2) * factor:
                    sig_t[key][1].append(s)
                else:
                    sig_t[key][2].append(s)

            #print('sig_t[%s]=' % key, sig_t[key])
        
            sig_mode[key] = []
            for idx in range(len(sig_t[key])):
                if len(sig_t[key][idx]) > 0:
                    print('# [%s] sig_t[%s][%d] = (%d-%d)' % (key, key, idx,
                                                            min(sig_t[key][idx]), max(sig_t[key][idx])))
                    #print(sig_t[key][idx])
                    #print()
                
                    sig_mode[key].append(get_mode(sig_t[key][idx], 50))

            print('# [%s] sig_mode[%s][0] = %d' % (key, key, sig_mode[key][0]))

            ## check
            t0_min = min(sig_t[key][0])
            t0_max = max(sig_t[key][0])
            t1_min = min(sig_t[key][1])
            t1_max = max(sig_t[key][1])
            
            if t0_max * FIX_FACTOR > t1_min:
                print('# [%s] ! Error! %d, %d' % (key, t0_max, t1_min))
                stat_num = STAT_ERR

                ## fix sig[]
                print('# [%s] * Fix data: ' % key, end='')
                idx = sig[key].index(t0_min)
                print('%d->%d  ' % (sig[key][idx], sig_mode[key][0]), end='')
                sig[key][idx] = sig_mode[key][0]

                idx = sig[key].index(t1_min)
                print('%d<-%d  ' % (t0_max, sig[key][idx]), end='')
                sig[key][idx] = t0_max
                print()
                
                stat_num = STAT_UNKNOWN
                print()

    if stat_num != STAT_OK:
        print('! Error[%d]' % stat_num)
        sys.exit(1)

    #print('# mode value: ', [ sig_mode['pulse'][0], sig_mode['space'][0] ])

    sig_raw = sig_to_sig_raw(sig)

    sig_normalize = []
    key = 'pulse'
    for t in sig_raw:
        sig_normalize.append(round(t / sig_mode[key][0]))
        if key == 'pulse':
            key = 'space'
        else:
            key = 'pulse'

    #print('sig_normailze =', sig_normalize)
    
    ## is sony ?
    sony_type = False
    '''
    if sig_normalize[0] >= 3 and sig_normalize[0] <= 5 and sig_normalize[1] == 1:
        ## SONY type
        print('SONY type !')
        sony_type = True
        sig_raw.insert(0, SIG_LONG)
        if  sig_raw[-1] == SIG_LONG:
            sig_raw.pop(-1)
            sig_normalize.pop(-1)
        #print('sig_raw =', sig_raw)
        sig_normalize.insert(0, round(SIG_LONG / sig_mode['space'][0]))
        #print('sig_normalize =', sig_normalize)
    '''
    if len(sig_raw) % 2 != 0:
        sig_raw.append(SIG_LONG)
        sig_normalize.append(round(SIG_LONG / sig_mode['space'][0]))

    #print('sig_normailze =', sig_normalize)
        
    ## sig pair
    sig_normalize_pair = []
    while len(sig_normalize) > 0:
        sig_normalize_pair.append([sig_normalize.pop(0), sig_normalize.pop(0)])
    #print('sig_normalize_pair =')
    #print(sig_normalize_pair)

    sig_ptn = sorted(list(map(list, set(map(tuple, sig_normalize_pair)))))
    print('## sig_ptn =', sig_ptn)

    ## sig_ptn_raw
    idx = 0
    sig_ptn_raw = {}
    for [t1, t2] in sig_normalize_pair:
        v1 = sig_raw[idx]
        v2 = sig_raw[idx + 1]
        #print(t1, t2, v1, v2)
        sig_ptn_raw['pulse', t1] = sig_ptn_raw.get(('pulse', t1), [])
        sig_ptn_raw['space', t2] = sig_ptn_raw.get(('space', t2), [])
        sig_ptn_raw['pulse', t1].append(v1)
        sig_ptn_raw['space', t2].append(v2)
        idx += 2

    sig_key = ''
    for [s, t] in sorted(sig_ptn_raw.keys()):
        if s != sig_key:
            sig_key = s
            print('## [%s]' % sig_key)
        print('### %dT = %d' % (t, get_mode(sig_ptn_raw[s, t], 50)))
        #pprint.pprint(sig_ptn_raw[s, t], width=80, indent=2, compact=True)
    

    ## 度数分布
    sig_ptn_freq_dist = []
    for p in sig_ptn:
        sig_ptn_freq_dist.append([p, 0])
    #print('sig_ptn_freq_dist =', sig_ptn_freq_dist)
    
    for [p, s] in sig_normalize_pair:
        for idx in range(len(sig_ptn)):
            if p == sig_ptn[idx][0] and s == sig_ptn[idx][1]:
                sig_ptn_freq_dist[idx][1] += 1
    #print('sig_ptn_freq_dist =', sig_ptn_freq_dist)

    def freq_dist(t1, t2):
        for idx in range(len(sig_ptn_freq_dist)):
            t1a = sig_ptn_freq_dist[idx][0][0]
            t2a = sig_ptn_freq_dist[idx][0][1]
            num = sig_ptn_freq_dist[idx][1]
            if t1 == t1a and t2 == t2a:
                return num

    #print('# sig_ptn =', sig_ptn)
    #print('# ', [[t1 * sig_mode['pulse'][0], t2 * sig_mode['space'][0]] for [t1, t2] in sig_ptn])

    
    ## 信号パターン判定
    sig_ptn_work = sig_ptn[:]
    
    # 'leader'
    t1a = sig_normalize_pair[0][0]
    t2a = sig_normalize_pair[0][1]
    ir_sig = {}
    ir_sig[t1a, t2a] = 'leader'
    sig_ptn_work.remove([t1a, t2a])
    
    # '0'
    ir_sig[1,1] = 'zero'
    try:
        sig_ptn_work.remove([1, 1])
    except ValueError:
        print('!! Error: [1, 1]: not found')
        sys.exit(1)
    
    # '1'
    sig_ptn_a = sig_ptn_work[:]
    for [t1, t2] in sig_ptn_a:
        if ( t1 == 1 and t2 >= 2 and t2 <= 4) or ( t1 >= 2 and t1 <= 4 and t2 == 1 ):
            ir_sig[t1, t2] = 'one'
            sig_ptn_work.remove([t1, t2])

    # 'leader'
    sig_ptn_a = sig_ptn_work[:]
    for [t1, t2] in sig_ptn_a:
        if t1 > 2 and abs(t1 - t1a) <= 1 and abs(t2 - t2a) <= 1:
            ir_sig[t1, t2] = 'leader'
            sig_ptn_work.remove([t1, t2])

    # 'trailer'
    sig_ptn_a = sig_ptn_work[:]
    for [t1, t2] in sig_ptn_a:
        if (t1 == 1 and t2 >= 6) or t2 > 100:
            ir_sig[t1, t2] = 'trailer'
            sig_ptn_work.remove([t1, t2])

    # repeat?
    sig_ptn_a = sig_ptn_work[:]
    for [t1, t2] in sig_ptn_a:
        if t1 >= 2 and t2 >= 2:
            ir_sig[t1, t2] = 'repeat'
            sig_ptn_work.remove([t1, t2])

    # '?'
    sig_ptn_a = sig_ptn_work[:]
    for [t1, t2] in sig_ptn_a:
        ir_sig[t1, t2] = 'misc'
        sig_ptn_work.remove([t1, t2])

    # reverse 
    ir_sig_name = {}
    for [t1, t2] in ir_sig.keys():
        sig_name = ir_sig[t1, t2]
        ir_sig_name[sig_name] = ir_sig_name.get(sig_name, [])
        ir_sig_name[sig_name].append([t1, t2])
    #print(ir_sig_name)

    ## print signal pattern
    for sig_name in ['leader', 'zero', 'one', 'trailer', 'repeat', 'misc']:
        print('# [%s]%-8s: ' % (SIG_CH[sig_name], sig_name), end='')
        for [t1, t2] in ir_sig_name.get(sig_name, []):
            print('%dT+%dT * %d\t' % (t1, t2, freq_dist(t1, t2)), end='')
        print()
    
    ## フォーマット判定
    print('## IR Format = ', end='')

    fmt = '???'
    for [t1, t2] in ir_sig_name['one']:
        if (t1 == 2 or t1 == 3) and t2 == 1:
            fmt = 'SONY'
            break
        if t1 == 1 and t2 >= 3 and t2 <= 5:
            for [t11, t22] in ir_sig_name['leader']:
                if t11 >= 13 and t11 <= 17 and t22 >= 7 and t22 <= 10:
                    fmt = 'NEC'
                    break
                if t11 >= 7 and t11 <= 9 and t22 >= 3 and t22 <= 5:
                    fmt = 'AEHA'
                    break
            if fmt != '???':
                break
            for [t11, t22] in ir_sig_name.get('repeat', []):
                if t11 >= 12 and t22 <= 8:
                    fmt = 'NEC?'
                
    print(fmt)
                
    
    ## make signal string list
    sig_str = mk_sig_str(sig_normalize_pair, ir_sig)
    sig_line = re.sub(SIG_CH['leader'], ' '+SIG_CH['leader'], sig_str).split()
    sig_list = []
    for l in sig_line:
        sig_list.append(re.sub('(\D)', ' \\1 ', l).split())

    decode_signal(sig_list)

    #print(sig_list)
    
    print('### for SONY Type: -1 bit decoding')
    for idx1 in range(len(sig_list)):
        for idx2 in range(len(sig_list[idx1])):
            if sig_list[idx1][idx2][0] in SIG_CH_01:
                if len(sig_list[idx1][idx2]) > 1:
                    sig_list[idx1][idx2] = sig_list[idx1][idx2][:-1]

    #print(sig_list)
    decode_signal(sig_list)
    
    ## print lirc.conf raw codes
    print('# raw codes')
    count = 0
    nl_flag = True
    if sony_type:
        sig_raw.pop(0)
        sig_raw.append(SIG_LONG)
        #print(sig_raw)

    sig_sum = 0
    for [t1, t2] in sig_normalize_pair:
        sym = SIG_CH[ir_sig[t1, t2]]
        v1 = sig_raw.pop(0)
        v2 = sig_raw.pop(0)
        sig_sum += v1 + v2

        if sym in SIG_CH_01:
            print('%4d %4d ' % (v1, v2), end='')
            nl_flag = False
            count += 1
            if count >= 8:
                print()
                nl_flag = True
                count = 0
        else:
            if not nl_flag:
                print()
                
            print('%4d %4d ' % (v1, v2))
            nl_flag = True
            count = 0

            if v2 == SIG_LONG:
                sig_sum -= SIG_LONG
            #print('[%d]' % sig_sum)
            sig_sum = 0
            
        # print(t1, t2, '', end='')

    print()


#####
if __name__ == '__main__':
    main()
