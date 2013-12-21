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
        """
        Constructor
        """
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
        if ex:
            message += " Exception: " + str(ex)
        if level == "SEVERE":
            gadget.write_file(self.filenameDebug, "[{}] {}".format(self._time(), message), None)
        gadget.write_file(self.filenameDebug, "[{}] <{}> {}".format(self._time(), level, message), None)

    def _time(self):
        i = datetime.datetime.now()
        return "{}-{}-{} {}:{}:{}".format(i.year, i.month, i.day, i.hour, i.minute, i.second)

    def _open(self, module):
        i = datetime.datetime.now()
        self.module = module
        self.filename = "{}/debug/{}/{}_{}.log".format(Global.wwwPath, i.year + i.month, i.day, self.module)
        self.filenameDebug = "{}/debug/{}/{}_{}_err.log".format(Global.wwwPath, str(i.year) + str(i.month),
                                                                i.day, self.module)
        gadget.write_file(self.filename, "-----Start at: {}------".format(self._time()), None)
        gadget.write_file(self.filenameDebug, "-----Start at: {}------".format(self._time()), None)

    def close(self):
        gadget.write_file(self.filename, "End at: {}".format(self._time()), None)
        gadget.write_file(self.filenameDebug, "End at: {}".format(self._time()), None)


if __name__=="__main__":
    i = Logger("DEBUG")
    i.add("Test", "SEVERE", ex = "Meowuuuuuuu~~")
    i.close()