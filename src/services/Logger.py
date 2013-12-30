"""
Created on Nov 24, 2013

@author: BigMoe
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import traceback
import datetime

from miscellaneous import gadget
import Global


class Logger(object):
    """
    物怪
    """

    def __init__(self, module):
        """
        Constructor
        """
        self.previousTime = ""
        self.indent = "  "
        self.module = None
        self.filename = None
        self.filenameDebug = None
        self.err = False
        self._open(module)

    def add(self, message, level="DETAIL", ex=None):
        """
        @Param level: Can only be three cases.
                      -- SEVERE: Record into the normal log file and the error log file.
                      -- WARNING: Record into the normal log file.
                      -- INFO: Record into the normal log file.
        @Param ex: Exception. If it is not None, append the exception after the message.
        """
        currentTime = self._time()
        toConsole = Global.isDebug and level!="DETAIL"
        if self.previousTime!=currentTime:
            gadget.write_file(self.filename, "[{}]".format(currentTime), None, toConsole=Global.isDebug)
            self.previousTime = currentTime
        if ex:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            message += "\n{}Exception: ".format(self.indent) + str(ex)
            message += "\n{}Traceback: \n".format(self.indent)
            extractTB = traceback.extract_tb(exc_traceback)
            for x in range(len(extractTB)):
                message += self.indent + repr(extractTB[x]).strip("(").strip(")").strip("'") + "\n"
        if level == "SEVERE":
            gadget.write_file(self.filenameDebug, "[{}]".format(currentTime), None)
            gadget.write_file(self.filenameDebug, self.indent + message, None)
        gadget.write_file(self.filename, "{}<{}> {}".format(self.indent, level, message), None, toConsole=toConsole)

    @staticmethod
    def _time():
        i = datetime.datetime.now()
        return "{}-{}-{} {:02d}:{:02d}:{:02d}".format(i.year % 100, i.month, i.day, i.hour, i.minute, i.second)

    def _open(self, module):
        i = datetime.datetime.now()
        self.module = module
        self.filename = "{}/debug/{}-{:02d}/{:02d}_{}.{}".format(Global.wwwPath, i.year, i.month, i.day,
                                                                 self.module, Global.logFileSuffix)
        self.filenameDebug = "{}/debug/{}-{:02d}/{:02d}_{}_err.{}".format(Global.wwwPath, i.year, i.month,
                                                                          i.day, self.module, Global.logFileSuffix)
        gadget.write_file(self.filename, "-----Start at: {}------".format(self._time()), None)

    def close(self):
        """
        It is okay to skip this method...
        """
        gadget.write_file(self.filename, "-----End at: {}-----".format(self._time()), None)


if __name__ == "__main__":
    i = Logger("DEBUG")
    i.add("Test", "SEVERE", ex="Meowuuuuuuu~~")
    i.close()