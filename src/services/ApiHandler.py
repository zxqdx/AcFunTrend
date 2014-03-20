"""
Created on March 7, 2014

@author: zxqdx
"""

# Imports parent directory to sys.path
import os
import sys
import threading
import time
import datetime
import json

import pymysql

from ServiceLocker import ServiceLocker
from Logger import Logger
import Global
from miscellaneous import gadget


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ApiHandler(threading.Thread):
    """
    The wrapper class for this module.
    """

    def __init__(self):
        threading.Thread.__init__(self, name="ApiHandler")
        self.logger = Logger(self.name);
        try:
            self.serviceLocker = ServiceLocker(self.name)
            self.serviceLocker.acquire()
        except Exception as e:
            self.logger.add("Unable to initialize {}. Maybe another instance is already running.".format(self.name),
                            "SEVERE", ex=e)
            raise e

        self.queue = {"paused": False, "feedback": [False for _ in range(Global.TrendAPIPoolNum)]}
        for k in range(Global.TrendAPIPoolNum):
            self.queue[k] = {}

        # Sets up threads.
        self.logger.add("Setting up threads.", "DEBUG")
        self.apiPoolHandler = ApiPoolHandler(self.queue)
        self.apiPoolHandler.daemon = True
        self.apiQueueHandlerDict = {}
        for k in range(Global.TrendAPIPoolNum):
            self.apiQueueHandlerDict[k] = ApiQueueHandler(self.queue, k)
            self.apiQueueHandlerDict[k].daemon = True

    def run(self):
        # Starts threads.
        self.logger.add("Starting threads...", "DEBUG")
        self.apiPoolHandler.start()
        for k in range(Global.TrendAPIPoolNum):
            self.apiQueueHandlerDict[k].start()
        while True:
            interrupter = self.serviceLocker.is_interrupt()
            if interrupter:
                self.logger.add("The service is interrupted by {}.".format(interrupter), "SEVERE")
                break

            if not self.apiPoolHandler.isAlive():
                self.logger.add("An error occurs in thread {}. The service is about to quit.".format("apiPoolHandler"),
                                "SEVERE")
                break

            isBreak = False
            for k in range(Global.TrendAPIPoolNum):
                if not self.apiQueueHandlerDict[k].isAlive():
                    self.logger.add("An error occurs in thread {}. "
                                    "The service is about to quit.".format("ApiQueueHandler" + k), "SEVERE")
                    isBreak = True
                    break
            if isBreak: break

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


class ApiPoolHandler(threading.Thread):
    """
    The handler that deals with each specific connection pools.
    """

    def __init__(self, queue, poolId):
        threading.Thread.__init__(self, name="ApiPoolHandler" + poolId)
        self.logger = Logger(self.name)
        self.queue = queue
        self.poolId = poolId
        try:
            self.logger.add("Connecting to MYSQL {}:{}. DB={}. User={} ...".format(Global.mysqlHost, Global.mysqlPort,
                                                                                   Global.mysqlApiDB,
                                                                                   Global.mysqlUser), "DEBUG")
            self.conn = pymysql.connect(host=Global.mysqlHost, port=Global.mysqlPort, user=Global.mysqlUser,
                                        passwd=Global.mysqlPassword, db=Global.mysqlApiDB)
            self.conn.set_charset(Global.mysqlEncoding)
            self.cursor = self.conn.cursor()
            self.cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
        except Exception as e:
            self.logger.add("Failed to connect {} database. Please check the status of MYSQL service.".format(
                Global.mysqlApiDB), "SEVERE", ex=e)
            raise e

    def escape_string(self, s):
        return self.conn.escape_string(s)

    def generate_result(self, success, content):
        if success:
            return {"success": True, "content": content}
        else:
            return {"success": False, "content": {"query": False, "reason": content}}

    def run(self):
        while True:
            try:
                # Check paused.
                if self.queue["paused"]:
                    self.logger.add("Pause request found.")
                    self.queue["feedback"][self.poolId] = True
                    while self.queue["paused"]: time.sleep(0.5)
                # Fetch one query.
                self.logger.add("Fetching one query...")
                currentQuery = None
                isFound = False
                for eachPriority in sorted(self.queue[self.poolId].keys()):
                    for eachQuery in self.queue[self.poolId][eachPriority]:
                        eachQueryInfo = self.queue[self.poolId][eachPriority][eachQuery]
                        if not eachQueryInfo["finished"]:
                            currentQuery = eachQuery
                            isFound = True
                            break
                    if isFound: break
                if isFound:
                    # Fetch the result of query.
                    self.logger.add("Fetching the result for {}".format(currentQuery), "DEBUG")
                    eachQueryOrder, eachQueryParam = eachQuery.split("?")
                    if eachQueryOrder == "1_1_1":
                        pass
                    elif eachQueryOrder == "1_2_1":
                        # TODO MARK.

                        pass
                    else:
                        resultJson = self.generate_result(False, "无法识别请求类型。")
                        self.logger.add("Unrecognized query order {}.".format(eachQueryOrder), "WARNING")

                    # Store the result into cache.
                    self.logger.add("Storing the result into cache.")
                    self.cursor.execute('SELECT query FROM trend_api_cache '
                                        'WHERE query="{}"'.format(self.escape_string(eachQuery)))
                    if self.cursor.rowcount > 0:
                        self.cursor.execute('UPDATE trend_api_cache SET '
                                            'expire_time={}, result="{}" WHERE '
                                            'query="{}"'.format(gadget.datetime_to_timestamp(
                            datetime.datetime.now() + datetime.timedelta(seconds=eachQueryTimeout)),
                                                                self.escape_string(json.dumps(resultJson)),
                                                                self.escape_string(currentQuery)))
                    else:
                        self.cursor.execute('INSERT INTO trend_api_cache(query, expire_time, result) '
                                            'VALUES ("{}", {}, "{}")'.format(self.escape_string(eachQuery),
                                                                             gadget.datetime_to_timestamp(
                                                                                 datetime.datetime.now()
                                                                                 + datetime.timedelta(
                                                                                     seconds=eachQueryTimeout)),
                                                                             self.escape_string(
                                                                                 json.dumps(resultJson))));
                    # Delete query from queue.
                    self.logger.add("Deleting query from queue.")
                    self.cursor.execute('DELETE FROM trend_api_queue '
                                        'WHERE query="{}"'.format(self.escape_string(currentQuery)))
                    # Change the status of query.
                    self.queue[self.poolId][eachPriority][currentQuery]["finished"] = True
            except Exception as e:
                self.logger.add("Unknown error occurred.", "SEVERE", ex=e)
                break
            time.sleep(Global.TrendAPIQueryCycle)


class ApiQueueHandler(threading.Thread):
    """
    The handler that maintains ApiHandler.queue
    """

    def __init__(self, queue):
        threading.Thread.__init__(self, name="ApiQueueHandler")
        self.logger = Logger(self.name)
        self.count = 1
        self.queue = queue
        try:
            self.logger.add("Connecting to MYSQL {}:{}. DB={}. User={} ...".format(Global.mysqlHost, Global.mysqlPort,
                                                                                   Global.mysqlApiDB,
                                                                                   Global.mysqlUser), "DEBUG")
            self.conn = pymysql.connect(host=Global.mysqlHost, port=Global.mysqlPort, user=Global.mysqlUser,
                                        passwd=Global.mysqlPassword, db=Global.mysqlApiDB)
            self.conn.set_charset(Global.mysqlEncoding)
            self.cursor = self.conn.cursor()
            self.cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
        except Exception as e:
            self.logger.add("Failed to connect {} database. Please check the status of MYSQL service.".format(
                Global.mysqlApiDB), "SEVERE", ex=e)
            raise e

    def escape_string(self, s):
        return self.conn.escape_string(s)

    def acquire_lock(self):
        self.queue["paused"] = True
        locked = False
        while not locked:
            locked = True
            for eachPoolId in range(Global.TrendAPIPoolNum):
                locked = locked and self.queue["feedback"][eachPoolId]
            time.sleep(0.5)

    def release_lock(self):
        for eachPoolId in range(Global.TrendAPIPoolNum):
            self.queue["feedback"][eachPoolId] = False
        self.queue["paused"] = False

    def run(self):
        while True:
            try:
                if self.count % 500 == 0:
                    self.logger.add("Acquiring lock...")
                    self.acquire_lock()
                    # Clear cache.
                    self.logger.add("Clearing cache...")
                    self.cursor.execute(
                        'DELETE FROM trend_api_cache '
                        'WHERE expire_time>={}'.format(gadget.datetime_to_timestamp(datetime.datetime.now())))
                    if self.count % 1000 == 0:
                        # Clear queue.
                        self.logger.add("Clearing queue...")
                        for eachPoolId in range(Global.TrendAPIPoolNum):
                            for eachPriority in self.queue[eachPoolId]:
                                for eachQuery in self.queue[eachPoolId][eachPriority]:
                                    if self.queue[eachPoolId][eachPriority][eachQuery]["finished"]:
                                        del self.queue[eachPoolId][eachPriority][eachQuery]
                    self.count = 0
                    self.release_lock()

                # Update queue.
                self.logger.add("Updating queue...")
                self.cursor.execute('SELECT query, pool_id, priority FROM trend_api_queue')
                queueList = self.cursor.fetchall()
                for eachQueue in queueList:
                    eachQuery, eachPoolId, eachPriority = eachQueue
                    if eachPriority not in self.queue[eachPoolId]:
                        self.queue[eachPoolId][eachQuery] = {}
                    if eachQuery not in self.queue[eachPoolId][eachPriority]:
                        # Check whether same query with other priorities exists.
                        for eachPriority in self.queue[eachPoolId]:
                            if eachQuery in self.queue[eachPoolId][eachPriority]:
                                del self.queue[eachPoolId][eachPriority][eachQuery]
                        # Add into the corresponding priority queue.
                        self.queue[eachPoolId][eachPriority][eachQuery] = {"finished": False}
            except Exception as e:
                self.logger.add("Unknown error occurred.", "SEVERE", ex=e)
                break
            time.sleep(Global.TrendAPIQueryCycle)
            self.count += 1
