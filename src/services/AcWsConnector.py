'''
Created on Nov 24, 2013

@author: zxqdx
'''

# Imports parent directory to sys.path
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ServiceLocker import ServiceLocker
from Logger import Logger
import pymysql


class AcWsConnector(object):

    """
    The Wrapper class for this module.
    """

    def __init__(self):
    	self.name = "AcWsConnector"
    	self.logger = Logger(self.name)
    	try:
	    	self.serviceLocker = ServiceLocker(self.name)
	    	self.serviceLocker.acquire()
	    except:
	    	self.logger.add("Unable to initialize {}. Maybe another instance is already running".format(self.name), "SEVERE")
        self.acWsSender = AcWsSender()
        self.acWsReceiver = AcWsReceiver()


class AcWsSender(object):

    """
    The sender that is responsible for sending requests.
    """

    def __init__(self, arg):
        super(AcWsSender, self).__init__()
        self.arg = arg


class AcWsReceiver(object):

    """
    The receiver that is responsible for receiving requests and saving them to database.
    """

    def __init__(self, arg):
        super(AcWsReceiver, self).__init__()
        self.arg = arg
