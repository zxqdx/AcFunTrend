"""
Created on Nov 24, 2013

@author: zxqdx
"""

# Imports parent directory to sys.path
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ServiceLocker import ServiceLocker
from Logger import Logger
import Global

import threading
import pymysql
import time


class AcWsConnector(threading.Thread):
    """
    The Wrapper class for this module.
    """

    def __init__(self):
        threading.Thread.__init__(self, name="AcWsConnector")
        self.logger = Logger(self.name)
        try:
            self.serviceLocker = ServiceLocker(self.name)
            self.serviceLocker.acquire()
        except Exception as e:
            self.logger.add("Unable to initialize {}. Maybe another instance is already running.".format(self.name),
                            "SEVERE", ex=e)
            raise e
        self.acWsSender = AcWsSender(self.logger)
        self.acWsReceiver = AcWsReceiver(self.logger)
        self.acWsSender.daemon = True
        self.acWsReceiver.daemon = True

    def run(self):
        self.acWsReceiver.start()
        self.acWsSender.start()
        while True:
            interrupter = self.serviceLocker.is_interrupt()
            if interrupter:
                self.logger.add("The service is interrupted by {}.".format(interrupter), "SEVERE")
                break

            self.acWsReceiver.join(0.1)
            if not self.acWsReceiver.isAlive():
                self.logger.add("An error occurs in thread {}. The service is about to quit.".format("AcWsReceiver"),
                                "SEVERE")
                break
            self.acWsSender.join(0.1)

            if not self.acWsSender.isAlive():
                self.logger.add("An error occurs in thread {}. The service is about to quit.".format("AcWsSender"),
                                "SEVERE")
                break
            time.sleep(1)
        self.close()
        self.logger.close()

    def close(self):
        try:
            self.serviceLocker.release()
        except Exception as e:
            self.logger.add("Unable to close {}. Maybe another instance is already running.".format(self.name),
                            "SEVERE", ex=e)
            raise e


class AcWsSender(threading.Thread):
    """
    The sender that is responsible for sending requests.
    """

    def __init__(self, logger):
        threading.Thread.__init__(self, name="AcWsSender")
        self.logger = logger
        try:
            self.logger.add("Connecting to MYSQL {}:{}. DB={}. User={}...".format(Global.mysqlHost, Global.mysqlPort,
                                                                                  Global.mysqlAcWsConnectorDB,
                                                                                  Global.mysqlUser), "INFO")
            self.connAcWs = pymysql.connect(host=Global.mysqlHost, port=Global.mysqlPort, user=Global.mysqlUser,
                                            passwd=Global.mysqlPassword, db=Global.mysqlAcWsConnectorDB)
            self.cursorAcWs = self.connAcWs.cursor()
        except Exception as e:
            self.logger.add("Failed to connect {} database. Please check the status of MYSQL service.".format(
                Global.mysqlAcWsConnectorDB), "SEVERE", ex=e)
            raise e

    def run(self):
        while True:
            pass


class AcWsReceiver(threading.Thread):
    """
    The receiver that is responsible for receiving requests and saving them to database.
    """

    def __init__(self, logger):
        threading.Thread.__init__(self, name="AcWsReceiver")
        self.logger = logger
        try:
            self.logger.add("Connecting to MYSQL {}:{}. DB={}. User={}...".format(Global.mysqlHost, Global.mysqlPort,
                                                                                  Global.mysqlAcWsConnectorDB,
                                                                                  Global.mysqlUser), "INFO")
            self.connAcWs = pymysql.connect(host=Global.mysqlHost, port=Global.mysqlPort, user=Global.mysqlUser,
                                            passwd=Global.mysqlPassword, db=Global.mysqlAcWsConnectorDB)
            self.cursorAcWs = self.connAcWs.cursor()
        except Exception as e:
            self.logger.add("Failed to connect {} database. Please check the status of MYSQL service.".format(
                Global.mysqlAcWsConnectorDB), "SEVERE", ex=e)
            raise e

    def run(self):
        while True:
            pass


if __name__ == "__main__":
    acWsConnector = AcWsConnector()
    acWsConnector.start()