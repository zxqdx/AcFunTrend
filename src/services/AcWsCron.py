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
    # Connects to the MYSQL Database.
    conn, cursor = connect_to_queue()
    # Quits if the previous requests have not been finished yet.
    if is_previous_running(cursor, mode):
        logger.add("The previous requests are still running. This cron job is about to quit in order to avoid conflict",
                   "SEVERE")
        raise SystemExit
    if mode==1:
        # Gets the newest article (Using HTTP request).
        newestAID = None
        for x in xrange(10):
            resultStr = gadget.get_page(Global.AcFunAPIHost, Global.AcFunAPIHttpUrl, port=AcFunAPIPort,
                                        timeout=10, retryNum=3, logger=logger)
            resultJson = json.loads(resultStr)
            try:
                newestAID = resultJson["result"]["id"]
                break
            except:
                pass
            time.sleep(10)
        if not newestAID:
            logger.add("Failed to get the newest AID. This cron job is forced to quit.", "SEVERE")
            raise SystemExit
        # Adds and refreshes today's articles.

        pass
    elif mode==2:
        pass
    elif mode==3:
        pass


def connect_to_queue():
    try:
        logger.add("Connecting to MYSQL {}:{}. DB={}. User={}...".format(Global.mysqlHost, Global.mysqlPort,
                                                                         Global.mysqlAcWsConnectorDB,
                                                                         Global.mysqlUser))
        connAcWs = pymysql.connect(host=Global.mysqlHost, port=Global.mysqlPort, user=Global.mysqlUser, passwd=Global.mysqlPassword, db=Global.mysqlAcWsConnectorDB)
        cursorAcWs = connAcWs.cursor()
    except Exception as e:
        logger.add("Failed to connect {} database. Please check the status of MYSQL service.".format(Global.mysqlAcWsConnectorDB), "SEVERE", ex=e)
        raise e
    return connAcWs, cursorAcWs


def is_previous_running(cursor, mode):
    cursor.execute("SELECT request_id FROM trend_acws_queue WHERE priority={}} LIMIT 1".format(mode))
    return cursor.rowcount > 0

logger = Logger("AcWsCron")
if __name__ == "__main__":
    try:
        mode = int(sys.argv[1])
    except:
        mode = 1 # When manually running it, modify this number to change the mode.
    main(mode)