"""
Created on 12/30/13

@author: zxqdx
"""

import json

if __name__ == "__main__":
    f = open("jsonTest.txt", "rb")
    s = f.read().decode("utf-8")

    print(s)

    p = '["{}"]'.format(s[215:218])
    print(p)

    print(json.loads(s, strict=False)[0])

    f.close()
    pass