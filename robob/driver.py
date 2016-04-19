
class TestDriver:
	"""
	This class is responsible for starting the streams, monitoring
	their output, feeding them to the appropriate stream readers 
	and collecting the test results.
	"""

	def __init__(self, test, streams):
		"""
		Initialize a new test driver objet
		"""
		self.test = test
		self.streams = streams

	def test_thread(self):
		"""
		The thread that is responsible for the thread I/O
		"""
		pass

	def run(self):
		"""
		Start the tests on the test driver
		"""
		pass

	