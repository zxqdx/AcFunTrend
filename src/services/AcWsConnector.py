'''
Created on Nov 24, 2013

@author: zxqdx
'''

# Imports parent directory to sys.path
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AcWsConnector(object):
	"""
	The Wrapper class for this module.
	"""
	def __init__(self):
		super(AcWsConnector, self).__init__()

class AcWsSender(object):
	"""docstring for AcWsSender"""
	def __init__(self, arg):
		super(AcWsSender, self).__init__()
		self.arg = arg

class AcWsReceiver(object):
	"""docstring for AcWsReceiver"""
	def __init__(self, arg):
		super(AcWsReceiver, self).__init__()
		self.arg = arg
		