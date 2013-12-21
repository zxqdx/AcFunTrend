'''
Created on Nov 24, 2013

@author: zxqdx
'''

# Imports parent directory to sys.path
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import Global
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
        except Exception as e:
            self.logger.add("Unable to initialize {}. Maybe another instance is already running.".format(self.name), "SEVERE", ex=e)
            raise e
        self.acWsSender = AcWsSender(self.logger)
        self.acWsReceiver = AcWsReceiver(self.logger)

    def run(self):
        self.acWsSender.run()
        # self.acWsReceiver.run()

    def close(self):
        try:
            self.serviceLocker
        except Exception as e:
            self.logger.add("Unable to close {}. Maybe another instance is already running.".format(self.name), "SEVERE", ex=e)
            raise e


class AcWsSender(threading.Thread):

    """
    The sender that is responsible for sending requests.
    """
    def __init__(self, logger):
        self.logger = logger
        try:
            self.connAcWs = pymysql.connect(host=Global.mysqlHost, port=Global.mysqlPort, user=Global.mysqlUser, passwd=Global.mysqlPassword, db=Global.mysqlAcWsConnectorDB)
            self.cursorAcWs = self.connAcWs.cursor()
        except Exception as e:
            self.logger.add("Failed to connect {} database. Please check the status of MYSQL service.".format(Global.mysqlAcWsConnectorDB), "SEVERE", ex=e)
            raise e

    def run(self):

        pass



class AcWsReceiver(object):

    """
    The receiver that is responsible for receiving requests and saving them to database.
    """

    def __init__(self, logger, mysqlAcWs):
        self.logger = logger
        try:
            self.connAcWs = pymysql.connect(host=Global.mysqlHost, port=Global.mysqlPort, user=Global.mysqlUser, passwd=Global.mysqlPassword, db=Global.mysqlAcWsConnectorDB)
            self.cursorAcWs = self.connAcWs.cursor()
        except Exception as e:
            self.logger.add("Failed to connect {} database. Please check the status of MYSQL service.".format(Global.mysqlAcWsConnectorDB), "SEVERE", ex=e)
            raise e
    def run(self):
        pass