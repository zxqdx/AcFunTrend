'''
Created on Nov 24, 2013

@author: BigMoe
'''

import gadget
import datetime


class Logger(object):

    '''
    classdocs
    '''

    def __init__(self, module):
        '''
        Constructor
        '''
        self.module = module
        self.time = datetime.datetime.now()
        self.filename = None

    def add(self, massage, level):
        if isinstance(massage, Exception):

            gadget.write_file(self.filename, str(massage) + str(level))
