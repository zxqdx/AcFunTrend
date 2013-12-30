"""
Created on 11, 24, 2013

@author: BigMoe
"""

import json
import sys
import os
import time
import datetime


def is_panguine():
    """
    Returns true if it is Linux.
    """
    return not sys.platform.startswith("win")


def is_file(filePath):
    """
    Returns true if the file exists.
    """
    return os.path.isfile(filePath)


def write_file(filename, content, form="json", append=True, end=True, toConsole=False):
    try:
        folderName = os.path.dirname(filename)
        try:
            os.makedirs(folderName)
        except Exception as e:
            pass
        if append:
            file = open(filename, "a")
        else:
            file = open(filename, "w")
        if not form:
            file.write(content)
            if toConsole:
                print(content, end="")
        elif form == "json":
            file.write(json.dumps(content))
            if toConsole:
                print(json.dumps(content), end="")
        if end:
            if is_panguine():
                end_str = "\r"
            else:
                end_str = "\n"
            file.write(end_str)
            if toConsole:
                print(end_str, end="")
        file.close()
    except Exception as e:
        raise e
    return True


def read_file(filename, form="json"):
    try:
        file = open(filename, "r")
        content = file.read().strip()
        if form == "json":
            content = json.loads(content, strict=False)
        file.close()
        return content
    except Exception as e:
        raise e


def remove_file(filename):
    try:
        os.remove(filename)
    except Exception as e:
        return False
    return True


def try_until_sign_appears(sign, tryFunc, errorFunc=None, failedFunc=None, retryNum=-1, sleep=1, logger=None):
    """
    @Param errorFunc: Has to have the "msg" parameter.
    """
    isSuccess = False
    retry = 0
    while not isSuccess and retry <= retryNum:
        try:
            receive = tryFunc()
            if receive == sign:
                isSuccess = True
        except Exception as e:
            if errorFunc:
                errorFunc(msg=str(e))
            if logger:
                logger.add("Error occurred in try_until_sign_appears@gadget.", "WARNING", e)
        retry += 1
        if retry == retryNum + 1:
            time.sleep(sleep)
    if not isSuccess:
        if failedFunc:
            failedFunc()
    return isSuccess


def replace_all(string, old, new):
    while old in string:
        string = string.replace(old, new)
    return string


def date_to_ac_days(d=None):
    if not d:
        d = datetime.datetime.now()
    start = datetime.datetime(2007, 6, 4)
    return (d - start).days + 1


def date_to_ac_weeks(d=None):
    if not d:
        d = datetime.datetime.now()
    start = datetime.datetime(2007, 6, 4)
    return (d - start).days // 7 + 1


def datetime_to_timestamp(d=None):
    if not d:
        d = datetime.datetime.now()
    return int(d.timestamp() * 1000)


def timestamp_to_datetime(ts, tz=8):
    try:
        d = datetime.datetime.utcfromtimestamp(ts)
    except OSError:
        d = datetime.datetime.utcfromtimestamp(ts / 1000)
    return d + datetime.timedelta(hours=tz)


def get_page(host, url, port=80, timeout=None, form=None, retryNum=-1, sleep=1, logger=None):
    def get_result(resultWrapper):
        resultWrapper[0] = pool.request('GET', url)
        resultWrapper[1] = resultWrapper[0].data.decode("utf-8")

    def raise_exception(msg):
        raise Exception(msg)

    import urllib3

    if not timeout:
        timeout = urllib3.Timeout.DEFAULT_TIMEOUT
    else:
        timeout = urllib3.Timeout(total=timeout)
    pool = urllib3.HTTPConnectionPool(host, port, timeout=timeout)

    resultWrapper = [None, None]
    try_until_sign_appears(None, lambda: get_result(resultWrapper),
                           failedFunc=lambda: raise_exception("Failed to GET http:{}:{}{}".format(host, port, url)),
                           retryNum=retryNum, sleep=sleep, logger=logger)
    if not resultWrapper[1]:
        resultWrapper[1] = ""
    if not form:
        return resultWrapper[1]
    elif form == "json":
        resultJson = None
        try:
            resultJson = json.loads(resultWrapper[1], strict=False)
        except Exception as e:
            raise_exception(str(e))
        return resultJson
    else:
        raise NotImplementedError("Unknown format: {}".format(form))


def calc_score(hits, comments, stows, parts, isOriginal, uploaderScore, highestUploaderScore, channelScore,
               highestChannelScore, uploaderRank):
    import math

    # print(hits, comments, stows, parts, isOriginal, uploaderScore, highestUploaderScore, channelScore,
    #       highestChannelScore, uploaderRank)

    GOLDEN_SECTION = (1 + math.sqrt(5)) / 2

    if hits > 0:
        hit_score = hits * ((1 / math.e) ** math.log(hits / 100, 10))
    else:
        hit_score = 0
    if comments > 0:
        comment_score = comments * 20 / (
            (comments * (1 / math.e ** (math.log(comments, 10)))) / (math.e / (GOLDEN_SECTION - 1) + 1))
    else:
        comment_score = 0
    if stows <= 0:
        stow_score = 0
    elif stows <= 50000:
        stow_score = stows * ((GOLDEN_SECTION - 1) + stows / 100000) ** (1 - math.log(stows, 10) / GOLDEN_SECTION)
    else:
        stow_score = 40432
    if parts == 0:
        part_score = 0
    else:
        part_score = 100 / (8 ** math.log(parts, 10)) * parts ** 1.5
    score_trend = hit_score + comment_score + stow_score + part_score

    # Original.
    if isOriginal:
        score_trend *= 1.05
    # Hits-Stows.
    if stows == 0:
        score_trend *= 0.99
    else:
        if hits / stows > 200:
            z = (hits / stows - 200) / 1000
            if z <= 1:
                t = z
            else:
                t = 1
            score_trend *= (1 - t / 100)
    # Comments-Stows.
    if stows == 0:
        score_trend *= 0.99
    else:
        if comments / stows > 20:
            z = (hits / stows - 20) / 1000
            if z <= 1:
                t = z
            else:
                t = 1
            score_trend *= (1 - t / 100)
    # Parts.
    if parts != 0:
        score_trend *= (1 / parts) ** 0.01
    # Uploader.
    if highestUploaderScore != 0:
        if uploaderScore == 0:
            uploaderScore = score_trend
        if highestUploaderScore / uploaderScore <= 2000:
            score_trend *= (1 + ((highestUploaderScore - uploaderScore) / uploaderScore) / 10000)
        else:
            score_trend *= 1.2
    # Channel.
    if highestChannelScore != 0:
        if channelScore == 0:
            channelScore = score_trend
        if highestChannelScore / channelScore <= 1000:
            score_trend *= (1 + ((highestChannelScore - channelScore) / channelScore) / 2000)
        else:
            score_trend *= 1.5
    # Rank.
    if uploaderRank != 0:
        score_trend *= (1 + (uploaderRank - 1) / 10000)

    return int(score_trend)

def clear_screen():
    if is_panguine():
        os.system("clear")
    else:
        os.system("cls")


if __name__ == '__main__':
    # write_file("test", {"erwe": "wrwer"}, end=False)
    # print(date_to_ac_days(datetime.datetime(2007, 6, 4)))
    # print(date_to_ac_days(datetime.datetime.now()))
    # print(date_to_ac_weeks())
    # print(date_to_ac_weeks(datetime.datetime(2007, 6, 11)))
    print(calc_score(10000, 20, 30, 1, True, 0, 0, 0, 0, 2))
    clear_screen()
    print("123")
    pass
