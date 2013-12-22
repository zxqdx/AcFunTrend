'''
Created on 11, 24, 2013

@author: BigMoe
'''

import json
import sys
import os
import time
import datetime


def is_panguine():
    '''
    Returns true if it is Linux.
    '''
    return not sys.platform.startswith("win")


def is_file(filepath):
    """
    Returns true if the file exists.
    """
    return os.path.isfile(filepath)


def write_file(filename, content, form="json", append=True, end=True):
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
        if form == None:
            file.write(content)
        elif form == "json":
            file.write(json.dumps(content))
        if end:
            if is_panguine():
                end_str = "\r"
            else:
                end_str = "\n"
            file.write(end_str)
        file.close()
    except Exception as e:
        raise e
        return False


def remove_file(filename):
    try:
        os.remove(filename)
    except Exception as e:
        return False


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

def date_to_ac_days(date=None):
    if not date:
        date = datetime.datetime.now()
    start = datetime.datetime(2007,6,4)
    return (date - start).days + 1

def get_page(host, url, port=80, timeout=None, form=None, retryNum=-1, sleep=1, logger=None):
    def get_result(resultWrapper):
        resultWrapper[0] = pool.request('GET', url)
        resultWrapper[1] = str(resultWrapper[0].data)

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
        return json.loads(resultWrapper[1])
    else:
        raise NotImplementedError("Unknown format: {}".format(form))

if __name__ == '__main__':
    # write_file("test", {"erwe": "wrwer"}, end=False)
    print(date_to_ac_days(datetime.datetime(2007,6,4)))
    print(date_to_ac_days(datetime.datetime.now()))
