'''
Created on 11, 24, 2013

@author: BigMoe
'''

import json
import sys
import os


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
        end_str = ""
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
        return False


def remove_file(filename):
    try:
        os.remove(filename)
    except Exception as e:
        return False


def try_until_sign(sign, tryFunc, errorFunc=None, failedFunc=None, retryNum=-1, sleep=1):
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
        retry += 1
    if not isSuccess:
        if failedFunc:
            failedFunc()
    return isSuccess

if __name__ == '__main__':
    write_file("test", {"erwe": "wrwer"}, end=False)
