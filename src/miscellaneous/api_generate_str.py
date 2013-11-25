class GeneratedStr(object):
	def __init__(self, s=""):
		self.s = s
	def __str__(self):
		return self.s
	def __add__(self, s):
		self.s += s
		return GeneratedStr(self.s)

s = GeneratedStr()