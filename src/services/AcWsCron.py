"""
Created on 12/21/13

@author: zxqdx
"""

# Imports parent directory to sys.path
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
import time
import json

from Logger import Logger
from miscellaneous import gadget
import Global


def main(mode):
    logger.add("Running on mode {}.".format(mode))
    # Connects to the ACWS Queue.
    conn, cursor = connect_to_queue()
    # Quits if the previous requests have not been finished yet.
    if is_previous_running(cursor, mode):
        logger.add("The previous requests are still running. This cron job is about to quit in order to avoid conflict",
                   "SEVERE")
        raise SystemExit
    if mode == 1:
        # Gets the newest article ID (AID) using HTTP request.
        logger.add("Fetching the newest AID ...")
        newestAID = None
        for x in range(10):
            resultJson = gadget.get_page(Global.AcFunAPIHost,
                                         "/http/json/exec?func=content.get&id=1999999999&next=true&desc=true",
                                         port=Global.AcFunAPIPort, timeout=10, form="json", retryNum=3, logger=logger)

            try:
                newestAID = resultJson["result"]["id"]
                break
            except:
                pass
            time.sleep(10)
        if not newestAID:
            logger.add("Failed to get the newest AID. This cron job is forced to quit.", "SEVERE")
            raise SystemExit
        else:
            logger.add("The newest AID is {}".format(newestAID))
        # Creates the job that adds and refreshes articles today.
        acDayToday = gadget.date_to_ac_days()
        ## Fetches the latest AID of articles before today.
        cursor.execute(
            "SELECT id FROM ac_articles WHERE sort_time_ac_day<{} ORDER BY sort_time DESC LIMIT 1".format(acDayToday))
        if cursor.rowcount > 1:
            earliestAID = cursor.fetchall()[0][0] # TODO: test it.
        else:
            ## If failed, set the earliest AID equals 1.
            earliestAID = 1
        logger.add("The earliest AID is {}".format(earliestAID))
        ## Pushes requests into the ACWS Queue.
        for AID in range(earliestAID + 1, newestAID + 1):
            if AID % 200 == 0:
                logger.add("{{{}/{}}} Pushing requests...".format(AID, newestAID))
            cursor.execute(
                'INSERT INTO trend_acws_queue(func, id, max_retry_num, priority) VALUES ("{}", "{}", {}, {})'.format(
                    "fullcontent.get", AID, 5, 1))
        conn.commit()
        logger.add("Requests pushed successfully.")
    elif mode == 2:
        pass
    elif mode == 3:
        pass
    logger.add("Finish mode {}.".format(mode))


def connect_to_queue():
    try:
        logger.add("Connecting to MYSQL {}:{}. DB={}. User={}...".format(Global.mysqlHost, Global.mysqlPort,
                                                                         Global.mysqlAcWsConnectorDB,
                                                                         Global.mysqlUser))
        connAcWs = pymysql.connect(host=Global.mysqlHost, port=Global.mysqlPort, user=Global.mysqlUser,
                                   passwd=Global.mysqlPassword, db=Global.mysqlAcWsConnectorDB)
        cursorAcWs = connAcWs.cursor()
    except Exception as e:
        logger.add("Failed to connect {} database. Please check the status of MYSQL service.".format(
            Global.mysqlAcWsConnectorDB), "SEVERE", ex=e)
        raise e
    return connAcWs, cursorAcWs


def is_previous_running(cursor, mode):
    cursor.execute("SELECT request_id FROM trend_acws_queue WHERE priority={} LIMIT 1".format(mode))
    return cursor.rowcount > 0


logger = Logger("AcWsCron")
if __name__ == "__main__":
    try:
        mode = int(sys.argv[1])
    except:
        mode = 1 # NOTICE: When manually running it, modify this number to change the mode.
    main(mode)