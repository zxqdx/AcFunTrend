# Imports parent directory to sys.path
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def parse_json(s):
    import json
    while True:
        try:
            return json.loads(s)
        except ValueError as e:
            err = str(e)
            import re
            pattern = re.compile(r"\(char (\d*)\)")
            escapeIndex = int(pattern.findall(err)[0])
            s = s[:escapeIndex] + s[(escapeIndex+2):]
        except Exception as e:
            raise e

from websocket import create_connection
from miscellaneous import gadget
ws = create_connection("ws://103.244.232.84:8085/ws")
ws.send('{func:"auth","key":"3fe3f2b10bbad0a1","secret":"e0c64e4b2c6eba73a1bb2b5ba2a854bbc1fa592f"}')
result =  ws.recv()
print("Received '%s'" % result)
# ws.send('{func:"fullcontent.get",id:"99999999",next:"true",desc:"true",requestId:"papaya5"}')
ws.send('{func:"fullcontent.get",id:"42901",requestId:"papaya5"}')
# ws.send('{func:"user.get",id:"2",requestId:"papaya2"}')
result =  ws.recv()
print("Received '{}'".format(parse_json(result)))
ws.close()


# test