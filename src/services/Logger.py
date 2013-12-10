'''
Created on Nov 24, 2013

@author: BigMoe
'''
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from miscellaneous import gadget
import datetime

import Global
class Logger(object):

    """
    物怪
    """

    def __init__(self, module):
        '''
        Constructor
        '''
        self.module = None
        self.filename = None
        self._open(module)
        
    def add(self, message, level):
        """
        @Param level: Can only be three cases.
                      -- SEVERE: Record into the normal log file and the error log file.
                      -- WARNING: Record into the normal log file.
                      -- INFO: Record into the normal log file.
        """
        if isinstance(message, Exception):
            gadget.write_file(self.filename, str(datetime.datetime.now()) + "Meowu!", None)
        else:
            gadget.write_file(self.filename, str(datetime.datetime.now()) + "---Messege: " + str(message) + "-----Level: " + str(level), None)

    def _open(self, module):
        self.module = module
        self.filename = "{}/debug/{}/{}_{}.log".format(Global.wwwPath, str(datetime.datetime.now().year)+str(datetime.datetime.now().month), datetime.datetime.now().day, self.module)
        gadget.write_file(self.filename, "-----------Start at "+str(datetime.datetime.now())+"--------Module: "+str(self.module), None)

    def close(self):
        gadget.write_file(self.filename, "End at "+ str(datetime.datetime.now()), None)

if __name__=="__main__":
    i = Logger("Ma")
    i.add("Test", "DEBUG")
    i.close()