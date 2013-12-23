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

from miscellaneous import gadget
import threading
import pymysql
import datetime
import time
import json


class AcWsConnector(threading.Thread):
    """
    The Wrapper class for this module.
    """

    def __init__(self):
        threading.Thread.__init__(self, name="AcWsConnector")

        # Initializes the service.
        self.logger = Logger(self.name)
        try:
            self.serviceLocker = ServiceLocker(self.name)
            self.serviceLocker.acquire()
        except Exception as e:
            self.logger.add("Unable to initialize {}. Maybe another instance is already running.".format(self.name),
                            "SEVERE", ex=e)
            raise e

        # Connects to AcFun WebSocket.
        self.logger.add("Connecting to AcFun WebSocket...")
        from websocket import create_connection

        try:
            self.ws = create_connection(Global.AcFunAPIWsUrl)
        except Exception as e:
            self.logger.add("Failed to connect to AcFun WebSocket.", "SEVERE", ex=e)
        self.logger.add("Authenticating...")
        self.ws.send('{{func:"auth","key":"{}","secret":"{}"}}'.format(Global.AcFunAPIWsKey, Global.AcFunAPIWsSecret))
        try:
            result = json.loads(self.ws.recv())
            if result["success"]:
                self.logger.add("Authenticate complete.")
            else:
                raise Exception("Connection maintains but authenticate failed.")
        except Exception as e:
            self.logger.add("Failed to authenticate.", "SEVERE", ex=e)

        # Sets up threads.
        self.logger.add("Setting up threads.")
        self.acWsSender = AcWsSender(self.logger, self.ws)
        self.acWsReceiver = AcWsReceiver(self.logger, self.ws)
        self.acWsSender.daemon = True
        self.acWsReceiver.daemon = True

    def run(self):
        # Starts threads.
        self.logger.add("Starting threads...")
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

        # Close when interruption or exception occurs.
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

    def __init__(self, logger, ws):
        threading.Thread.__init__(self, name="AcWsSender")
        self.logger = logger
        self.ws = ws
        try:
            self.logger.add("Connecting to MYSQL {}:{}. DB={}. User={}...".format(Global.mysqlHost, Global.mysqlPort,
                                                                                  Global.mysqlAcWsConnectorDB,
                                                                                  Global.mysqlUser))
            self.conn = pymysql.connect(host=Global.mysqlHost, port=Global.mysqlPort, user=Global.mysqlUser,
                                        passwd=Global.mysqlPassword, db=Global.mysqlAcWsConnectorDB)
            self.cursor = self.conn.cursor()
        except Exception as e:
            self.logger.add("Failed to connect {} database. Please check the status of MYSQL service.".format(
                Global.mysqlAcWsConnectorDB), "SEVERE", ex=e)
            raise e

    def run(self):
        while True:
            # Processes the AcWs Queue.
            self.logger.add("Processing the AcWs Queue...")
            requestList = []
            try:
                # Gets the next 100 requests from ACWS Queue.
                self.logger.add("Fetching the next 100 requests from ACWS Queue...")
                self.cursor.execute(
                    'SELECT request_id, func, id, requested FROM trend_acws_queue WHERE requested=0 ORDER BY priority LIMIT 100')
                newRequestList = self.cursor.fetchall()
                self.logger.add("Fetched {} requests".format(len(newRequestList)))
                requestList.extend(newRequestList)

                # Gets all the timed out requests.
                self.logger.add("Fetching all  the timed out requests...")
                self.cursor.execute(
                    'SELECT request_id, func, id, retry_num, max_retry_num, priority FROM trend_acws_queue WHERE requested=1 and expire_time<{}'.format(
                        gadget.datetime_to_timestamp))
                timedOutRequestList = self.cursor.fetchall()

                # Retries the request if retryNum <= maxRetryNum. Abandons if retryNum > maxRetryNum.
                for eachTimedOutRequest in timedOutRequestList:
                    if eachTimedOutRequest[3] <= eachTimedOutRequest[4]: # Retries.
                        requestList.append((eachTimedOutRequest[0], eachTimedOutRequest[1], eachTimedOutRequest[2], 1))
                        self.logger.add(
                            "Retries request: func={}, id={}".format(eachTimedOutRequest[1], eachTimedOutRequest[2]),
                            "WARNING")
                    else: # Abandons.
                        self.cursor.execute(
                            'DELETE FROM trend_acws_queue WHERE request_id={}'.format(eachTimedOutRequest[0]))
                        self.logger.add(
                            "Abandoned request: func={}, id={}".format(eachTimedOutRequest[1], eachTimedOutRequest[2]),
                            "WARNING")
            except Exception as e:
                self.logger.add("Error occurs during processing the AcWs Queue.", "SEVERE", ex=e)
                raise e

            # Sends the request and updates AcWs Queue.
            for eachRequest in requestList:
                # Sends the request.
                self.logger.add(
                    "Sending request {}: func={}, id={}, requested={} ...".format(eachRequest[0], eachRequest[1],
                                                                                  eachRequest[2], eachRequest[3]))
                try:
                    self.ws.send(
                        '{{func:"{}",id:"[]",requestId:"AcTr-{}"}}'.format(eachRequest[1], eachRequest[2],
                                                                           eachRequest[0]))
                except Exception as e:
                    self.logger.add(
                        "Error occurs while sending request {}: func={}, id={}".format(eachRequest[0], eachRequest[1],
                                                                                       eachRequest[2]), "SEVERE", ex=e)
                    raise e
                # Updates AcWs Queue.
                self.logger.add("Updating AcWs Queue ...")
                try:
                    d = datetime.datetime.now()
                    if eachRequest[3] == 0: # New request.
                        self.cursor.execute(
                            'UPDATE trend_acws_queue SET request_date="{}", request_time={}, expire_time={}, retry_num=0, max_retry_num={}, requested=1 WHERE request_id={}'.format(
                                d.isoformat(), gadget.datetime_to_timestamp(d),
                                gadget.datetime_to_timestamp(d + datetime.timedelta(seconds=Global.AcFunAPIWsTimeout)),
                                Global.AcFunAPIWsRetryNum), eachRequest[0])
                    else: # Retry request.
                        self.cursor.execute(
                            'UPDATE trend_acws_queue SET request_date="{}", request_time={}, expire_time={}, retry_num=retry_num+1 WHERE request_id={}'.format(
                                d.isoformat(), gadget.datetime_to_timestamp(d),
                                gadget.datetime_to_timestamp(d + datetime.timedelta(seconds=Global.AcFunAPIWsTimeout)),
                                Global.AcFunAPIWsRetryNum), eachRequest[0])
                except Exception as e:
                    self.logger.add("Error occurs during updating the AcWs Queue.", "SEVERE", ex=e)
                    raise e

            time.sleep(Global.AcFunAPIWsCycleGap)


class AcWsReceiver(threading.Thread):
    """
    The receiver that is responsible for receiving requests and saving them to database.
    """

    def __init__(self, logger, ws):
        threading.Thread.__init__(self, name="AcWsReceiver")
        self.logger = logger
        self.ws = ws
        try:
            self.logger.add("Connecting to MYSQL {}:{}. DB={}. User={}...".format(Global.mysqlHost, Global.mysqlPort,
                                                                                  Global.mysqlAcWsConnectorDB,
                                                                                  Global.mysqlUser))
            self.conn = pymysql.connect(host=Global.mysqlHost, port=Global.mysqlPort, user=Global.mysqlUser,
                                        passwd=Global.mysqlPassword, db=Global.mysqlAcWsConnectorDB)
            self.cursor = self.conn.cursor()
        except Exception as e:
            self.logger.add("Failed to connect {} database. Please check the status of MYSQL service.".format(
                Global.mysqlAcWsConnectorDB), "SEVERE", ex=e)
            raise e

    def run(self):
        while True:
            result = self.ws.recv()
            self.logger.add("Received {}".format(result))
            time.sleep(Global.AcFunAPIWsCycleGap)


if __name__ == "__main__":
    acWsConnector = AcWsConnector()
    acWsConnector.start()