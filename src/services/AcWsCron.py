"""
Created on 12/21/13

@author: zxqdx
"""

# Imports parent directory to sys.path
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Logger import Logger
import Global
import pymysql

def main(mode):
    # Connects to the MYSQL Database.
    conn, cursor = connect_to_queue()
    # Quits if the previous requests have not been finished yet.
    if mode==1:
        if is_previous_running(cursor, "priority=0 OR priority=1"):
            pass
    elif mode==2:
        if is_previous_running(cursor, "priority=2"):
            pass
    elif mode==3:
        if is_previous_running(cursor, "priority=3"):
            pass

def connect_to_queue():
    try:
        connAcWs = pymysql.connect(host=Global.mysqlHost, port=Global.mysqlPort, user=Global.mysqlUser, passwd=Global.mysqlPassword, db=Global.mysqlAcWsConnectorDB)
        cursorAcWs = connAcWs.cursor()
    except Exception as e:
        logger.add("Failed to connect {} database. Please check the status of MYSQL service.".format(Global.mysqlAcWsConnectorDB), "SEVERE", ex=e)
        raise e
    return connAcWs, cursorAcWs

def is_previous_running(cursor, where):
    cursor.execute("SELECT request_id FROM trend_acws_queue WHERE {} LIMIT 1".format(where))
    return cursor.rowcount > 0

logger = Logger("AcWsCron")
if __name__ == "__main__":
    try:
        mode = int(sys.argv[1])
    except:
        mode = 1 # When manually running it, modify this number to change the mode.
    main(mode)