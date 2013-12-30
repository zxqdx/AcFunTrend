import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from miscellaneous import gadget

# IMPORTANT: isDebug indicates whether all the services are running in the real environment
#            or running in testing mode. Change it during deployment!!
isDebug = True

wwwPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wwwPath = gadget.replace_all(wwwPath, "\\", "/")

# IMPORTANT: globalSwitchPath is the path of global switch. If it contains "9",
#            AcFun Trend services will quit!!
globalSwitchPath = "{}/GlobalSwitch.trr".format(wwwPath)

AcFunAPIHost = "59.175.227.54"
AcFunAPIPort = 88
AcFunAPIHttpUrl = "http://{}:{}/http/json/exec?".format(AcFunAPIHost, AcFunAPIPort)
AcFunAPIWsUrl = "ws://{}:{}/ws".format(AcFunAPIHost, AcFunAPIPort)
AcFunAPIWsKey = "3fe3f2b10bbad0a1"
AcFunAPIWsSecret = "e0c64e4b2c6eba73a1bb2b5ba2a854bbc1fa592f"
AcFunAPIWsRequestIdPrefix = "AcTr-"
AcFunAPIWsTimeout = 20
AcFunAPIWsRetryNum = 3
AcFunAPIWsCycleGap = 2
AcFunAPIFuncGetArticle = "content.get"
AcFunAPIFuncGetArticleFull = "fullcontent.get"
AcFunAPIFuncGetUserFull = "fulluser.get"

logFileSuffix = "trendlog"
lockFileSuffix = "slock"

if isDebug:
    mysqlUser = "root"
    mysqlHost = "127.0.0.1"
    mysqlPassword = "miaowu"
    mysqlPort = 3306
    mysqlAcWsConnectorDB = "trend_acws"
    mysqlAcArticleDB = "trend_articles"
else:
    raise NotImplementedError("Not yet deployed.")
