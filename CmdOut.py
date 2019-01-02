#!/usr/bin/python3 -u
#
# (c) Yoichi Tanibayashi
#
import sys
import subprocess
import threading
import queue
import time
import click

#
# CmdOut class
#
class CmdOut(threading.Thread):
    def __init__(self, cmd):
        self.cmd = cmd
        self.lineq = queue.Queue()
        self.proc = subprocess.Popen(self.cmd,
                                     universal_newlines=True, bufsize=0, 
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
        super().__init__()

    def run(self):
        while True:
            try:
                line = self.proc.stdout.readline()
                if not line:
                    break
                self.lineq.put(line)
            except:
                break

    def __del__(self):
        pass

    def readline(self, timeout=0.6):
        try:
            line = self.lineq.get(block=True, timeout=timeout)
        except queue.Empty:
            line = None
        return line

    def close(self):
        self.proc.terminate()
        self.proc.wait()

#
# main
#
@click.command(help='exec <command> and readline from it : ex. \'ls -l\'')
@click.argument('cmd', metavar='<command>', type=str, nargs=1)
@click.option('--monitor', '-m', 'monitor', is_flag=True, default=False,
              help='monitor mode')
@click.option('--filter', '-f', 'filter', type=str, default='',
              help='filter string')
def main(cmd, monitor, filter):
    cmd = cmd.split()
    print('command =', cmd)

    read_timeout = 5
    sleep_time = 1
    lines_max = 5

    if monitor:
        read_timeout=0.6
        sleep_time = 0
        
    f = CmdOut(cmd)
    f.start()

    l_num = 0
    while True:
        line = f.readline(timeout = read_timeout)
        if not line:
            if monitor:
                continue
            break
        line = line.rstrip()
        
        if filter != '':
            found_flag = False
            for w in filter.split():
                if w in line:
                    found_flag = True
                else:
                    found_flag = False
                    break
            if found_flag:
                print(line)
            continue
            
        l_num += 1
        data = line.split()
        print('%5d\t%s' % (l_num, str(data)))
        if not monitor and l_num >= lines_max:
            break
        time.sleep(sleep_time)

    f.close()
    f.join()

if __name__ == '__main__':
    main()
