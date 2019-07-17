#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#

__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN
console_handler = StreamHandler()
console_handler.setLevel(DEBUG)
handler_fmt = Formatter(
    '%(asctime)s %(levelname)s %(name)s.%(funcName)s> %(message)s',
    datefmt='%H:%M:%S')
console_handler.setFormatter(handler_fmt)
logger = getLogger(__name__)
logger.setLevel(INFO)
logger.addHandler(console_handler)
logger.propagate = False

def get_logger(name, debug):
    l = logger.getChild(name)
    if debug:
        l.setLevel(DEBUG)
    else:
        l.setLevel(INFO)
    return l

