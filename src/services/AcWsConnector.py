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
        self.acWsSender = AcWsSender(self.ws)
        self.acWsReceiver = AcWsReceiver(self.ws)
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

    def __init__(self, ws):
        threading.Thread.__init__(self, name="AcWsSender")
        self.logger = Logger(name)
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
                    'SELECT request_id, func, id, requested FROM trend_acws_queue '
                    'WHERE requested=0 ORDER BY priority LIMIT 100')
                newRequestList = self.cursor.fetchall()
                self.logger.add("Fetched {} requests".format(len(newRequestList)))
                requestList.extend(newRequestList)

                # Gets all the timed out requests.
                self.logger.add("Fetching all  the timed out requests...")
                self.cursor.execute(
                    'SELECT request_id, func, id, retry_num, max_retry_num, priority FROM trend_acws_queue '
                    'WHERE requested=1 and expire_time<{}'.format(
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
                            'UPDATE trend_acws_queue SET '
                            'request_date="{}", request_time={}, expire_time={}, '
                            'retry_num=0, max_retry_num={}, requested=1 '
                            'WHERE request_id={}'.format(
                                d.isoformat(), gadget.datetime_to_timestamp(d),
                                gadget.datetime_to_timestamp(d + datetime.timedelta(seconds=Global.AcFunAPIWsTimeout)),
                                Global.AcFunAPIWsRetryNum), eachRequest[0])
                    else: # Retry request.
                        self.cursor.execute(
                            'UPDATE trend_acws_queue SET '
                            'request_date="{}", request_time={}, expire_time={}, '
                            'retry_num=retry_num+1 '
                            'WHERE request_id={}'.format(
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

    def __init__(self, ws):
        threading.Thread.__init__(self, name="AcWsReceiver")
        self.logger = Logger(name)
        self.count = 0
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
            if self.count % 10000 == 0:
                # Gets the highest uploader score and the highest channel score.
                self.logger.add("Fetching the highest uploader % channel score ...")
                try:
                    self.cursor.execute("SELECT score_trend FROM ac_users ORDER BY score_trend DESC LIMIT 1")
                    assert self.cursor.rowcount > 0
                    highestUploaderScore = self.cursor.fetchall()[0][0]
                except Exception as e:
                    highestUploaderScore = 0
                    self.logger.add("Failed to get highest uploader score. Treat it as 0.", "SEVERE", ex=e)
                try:
                    self.cursor.execute("SELECT score_trend FROM ac_channels ORDER BY score_trend DESC LIMIT 1")
                    assert self.cursor.rowcount > 0
                    highestChannelScore = self.cursor.fetchall()[0][0]
                except Exception as e:
                    highestChannelScore = 0
                    self.logger.add("Failed to get highest uploader score. Treat it as 0.", "SEVERE", ex=e)
                self.logger.add(
                    "Highest score: uploader = {}, channel = {}".format(highestUploaderScore, highestChannelScore))

            try:
                # Receives information from the AcFun WebSocket API.
                result = json.loads(self.ws.recv())
                requestID = result["requestID"]

                # Gets the request information from AcWs Queue.
                self.cursor.execute("SELECT func, id FROM trend_acws_queue WHERE request_id={}".format(requestID))
                rFunc, rId = self.cursor.fetchall()[0]

                self.logger.add("Received requestID={}, func={}, id={}".format(requestID, rFunc, rId))

                # Parses the information.
                if rFunc == Global.AcFunAPIFuncGetArticleFull: # Article.
                    # Checks whether the article has record in database.
                    self.cursor.execute("SELECT survive FROM ac_articles WHERE id={}".format(rId))
                    articleHasRecord = self.cursor.rowcount > 0
                    isSurvive = None
                    if articleHasRecord:
                        isSurvive = self.cursor.fetchall()[0][0] == 1
                        self.logger.add(
                            "The database has ac{}: {}. Survive: {}".format(rId, articleHasRecord, isSurvive))
                    else:
                        self.logger.add("This is a new article: ac{}".format(rId))

                    if result["statusCode"] == 200: # Article exists.
                        # Adds the information into the database.
                        result = result["result"]
                        if result["id"] != rId:
                            raise Exception("Request ID and rID mismatch.")

                        # Checks whether the uploader has record in database.
                        self.logger.add("Checking whether the user has record ...")
                        self.cursor.execute(
                            "SELECT score_trend, rank FROM ac_users WHERE id={}".format(result["userId"]))
                        if self.cursor.rowcount > 0:
                            userHasRecord = True
                            fetchResult = self.cursor.fetchall()[0]
                            userScore = fetchResult[0]
                            userRank = fetchResult[1]
                        else:
                            userHasRecord = False
                            userScore = 0
                            userRank = 0
                        self.logger.add(
                            "Has record = {}, score = {}, rank = {}".format(userHasRecord, userScore, userRank))

                        # ac_articles
                        self.logger.add("Adding ac{} into ac_articles ...".format(rId))
                        sortTimeModified = False

                        if "contentImg" not in result:
                            result["contentImg"] = result["img"]

                        if "tags" not in result:
                            result["tags"] = []
                        tagList = []
                        for eachTag in result["tags"]:
                            tagList.append([eachTag[2], eachTag[3]])

                        # TODO Calculate score_trend of the article.


                        if articleHasRecord:
                            self.logger.add("Updating ac{}@ac_articles ...".format(rId))
                            previousSortTime = self.cursor.execute('SELECT sortTime FROM ac_articles '
                                                                   'WHERE id={}'.format(rId))
                            sortTimeCount = ", "
                            if previousSortTime != result["sortTime"]:
                                sortTimeCount += "sort_time_count=sort_time_count+1, "
                                sortTimeModified = True
                                self.logger.add("This article has been modified.")

                            self.cursor.execute('UPDATE ac_articles SET '
                                                'type_id={}, title="{}", description="{}", '
                                                'user_id={}, user_name="{}", '
                                                'sort_time={}{} last_feedback_time={}, '
                                                'img="{}", content_img="{}", '
                                                'hits={}, week_views={}, month_views={}, day_views={}, '
                                                'comments={}, stows={}, parts={}, score={}, score_trend={}, '
                                                'channel_name="{}", channel_id={}, survive=1, '
                                                'tags={} ' # tags only store tagId and tagName
                                                'WHERE id={}'.format(result["typeId"], result["title"],
                                                                     result["description"], result["userId"],
                                                                     result["userName"], result["sortTime"],
                                                                     sortTimeCount, result["lastFeedbackTime"],
                                                                     result["img"], result["contentImg"],
                                                                     result["views"], result["weekViews"],
                                                                     result["monthViews"], result["dayViews"],
                                                                     result["comments"], result["stows"], RESULT_PARTS,
                                                                     result["score"], TREND_SCORE_HERE,
                                                                     result["channelName"], result["channelId"],
                                                                     tagList, rId))
                        else:
                            self.logger.add("Inserting ac{}@ac_articles ...".format(rId))

                            contDatetime = datetime.datetime.utcfromtimestamp(result["contributeTime"])
                            contAcDay = gadget.date_to_ac_days(contDatetime)
                            contWeek = gadget.date_to_ac_weeks(contDatetime)

                            self.cursor.execute('INSERT INTO ac_articles ('
                                                'id, type_id, title, description, user_id, user_name,'
                                                'contribute_time, contribute_time_day, contribute_time_ac_day, '
                                                'contribute_time_week, contribute_time_month, contribute_time_year,  '
                                                'sort_time, last_feedback_time, img, content_img, '
                                                'hits, week_views, month_views, day_views, comments, stows, parts, '
                                                'score, score_trend, channel_name, channel_id, tags'
                                                ') VALUES ('
                                                '{}, {}, "{}", "{}", {}, "{}", '
                                                '{}, {}, {}, {}, {}, {}, '
                                                '{}, {}, {}, "{}", "{}", '
                                                '{}, {}, {}, {}, {}, {}, {}'
                                                '{}, {}, "{}", {}, "{}"'
                                                ')'.format(rId, result["typeId"], result["title"],
                                                           result["description"], result["userId"], result["userName"],
                                                           result["contributeTime"], contDatetime.day, contAcDay,
                                                           contWeek, contDatetime.month, contDatetime.year,
                                                           result["sortTime"], result["lastFeedbackTime"],
                                                           result["img"], result["contentImg"], result["views"],
                                                           result["weekViews"], result["monthViews"],
                                                           result["dayViews"], result["comments"],
                                                           result["stows"], RESULT_PARTS, result["score"],
                                                           TREND_SCORE_HERE, result["channelName"], result["channelId"],
                                                           tagList))
                        # ac_users
                        self.logger.add("Adding ac{} into ac_users ...".format(rId))
                        # TODO MARK.

                        # ac_channels
                        self.logger.add("Adding ac{} into ac_channels ...".format(rId))
                        # TODO MARK.

                        # ac_delta
                        self.logger.add("Adding ac{} into ac_delta ...".format(rId))
                        # TODO MARK.
                        # HINT Don't forget update sortTime if modified.

                    elif result["statusCode"] == 402: # Article does not exist.
                        self.logger.add("Article does not exist: ac{}".format(rId))
                        if articleHasRecord and isSurvive:
                            # Changes survive in ac_articles.
                            self.logger.add("Changing survive mode of ac{} to 0 ...".format(rId))
                            self.cursor.execute("UPDATE ac_articles SET survive=0 WHERE id={}".format(rId))
                            # Changes ac_users.

                            # Changes ac_channels.

                            # Changes ac_tags.

                    else:
                        self.logger.add(
                            "Unexpected error at ac{}: statusCode={}, result={}".format(rId, result["statusCode"],
                                                                                        result["result"]), "SEVERE")
                elif rFunc == Global.AcFunAPIFuncGetUserFull: # User.
                    # TODO Parses user info.
                    pass
                else: # Unrecognized.
                    self.logger.add("Unrecognized func: {}.".format(rFunc), "SEVERE")
            except Exception as e:
                self.logger.add("Received invalid data. Skipped.", "WARNING", ex=e)

            self.count += 1
            time.sleep(Global.AcFunAPIWsCycleGap)


if __name__ == "__main__":
    acWsConnector = AcWsConnector()
    acWsConnector.start()