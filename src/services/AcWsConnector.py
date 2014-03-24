"""
Created on Nov 24, 2013

@author: zxqdx
"""

# Imports parent directory to sys.path
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from websocket import create_connection

from ServiceLocker import ServiceLocker
from Logger import Logger
import Global

from miscellaneous import gadget
import threading
import pymysql
import datetime
import time
import json


class RequestRemovedError(Exception):
    def __init__(self, rId):
        self.msg = "The request {} has been removed".format(rId)

    def __str__(self):
        return repr(self.msg)


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

        self.ws = [True, None]
        self.get_ws()

        # Sets up threads.
        self.logger.add("Setting up threads.", "DEBUG")
        self.acWsSender = AcWsSender(self.ws)
        self.acWsReceiver = AcWsReceiver(self.ws)
        self.acWsSender.daemon = True
        self.acWsReceiver.daemon = True

    def get_ws(self):
        # Connects to AcFun WebSocket.
        self.ws[1] = None
        self.logger.add("Connecting to AcFun WebSocket...", "DEBUG")
        isConnected = False
        while not isConnected:
            try:
                self.ws[1] = create_connection(Global.AcFunAPIWsUrl)
                isConnected = True
            except Exception as e:
                self.logger.add("Failed to connect to AcFun WebSocket.", "WARNING", ex=e)
                time.sleep(20)
        self.logger.add("Authenticating...", "DEBUG")
        self.ws[1].send(
            '{{func:"auth","key":"{}","secret":"{}"}}'.format(Global.AcFunAPIWsKey, Global.AcFunAPIWsSecret))
        try:
            result = json.loads(self.ws[1].recv(), strict=False)
            isSuccess = False
            if "success" in result:
                isSuccess = result["success"]
            elif "result" in result:
                assert type(result["result"]) == bool, result["result"]
                isSuccess = result["result"]
            if isSuccess:
                self.logger.add("Authenticate complete.", "DEBUG")
            else:
                raise Exception("Connection maintains but authenticate failed.")
        except Exception as e:
            self.logger.add("Failed to authenticate.", "SEVERE", ex=e)
            self.close()
            self.logger.close()
            raise SystemExit

    def run(self):
        # Starts threads.
        self.logger.add("Starting threads...", "DEBUG")
        self.acWsReceiver.start()
        self.acWsSender.start()
        while True:
            interrupter = self.serviceLocker.is_interrupt()
            if interrupter:
                self.logger.add("The service is interrupted by {}.".format(interrupter), "SEVERE")
                break

            # self.acWsReceiver.join(0.1)
            if not self.acWsReceiver.isAlive():
                self.logger.add("An error occurs in thread {}. The service is about to quit.".format("AcWsReceiver"),
                                "SEVERE")
                break

            # self.acWsSender.join(0.1)
            if not self.acWsSender.isAlive():
                self.logger.add("An error occurs in thread {}. The service is about to quit.".format("AcWsSender"),
                                "SEVERE")
                break

            if not self.ws[0]:
                self.get_ws()
                self.ws[0] = True
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
        self.logger = Logger(self.name)
        self.ws = ws
        try:
            self.logger.add("Connecting to MYSQL {}:{}. DB={}. User={} ...".format(Global.mysqlHost, Global.mysqlPort,
                                                                                   Global.mysqlAcWsConnectorDB,
                                                                                   Global.mysqlUser), "DEBUG")
            self.conn = pymysql.connect(host=Global.mysqlHost, port=Global.mysqlPort, user=Global.mysqlUser,
                                        passwd=Global.mysqlPassword, db=Global.mysqlAcWsConnectorDB)
            self.conn.set_charset(Global.mysqlEncoding)
            self.cursor = self.conn.cursor()
            self.cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
        except Exception as e:
            self.logger.add("Failed to connect {} database. Please check the status of MYSQL service.".format(
                Global.mysqlAcWsConnectorDB), "SEVERE", ex=e)
            raise e

    def escape_string(self, s):
        return self.conn.escape_string(s)

    def run(self):
        while True:
            # Processes the AcWs Queue.
            self.logger.add("Processing the AcWs Queue...")
            requestList = []
            try:
                # Gets the next {{Global.AcFunAPIWsCycleRequestNum}} requests from ACWS Queue.
                self.logger.add(
                    "Fetching the next {} requests from ACWS Queue ...".format(Global.AcFunAPIWsCycleRequestNum))
                self.cursor.execute(
                    'SELECT request_id, func, id, requested FROM trend_acws_queue '
                    'WHERE requested=0 ORDER BY priority LIMIT {}'.format(Global.AcFunAPIWsCycleRequestNum))
                newRequestList = self.cursor.fetchall()
                self.logger.add("Fetched {} new requests.".format(len(newRequestList)), "DEBUG")
                requestList.extend(newRequestList)

                # Gets all the timed out requests.
                self.logger.add("Fetching all the timed out requests ...")
                self.cursor.execute('SELECT request_id, func, id, retry_num, max_retry_num, priority '
                                    'FROM trend_acws_queue '
                                    'WHERE requested=1 and expire_time<{}'.format(gadget.datetime_to_timestamp()))
                timedOutRequestList = self.cursor.fetchall()
                if len(timedOutRequestList) != 0:
                    self.logger.add("Fetched {} timed out requests.".format(len(timedOutRequestList)), "DEBUG")

                # Retries the request if retryNum <= maxRetryNum. Abandons if retryNum > maxRetryNum.
                for eachTimedOutRequest in timedOutRequestList:
                    if eachTimedOutRequest[3] <= eachTimedOutRequest[4]: # Retries.
                        requestList.append((eachTimedOutRequest[0], eachTimedOutRequest[1], eachTimedOutRequest[2], 1))
                        self.logger.add(
                            "Retries request: func={}, id={}".format(eachTimedOutRequest[1], eachTimedOutRequest[2]))
                    else: # Abandons.
                        self.cursor.execute(
                            'DELETE FROM trend_acws_queue WHERE request_id={}'.format(eachTimedOutRequest[0]))
                        try:
                            self.cursor.execute('INSERT INTO trend_acws_removed('
                                                'request_id, func, id'
                                                ') VALUES ('
                                                '{}, "{}", "{}"'
                                                ')'.format(eachTimedOutRequest[0], eachTimedOutRequest[1],
                                                           eachTimedOutRequest[2]))
                        except Exception as ex:
                            self.cursor.execute('UPDATE trend_acws_removed SET '
                                                'func="{}", '
                                                'id="{}"'
                                                'WHERE request_id={}'.format(eachTimedOutRequest[2],
                                                                               eachTimedOutRequest[1],
                                                                               eachTimedOutRequest[0]))
                        self.logger.add(
                            "Abandoned request: func={}, id={}".format(eachTimedOutRequest[1], eachTimedOutRequest[2]),
                            "DEBUG")
                        self.conn.commit()
            except Exception as e:
                self.logger.add("Error occurs during processing the AcWs Queue.", "SEVERE", ex=e)
                raise e

            # Sends the request and updates AcWs Queue.
            requestListLength = len(requestList)
            for x in range(requestListLength):
                eachRequest = requestList[x]
                # Sends the request.
                if (x + 1) % 25 == 0:
                    debugLevel = "DEBUG"
                else:
                    debugLevel = "DETAIL"
                self.logger.add(
                    "{}/{} Sending request {}: func={}, id={}, requested={} ...".format((x + 1), requestListLength,
                                                                                        eachRequest[0], eachRequest[1],
                                                                                        eachRequest[2], eachRequest[3]),
                    debugLevel)
                try:
                    self.ws[1].send(
                        '{{func:"{}",id:"{}",requestId:"{}{}"}}'.format(eachRequest[1], eachRequest[2],
                                                                        Global.AcFunAPIWsRequestIdPrefix,
                                                                        eachRequest[0]))
                except Exception as e:
                    self.logger.add(
                        "Error occurs while sending request {}: func={}, id={}".format(eachRequest[0], eachRequest[1],
                                                                                       eachRequest[2]), "SEVERE", ex=e)
                    self.ws[0] = False
                    while not self.ws[0]:
                        time.sleep(1)
                        # raise e

                # Updates AcWs Queue.
                self.logger.add("Updating AcWs Queue ...")
                try:
                    d = datetime.datetime.now()
                    if eachRequest[3] == 0: # New request.
                        self.cursor.execute(
                            'UPDATE trend_acws_queue SET '
                            'request_date="{}", request_time={}, expire_time={}, '
                            'retry_num=0, requested=1 '
                            'WHERE request_id={}'.format(
                                self.escape_string(d.isoformat()), gadget.datetime_to_timestamp(d),
                                gadget.datetime_to_timestamp(d + datetime.timedelta(seconds=Global.AcFunAPIWsTimeout)),
                                eachRequest[0]))
                    else: # Retry request.
                        self.cursor.execute(
                            'UPDATE trend_acws_queue SET '
                            'request_date="{}", request_time={}, expire_time={}, '
                            'retry_num=retry_num+1 '
                            'WHERE request_id={}'.format(
                                self.escape_string(d.isoformat()), gadget.datetime_to_timestamp(d),
                                gadget.datetime_to_timestamp(d + datetime.timedelta(seconds=Global.AcFunAPIWsTimeout)),
                                eachRequest[0]))
                    self.conn.commit()
                except Exception as e:
                    self.logger.add("Error occurs during updating the AcWs Queue.", "SEVERE", ex=e)
                    raise e
            if requestListLength == 0:
                time.sleep(Global.AcFunAPIWsCycleGap)
            else:
                time.sleep(requestListLength / Global.AcFunAPIWsCycleRequestNum * 1.8)
                pass


class AcWsReceiver(threading.Thread):
    """
    The receiver that is responsible for receiving requests and saving them to database.
    """

    def __init__(self, ws):
        threading.Thread.__init__(self, name="AcWsReceiver")
        self.logger = Logger(self.name)
        self.count = 0
        self.ws = ws
        try:
            self.logger.add("Connecting to MYSQL {}:{}. DB={}. User={} ...".format(Global.mysqlHost, Global.mysqlPort,
                                                                                   Global.mysqlAcWsConnectorDB,
                                                                                   Global.mysqlUser), "DEBUG")
            self.conn = pymysql.connect(host=Global.mysqlHost, port=Global.mysqlPort, user=Global.mysqlUser,
                                        passwd=Global.mysqlPassword, db=Global.mysqlAcWsConnectorDB)
            self.conn.set_charset(Global.mysqlEncoding)
            self.cursor = self.conn.cursor()
            self.cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
        except Exception as e:
            self.logger.add("Failed to connect {} database. Please check the status of MYSQL service.".format(
                Global.mysqlAcWsConnectorDB), "SEVERE", ex=e)
            raise e

    def escape_string(self, s):
        return self.conn.escape_string(s)

    def run(self):
        while True:
            if self.count % 10000 == 0:
                # Gets the highest uploader score and the highest channel score.
                self.logger.add("Fetching the highest uploader % channel score ...")
                highestUploaderScore = 0
                highestChannelScore = 0
                channelScoreList = {}
                try:
                    self.cursor.execute("SELECT score_trend FROM ac_users ORDER BY score_trend DESC LIMIT 1")
                    assert self.cursor.rowcount > 0
                    highestUploaderScore = self.cursor.fetchall()[0][0]
                except Exception as e:
                    self.logger.add("Failed to get highest uploader score. Treat it as 0.", "SEVERE")
                try:
                    self.cursor.execute("SELECT id, score_trend FROM ac_channels ORDER BY score_trend DESC")
                    assert self.cursor.rowcount > 0
                    fetchResult = self.cursor.fetchall()
                    highestChannelScore = fetchResult[0][1]
                    for eachChannel in fetchResult:
                        channelScoreList[eachChannel[0]] = eachChannel[1]
                except Exception as e:
                    self.logger.add("Failed to get highest uploader score. Treat it as 0.", "SEVERE")
                self.logger.add(
                    "Highest score: uploader = {}, channel = {}".format(highestUploaderScore, highestChannelScore))

            try:
                # Initialization
                wsReceived = None
                result = None
                requestId = None

                # Receives information from the AcFun WebSocket API.
                try:
                    wsReceived = self.ws[1].recv()
                except Exception as e:
                    self.logger.add("Error occurs while receiving request.", "SEVERE", ex=e)
                    self.ws[0] = False
                    while not self.ws[0]:
                        time.sleep(1)
                result = gadget.parse_json(wsReceived, strict=False)
                requestId = result["requestId"][len(Global.AcFunAPIWsRequestIdPrefix):]

                # Gets the request information from AcWs Queue.
                self.cursor.execute("SELECT func, id FROM trend_acws_queue WHERE request_id={}".format(requestId))
                abandonedHint = ""
                if self.cursor.rowcount == 0:
                    self.cursor.execute("SELECT func, id FROM trend_acws_removed WHERE request_id={}".format(requestId))
                    if self.cursor.rowcount == 0:
                        raise RequestRemovedError(requestId)
                    abandonedHint = "abandoned "
                rFunc, rId = self.cursor.fetchall()[0]
                self.logger.add("Received {}requestId={}, func={}, id={}".format(abandonedHint, requestId, rFunc, rId))

                # Parses the information.
                if rFunc == Global.AcFunAPIFuncGetArticleFull: # Article.
                    # Checks whether the article has record in database.
                    self.cursor.execute('SELECT survive, hits, comments, stows, parts, '
                                        'score, score_trend, user_id, channel_id, tags, type_id '
                                        'FROM ac_articles WHERE id={}'.format(rId))
                    articleHasRecord = self.cursor.rowcount > 0
                    if articleHasRecord:
                        fetchResult = self.cursor.fetchall()[0]
                        isSurvive = fetchResult[0] == 2
                        previousHits, previousComments, previousStows, \
                        previousParts, previousScore, previousScoreTrend, \
                        previousUserId, previousChannelId, previousTags, previousTypeId = fetchResult[1:]
                        previousTags = json.loads(previousTags, strict=False)
                        self.logger.add(
                            "The database has ac{}: {}. Survive: {}".format(rId, articleHasRecord, isSurvive))
                    else:
                        isSurvive = False
                        self.logger.add("This article ac{} does not have record yet.".format(rId))

                    if result["statusCode"] == 200: # Article exists.
                        # status: -2 = does not exist. -1 = rejected. 0 = draft. 1 = waiting for editor.
                        # 2 = passed. 3 = hidden(?)
                        if "status" in result["result"]:
                            articleStatus = result["result"]["status"]
                        else:
                            self.logger.add("No status in API. Treat it as 2.", "WARNING")
                            articleStatus = 2

                        self.logger.add("Received ac{} with status={}.".format(rId, articleStatus), "DEBUG")

                        result = result["result"]
                        if result["id"] != int(rId):
                            raise Exception("Request ID {} and rID {} mismatch.".format(result["id"], rId))

                        # Checks whether the uploader has record in database.
                        self.cursor.execute(
                            'SELECT score_trend, rank FROM ac_users WHERE id={}'.format(result["userId"]))
                        if self.cursor.rowcount > 0:
                            userHasRecord = True
                            fetchResult = self.cursor.fetchall()[0]
                            userScore = fetchResult[0]
                            userRank = fetchResult[1]
                            if not userRank:
                                userRank = 0
                        else:
                            userHasRecord = False
                            userScore = 0
                            userRank = 0
                        self.logger.add(
                            "User {} has record = {}, score = {}, rank = {}".format(result["userId"], userHasRecord,
                                                                                    userScore, userRank))

                        # Checks whether the channel has record in database.
                        self.cursor.execute('SELECT id FROM ac_channels WHERE id={}'.format(result["channelId"]))
                        channelHasRecord = self.cursor.rowcount > 0
                        if not channelHasRecord:
                            self.logger.add(
                                "New channel: id={}, name={}".format(result["channelId"], result["channelName"]),
                                "DEBUG")

                        # ac_articles
                        self.logger.add("Adding ac{} into ac_articles ...".format(rId))
                        sortTimeModified = False

                        if "description" not in result:
                            result["description"] = ""

                        if "img" not in result:
                            result["img"] = ""

                        if "contentImg" not in result:
                            result["contentImg"] = result["img"]

                        if "tags" not in result:
                            result["tags"] = []
                        tagList = [] # tagList only store tagId and tagName
                        for eachTag in result["tags"]:
                            tagList.append([eachTag["tagId"], eachTag["tagName"]])

                        if "text" not in result:
                            # TODO Add a long-term solution.
                            resultParts = 0
                        else:
                            resultParts = result["text"].count("[NextPage]")
                            if resultParts == 0:
                                resultParts = 1

                        if result["typeId"] > 4 or result["typeId"] < 1:
                            self.logger.add("Unknown typeId={} occurs in ac{}.".format(result["typeId"], rId), "SEVERE")
                            result["typeId"] = 1
                        if result["typeId"] == 3: # TODO Adjust this when necessary.
                            isOriginal = True
                        else:
                            isOriginal = False

                        # Calculates score_trend of the article.
                        currentChannelScore = 0
                        if result["channelId"] in channelScoreList:
                            currentChannelScore = channelScoreList[result["channelId"]]
                        articleScore = gadget.calc_score(result["views"], result["comments"], result["stows"],
                                                         resultParts, isOriginal, userScore, highestUploaderScore,
                                                         currentChannelScore, highestChannelScore, userRank)
                        self.logger.add("The score of the article is {}".format(articleScore))

                        # ac_articles
                        if articleHasRecord:
                            self.logger.add("Updating ac{}@ac_articles ...".format(rId))
                            self.cursor.execute('SELECT sort_time FROM ac_articles '
                                                'WHERE id={}'.format(rId))

                            previousSortTime = self.cursor.fetchall()[0][0]
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
                                                'channel_name="{}", channel_id={}, survive={}, '
                                                'tags="{}" '
                                                'WHERE id={}'.format(result["typeId"],
                                                                     self.escape_string(result["title"]),
                                                                     self.escape_string(result["description"]),
                                                                     result["userId"],
                                                                     self.escape_string(result["username"]),
                                                                     result["sortTime"],
                                                                     sortTimeCount, result["lastFeedbackTime"],
                                                                     self.escape_string(result["img"]),
                                                                     self.escape_string(result["contentImg"]),
                                                                     result["views"], result["weekViews"],
                                                                     result["monthViews"], result["dayViews"],
                                                                     result["comments"], result["stows"], resultParts,
                                                                     result["score"], articleScore,
                                                                     self.escape_string(result["channelName"]),
                                                                     result["channelId"], articleStatus,
                                                                     self.escape_string(json.dumps(tagList)), rId))
                        else:
                            self.logger.add("Inserting ac{}@ac_articles ...".format(rId))

                            contDatetime = gadget.timestamp_to_datetime(result["contributeTime"])
                            contAcDay = gadget.date_to_ac_days(contDatetime)
                            contWeek = gadget.date_to_ac_weeks(contDatetime)

                            self.cursor.execute('INSERT INTO ac_articles ('
                                                'id, type_id, title, description, user_id, user_name,'
                                                'contribute_time, contribute_time_day, contribute_time_ac_day, '
                                                'contribute_time_week, contribute_time_month, contribute_time_year, '
                                                'sort_time, last_feedback_time, img, content_img, '
                                                'hits, week_views, month_views, day_views, comments, stows, parts, '
                                                'score, score_trend, channel_name, channel_id, survive, tags'
                                                ') VALUES ('
                                                '{}, {}, "{}", "{}", {}, "{}", '
                                                '{}, {}, {}, {}, {}, {}, '
                                                '{}, {}, "{}", "{}", '
                                                '{}, {}, {}, {}, {}, {}, {}, '
                                                '{}, {}, "{}", {}, {}, "{}"'
                                                ')'.format(rId, result["typeId"], self.escape_string(result["title"]),
                                                           self.escape_string(result["description"]), result["userId"],
                                                           self.escape_string(result["username"]),
                                                           result["contributeTime"], contDatetime.day, contAcDay,
                                                           contWeek, contDatetime.month, contDatetime.year,
                                                           result["sortTime"], result["lastFeedbackTime"],
                                                           self.escape_string(result["img"]),
                                                           self.escape_string(result["contentImg"]), result["views"],
                                                           result["weekViews"], result["monthViews"],
                                                           result["dayViews"], result["comments"], result["stows"],
                                                           resultParts, result["score"], articleScore,
                                                           self.escape_string(result["channelName"]),
                                                           result["channelId"], articleStatus,
                                                           self.escape_string(json.dumps(tagList))))
                        # ac_users
                        ## Removes old data.
                        if articleHasRecord:
                            self.logger.add("Removing old data of ac{} from ac_users ...".format(rId))
                            self.cursor.execute('UPDATE ac_users SET '
                                                'hits=hits-{}, comments=comments-{}, stows=stows-{}, '
                                                'parts=parts-{}, score=score-{}, score_trend=score_trend-{}, '
                                                'contains=contains-1, contains_{}=contains_{}-1 '
                                                'WHERE id={}'.format(previousHits, previousComments,
                                                                     previousStows, previousParts,
                                                                     previousScore, previousScoreTrend,
                                                                     previousTypeId, previousTypeId, previousUserId))
                        ## Adds new data.
                        if userHasRecord:
                            self.logger.add("Updating new data of ac{} into ac_users ...".format(rId))
                            self.cursor.execute('UPDATE ac_users SET '
                                                'hits=hits+{}, comments=comments+{}, stows=stows+{}, '
                                                'parts=parts+{}, score=score+{}, score_trend=score_trend+{}, '
                                                'contains=contains+1, contains_{}=contains_{}+1 '
                                                'WHERE id={}'.format(result["views"], result["comments"],
                                                                     result["stows"], resultParts, result["score"],
                                                                     articleScore, result["typeId"], result["typeId"],
                                                                     result["userId"]))
                        else:
                            self.logger.add("Inserting new data of ac{} into ac_users ...".format(rId))
                            self.cursor.execute('INSERT INTO ac_users ('
                                                'id, name, hits, comments, stows, parts, '
                                                'score, score_trend, contains, contains_{}'
                                                ') VALUES ('
                                                '{}, "{}", {}, {}, {}, {}, '
                                                '{}, {}, 1, 1'
                                                ')'.format(result["typeId"], result["userId"],
                                                           self.escape_string(result["username"]),
                                                           result["views"], result["comments"], result["stows"],
                                                           resultParts, result["score"], articleScore))

                        # ac_channels
                        ## Removes old data.
                        if articleHasRecord:
                            self.logger.add("Removing old data of ac{} from ac_channels ...".format(rId))
                            self.cursor.execute('UPDATE ac_channels SET '
                                                'hits=hits-{}, comments=comments-{}, stows=stows-{}, '
                                                'parts=parts-{}, score=score-{}, score_trend=score_trend-{}, '
                                                'contains=contains-1 '
                                                'WHERE id={}'.format(previousHits, previousComments,
                                                                     previousStows, previousParts,
                                                                     previousScore, previousScoreTrend,
                                                                     previousChannelId))
                        ## Adds new data.
                        if channelHasRecord:
                            self.logger.add("Updating new data of ac{} into ac_channels ...".format(rId))
                            self.cursor.execute('UPDATE ac_channels SET '
                                                'hits=hits+{}, comments=comments+{}, stows=stows+{}, '
                                                'parts=parts+{}, score=score+{}, score_trend=score_trend+{}, '
                                                'contains=contains+1 '
                                                'WHERE id={}'.format(result["views"], result["comments"],
                                                                     result["stows"], resultParts, result["score"],
                                                                     articleScore, result["channelId"]))
                        else:
                            self.logger.add("Inserting new data of ac{} into ac_channels ...".format(rId))
                            self.cursor.execute('INSERT INTO ac_channels ('
                                                'id, name, hits, comments, stows, parts, '
                                                'score, score_trend, contains'
                                                ') VALUES ('
                                                '{}, "{}", {}, {}, {}, {}, '
                                                '{}, {}, 1'
                                                ')'.format(result["channelId"],
                                                           self.escape_string(result["channelName"]),
                                                           result["views"], result["comments"], result["stows"],
                                                           resultParts, result["score"], articleScore))

                        # ac_tags
                        ## Removes old data.
                        if articleHasRecord:
                            self.logger.add("Removing old data of ac{} from ac_tags ...".format(rId))
                            for eachPreviousTag in previousTags:
                                self.cursor.execute('UPDATE ac_tags SET '
                                                    'hits=hits-{}, comments=comments-{}, stows=stows-{}, '
                                                    'parts=parts-{}, score=score-{}, score_trend=score_trend-{}, '
                                                    'contains=contains-1 '
                                                    'WHERE id={}'.format(previousHits, previousComments,
                                                                         previousStows, previousParts,
                                                                         previousScore, previousScoreTrend,
                                                                         eachPreviousTag[0]))
                        ## Adds new data.
                        for eachTag in result["tags"]:
                            self.cursor.execute('SELECT id FROM ac_tags WHERE id={}'.format(eachTag["tagId"]))
                            tagHasRecord = self.cursor.rowcount > 0
                            if tagHasRecord:
                                self.logger.add("Updating new data of ac{} into ac_tags ...".format(rId))
                                self.cursor.execute('UPDATE ac_tags SET '
                                                    'hits=hits+{}, comments=comments+{}, stows=stows+{}, '
                                                    'parts=parts+{}, score=score+{}, score_trend=score_trend+{}, '
                                                    'contains=contains+1 '
                                                    'WHERE id={}'.format(result["views"], result["comments"],
                                                                         result["stows"], resultParts, result["score"],
                                                                         articleScore, eachTag["tagId"]))
                            else:
                                self.logger.add("Inserting new data of ac{} into ac_tags ...".format(rId))
                                self.cursor.execute('INSERT INTO ac_tags ('
                                                    'id, name, hits, comments, stows, parts, '
                                                    'score, score_trend, contains, manager_id'
                                                    ') VALUES ('
                                                    '{}, "{}", {}, {}, {}, {}, '
                                                    '{}, {}, 1, {}'
                                                    ')'.format(eachTag["tagId"], self.escape_string(eachTag["tagName"]),
                                                               result["views"], result["comments"], result["stows"],
                                                               resultParts, result["score"], articleScore,
                                                               eachTag["managerId"]))

                        # ac_delta
                        if articleStatus == 2:
                            acDay = gadget.date_to_ac_days(gadget.timestamp_to_datetime(result["sortTime"]))
                            if articleHasRecord:
                                self.logger.add("Updating ac{} into ac_delta ...".format(rId))
                                self.cursor.execute('SELECT days, hits, comments, stows, sorts '
                                                    'FROM ac_delta WHERE id={}'.format(rId))
                                if self.cursor.rowcount > 0:
                                    deltaHasRecord = True
                                    dayList, hitList, commentList, stowList, sortList = self.cursor.fetchall()[0]
                                    dayList, hitList, commentList, stowList, sortList = json.loads(dayList), json.loads(
                                        hitList), json.loads(commentList), json.loads(stowList), json.loads(sortList)
                                    try:
                                        dayIndex = dayList.index(acDay)
                                        hitList[dayIndex] = result["views"]
                                        commentList[dayIndex] = result["comments"]
                                        stowList[dayIndex] = result["stows"]
                                        if sortTimeModified:
                                            sortList[acDay] += 1
                                    except:
                                        dayList.append(acDay)
                                        hitList.append(result["views"])
                                        commentList.append(result["comments"])
                                        stowList.append(result["stows"])
                                        sortList[acDay] = 1
                                else: # This should not happen.
                                    deltaHasRecord = False
                            if (not articleHasRecord) or (not deltaHasRecord):
                                self.logger.add("Inserting ac{} into ac_delta".format(rId))
                                self.cursor.execute('INSERT INTO ac_delta('
                                                    'id, days, hits, comments, stows, sorts'
                                                    ') VALUES ('
                                                    '{}, "{}", "{}", "{}", "{}", "{}"'
                                                    ')'.format(rId, [acDay], [result["views"]], [result["comments"]],
                                                               [result["stows"]],
                                                               self.escape_string(json.dumps({acDay: 1}))))
                        self.conn.commit()
                    elif result["statusCode"] == 402: # Article does not exist.
                        self.logger.add("Article does not exist: ac{}".format(rId))
                        if articleHasRecord and isSurvive:
                            # Changes survive in ac_articles.
                            self.logger.add("Changing survive mode of ac{} to -2 ...".format(rId), "DEBUG")
                            self.cursor.execute("UPDATE ac_articles SET survive=-2 WHERE id={}".format(rId))
                            self.conn.commit()
                    else:
                        self.logger.add(
                            "Unexpected error at ac{}: statusCode={}, result={}".format(rId, result["statusCode"],
                                                                                        result["result"]), "SEVERE")
                elif rFunc == Global.AcFunAPIFuncGetUserFull: # User.
                    if result["statusCode"] == 200:
                        self.logger.add("Received survived user{}.".format(rId), "DEBUG")

                        result = result["result"]
                        if result["id"] != int(rId):
                            raise Exception("Request ID {} and rID {} mismatch.".format(result["id"], rId))

                        self.logger.add("Updating user{} into ac_users ...".format(rId))
                        sqlUserInfo = ''
                        if "registerTime" in result:
                            sqlUserInfo += ', register_time={}'.format(result["registerTime"])
                        if "rank" in result:
                            sqlUserInfo += ', rank={}'.format(result["rank"])
                        if "gender" in result:
                            if result["gender"]:
                                result["gender"] = 0 # Male.
                            else:
                                result["gender"] = 1 # Female.
                            sqlUserInfo += ', gender={}'.format(result["gender"])
                        if "sextrend" in result:
                            sqlUserInfo += ', sex_trend={}'.format(result["sextrend"])
                        if "comefrom" in result:
                            sqlUserInfo += ', come_from="{}"'.format(self.escape_string(result["comefrom"]))
                        if "img" in result:
                            sqlUserInfo += ', img="{}"'.format(self.escape_string(result["img"]))
                        if "lastLoginTime" in result:
                            sqlUserInfo += ', last_login_time={}'.format(result["lastLoginTime"])
                        if "onlineDuration" in result:
                            sqlUserInfo += ', online_duration={}'.format(result["onlineDuration"])
                        self.cursor.execute('UPDATE ac_users SET '
                                            'name="{}"{} '
                                            'WHERE id={}'.format(self.escape_string(result["name"]), sqlUserInfo, rId))
                        self.conn.commit()
                    elif result["statusCode"] == 402:
                        raise Exception("Failed to get user info. Result={}".format(result["result"]))
                    else:
                        self.logger.add(
                            "Unexpected error at user{}: statusCode={}, result={}".format(rId, result["statusCode"],
                                                                                          result["result"]), "SEVERE")
                else: # Unrecognized.
                    self.logger.add("Unrecognized func: {}.".format(rFunc), "SEVERE")
                # Remove request from AcWs Queue.
                self.logger.add("Removing request {} from AcWs Queue ...".format(requestId))
                try:
                    self.cursor.execute("DELETE FROM trend_acws_queue WHERE request_id={}".format(requestId))
                    self.conn.commit()
                except Exception as e:
                    self.logger.add("Failed to remove request {} from AcWs Queue.".format(requestId), "SEVERE",
                                    ex=e)
            except RequestRemovedError as e:
                self.logger.add(str(e), "WARNING")
            except Exception as e:
                self.logger.add("Received invalid data = {}. Skipped.".format(wsReceived), "SEVERE", ex=e)
                # raise e
            self.count += 1


if __name__ == "__main__":
    acWsConnector = AcWsConnector()
    acWsConnector.start()