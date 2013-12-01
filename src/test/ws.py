# Imports parent directory to sys.path
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from websocket import create_connection

from miscellaneous import gadget
ws = create_connection("ws://59.175.227.54:88/ws")
ws.send('{func:"auth","key":"3fe3f2b10bbad0a1","secret":"e0c64e4b2c6eba73a1bb2b5ba2a854bbc1fa592f"}')
result =  ws.recv()
print("Received '%s'" % result)
ws.send('{func:"user.get",id:"1",requestId:"papaya1"}')
ws.send('{func:"user.get",id:"2",requestId:"papaya2"}')
result =  ws.recv()
print("Received '{}'".format(result))
ws.close()