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
def main(cmd):
    cmd = cmd.split()
    print('command =', cmd)

    f = CmdOut(cmd)
    f.start()

    l_num = 0
    while True:
        line = f.readline(timeout = 5)
        if not line:
            break
        l_num += 1
        line = line.rstrip()
        data = line.split()
        print('%5d\t%s' % (l_num, str(data)))
        if l_num >= 5:
            break
        time.sleep(1)

    f.close()
    f.join()

if __name__ == '__main__':
    main()
