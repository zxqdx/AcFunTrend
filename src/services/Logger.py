'''
Created on Nov 24, 2013

@author: BigMoe
'''
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from miscellaneous import gadget
import datetime
# import GLobal
class Logger(object):
    '''
    classdocs
    物怪
    '''


    def __init__(self, module):
        '''
        Constructor
        '''
        self.module = None
        self.filename = None
        self._open(module)
        
    def add(self, message, level):
        if isinstance(message, Exception):
            gadget.write_file(self.filename, str(datetime.datetime.now()) + "Meowu!")
        else:
            gadget.write_file(self.filename, str(datetime.datetime.now())+"---Messege: "+str(message)+"-----Level: "+str(level))

    def _open(self, module):
        self.module = module
        self.filename = "{}/debug/{}/{}_{}.log".format("Glabal.wwwPath", str(datetime.datetime.now().year)+str(datetime.datetime.now().month), datetime.datetime.now().day, self.module)
        gadget.write_file(self.filename, "-----------Start at "+str(datetime.datetime.now())+"--------Module: "+str(self.module))

    def close(self):
        gadget.write_file(self.filename, "End at "+ str(datetime.datetime.now()))

    
i = Logger("Ma")
