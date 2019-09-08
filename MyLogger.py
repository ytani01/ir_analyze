#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN

class MyLogger:
    def __init__(self, name=''):
        self.handler_fmt = Formatter(
            '%(asctime)s %(levelname)s %(name)s.%(funcName)s> %(message)s',
            datefmt='%H:%M:%S')

        self.console_handler = StreamHandler()
        self.console_handler.setLevel(DEBUG)
        self.console_handler.setFormatter(self.handler_fmt)

        self.logger = getLogger(name)
        self.logger.setLevel(INFO)
        self.logger.addHandler(self.console_handler)
        self.logger.propagate = False

    def get_logger(self, name, debug):
        l = self.logger.getChild(name)
        if debug:
            l.setLevel(DEBUG)
        else:
            l.setLevel(INFO)
        return l

#####
my_logger = MyLogger(__file__)

class Sample:
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, self.debug)
        self.logger.debug('debug = %s', self.debug)

    def main(self):
        self.logger.debug('')
        self.logger.info('hello, world.')

    def end(self):
        self.logger.debug('')
        

import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(debug):
    logger = my_logger.get_logger('main', debug)

    app = Sample(debug=debug)
    try:
        app.main()
    finally:
        app.end()

if __name__ == '__main__':
    main()
