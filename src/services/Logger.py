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
        self.filenameDebug = None
        self._open(module)
        
    def add(self, message, level, ex = None):
        """
        @Param level: Can only be three cases.
                      -- SEVERE: Record into the normal log file and the error log file.
                      -- WARNING: Record into the normal log file.
                      -- INFO: Record into the normal log file.
        @Param ex: Exception. If it is not None, append the exception after the message.
        """
        i = datetime.datetime.now()
        if ex:
            message += " Exception: "+ex
        if level == "SEVERE":
            gadget.write_file(self.filenameDebug, "{} {} {} {}:{}:{}---Messege: {}---Level: {}".format(str(i.year),str(i.month),str(i.day),str(i.hour),str(i.minute),str(i.second),str(message),str(level)), None)
        gadget.write_file(self.filename, "{} {} {} {}:{}:{}---Messege: {}---Level: {}".format(str(i.year),str(i.month),str(i.day),str(i.hour),str(i.minute),str(i.second),str(message),str(level)), None)

    def _open(self, module):
        i = datetime.datetime.now()
        self.module = module
        self.filename = "{}/debug/{}/{}_{}.log".format(Global.wwwPath, str(datetime.datetime.now().year)+str(datetime.datetime.now().month), datetime.datetime.now().day, self.module)
        gadget.write_file(self.filename, "-----Strat at: {} {} {} {}:{}:{}------Module: {}".format(str(i.year),str(i.month),str(i.day),str(i.hour),str(i.minute),str(i.second), str(module)), None)
        self.filenameDebug = "{}/debug/{}/{}_{}_{}.log".format(Global.wwwPath, str(datetime.datetime.now().year)+str(datetime.datetime.now().month), datetime.datetime.now().day, self.module,
         "DEBUG")
        gadget.write_file(self.filenameDebug, "-----Strat at: {} {} {} {}:{}:{}------Module: {}".format(str(i.year),str(i.month),str(i.day),str(i.hour),str(i.minute),str(i.second), str(module)), None)
        gadget.write_file(self.filenameDebug, "---------Record only SEVERE error--------", None)

    def close(self):
        i = datetime.datetime.now()
        gadget.write_file(self.filename, "End at: {} {} {} {}:{}:{}".format(str(i.year),str(i.month),str(i.day),str(i.hour),str(i.minute),str(i.second)), None)
        gadget.write_file(self.filenameDebug, "End at: {} {} {} {}:{}:{}".format(str(i.year),str(i.month),str(i.day),str(i.hour),str(i.minute),str(i.second)), None)

if __name__=="__main__":
    i = Logger("DEBUG")
    i.add("Test", "SEVERE", ex = "Meowuuuuuuu~~")
    i.close()