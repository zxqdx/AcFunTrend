'''
Created on 11, 24, 2013

@author: BigMoe
'''

import json
import sys

def is_panguine():
    '''如果系统的标志是企鹅它就是true喵～'''
    return not sys.platform.startswith("win")

def write_file(filename, content, form = "json", append = True, end = True):
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
    
if __name__ == '__main__':
    write_file("test", {"erwe":"wrwer"}, end = False)