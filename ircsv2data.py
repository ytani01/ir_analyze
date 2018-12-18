#!/usr/bin/python3
#coding: utf-8

#convIrData.py

import sys
import json

def conv_command(command, block):
    str_tmp = ""
    int_tmp = []
    for i in range(int(len(block)/2)):
        str_tmp = block[i*2] + block[i*2+1]
        int_tmp.append( int(str_tmp, 16))

    list = []
    ir_data = {}
    data_numH = 0;
    data_numL = 0;
    for i in range(int(len(int_tmp)/4)):
         data_numH = (int_tmp[i*4+1] * 256 + int_tmp[i*4+0]) * 26
         data_numL = (int_tmp[i*4+3] * 256 + int_tmp[i*4+2]) * 26
         list.append(data_numH)
         list.append(data_numL)

    ir_data[command] = list
    print(command, list)
    return ir_data

    
while True:
    argvc = sys.argv
    argc = len(argvc)
           
    if  (argc  == 2):
        filename = sys.argv[1]
        f = open(filename, 'r', encoding='utf-8')
        ir_data = {}
        for line in f:
            line_data = line.replace('"', '').rsplit(',', 1)
            [command, block] = line_data
            ir_data.update(conv_command(command, block))

        #print(json.dumps(ir_data,sort_keys=True).replace("],","],\n"))
        break   

    if  (argc  == 3):
        command = sys.argv[1]
        block = sys.argv[2]

        ir_data = conv_command(command, block)
        print(json.dumps(ir_data))
        break   

    print("Usage:")
    print(" python3 convIrData.py filename")
    print(" python3 convIrData.py command \"5B0018002E001800...\"")
    break
