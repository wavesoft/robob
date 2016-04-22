
from robob.pipe import PipeListener

class LogPipe(PipeListener):
	"""
	This class is used internally to log all stdout lines into a file
	"""

	def __init__(self, filename):
		"""
		"""
		PipeListener.__init__(self)
		self.fd = open(filename, "w")

	def got_stdout(self, line):
		"""
		Match the specified line against our configuration
		"""
		self.fd.write("%s\n" % line)

	def got_eof(self):
		"""
		Process end of stream
		"""
		self.fd.close()
