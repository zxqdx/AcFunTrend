__author__ = "zxqdx"

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from miscellaneous import gadget

# IMPORTANT: isDebug indicates whether all the services are running in the real environment
#            or running in testing mode. Change it during deployment!!
isDebug = True

wwwPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wwwPath = gadget.replace_all(wwwPath, "\\", "/")

if isDebug:
    mysqlUser = "root"
    mysqlHost = "127.0.0.1"
    mysqlPassword = "miaowu"
    mysqlPort = 3306
    mysqlAcWsConnectorDB = "trend_acws"
    mysqlAcArticleDB = "trend_articles"
else:
    raise NotImplementedError("Not yet deployed.")