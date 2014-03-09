"""
Created on 1/6/14

@author: zxqdx
"""

# Imports parent directory to sys.path
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import urllib.parse
import urllib.request


def main():
    url = 'http://translate.google.com/translate_tts'
    user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
    values = {'ie': 'UTF-8',
              'tl': 'zh-CN',
              'q': '你好吗哈哈哈'}
    headers = {'User-Agent': user_agent}

    data = urllib.parse.urlencode(values)
    data = data.encode('utf-8')
    req = urllib.request.Request(url, data, headers)
    response = urllib.request.urlopen(req)
    the_page = response.read()
    file = open('test.mp3', 'wb')
    file.write(the_page)
    file.close()

if __name__ == "__main__":
    main()