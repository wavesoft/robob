
import time
import signal
import select
import logging

from threading import Thread
from subprocess import Popen, PIPE
from robob.metrics import Metrics, summarize

class TestStreamThread(Thread):
	"""
	A thread that runs a test
	"""

	def __init__(self, stream, *args, **kwargs):
		"""
		Initialize a test launcher
		"""
		Thread.__init__(self, *args, **kwargs)

		self.proc = None
		self.stream = stream
		self.returncode = 0

	def interrupt(self):
		"""
		Interrupt the subprocess
		"""

		# First gracefully kill the sub-process
		if self.proc:
			self.proc.send_signal(signal.SIGINT)

	def run(self):
		"""
		Main run function
		"""
		pipe = self.stream.pipe
		logger = logging.getLogger("driver.thread")

		# Apply delay
		if self.stream.delay:
			logger.info("Delaying")
			time.sleep( self.stream.delay )

		# Open process
		self.proc = proc = Popen( pipe.pipe_cmdline(), stdin=PIPE, stdout=PIPE, stderr=PIPE )

		# Send stdin
		proc.stdin.write( pipe.pipe_stdin() )
		proc.stdin.close()
		
		# Read stdout/err
		while True:
			reads = [ proc.stdout.fileno(), proc.stderr.fileno() ]
			ret = select.select(reads, [], [])

			# Read stdout/err
			for fd in ret[0]:
				if fd == proc.stdout.fileno():
					read = proc.stdout.readline()
					pipe.pipe_stdout( read )

				if fd == proc.stderr.fileno():
					read = proc.stderr.readline()
					pipe.pipe_stderr( read )

			# Wait for process to complete
			if p.poll() != None:
				break

		# Clear
		proc.stdout.close()
		proc.stderr.close()

		# Cleanup
		self.proc = None
		self.returncode = proc.returncode


class TestDriver:
	"""
	This class is responsible for starting the streams, monitoring
	their output, feeding them to the appropriate stream readers 
	and collecting the test results.
	"""

	def __init__(self, specs, test):
		"""
		Initialize a new test driver objet
		"""

		self.specs = specs
		self.test = test

		self.metrics = Metrics()
		self.metrics.configure( test )

		self.results = []

	def run(self):
		"""
		Start the tests on the test driver
		"""

		# Create all stream specifications on this context
		streams = self.specs.createStreams( self.test, self.metrics )

		# Reset metrics
		self.metrics.reset()

		# Launch them
		threads = []
		for s in streams:

			# Create a test stream thread
			t = TestStreamThread( s )

			# Start and keep
			t.start()
			threads.append(t)

		# Wait for the to complete
		for t in threads:
			t.join()

		# Collect results
		self.results.append( self.metrics.results() )

	def summarize(self):
		"""
		Summarize results
		"""

		# Summarize results
		return summarize( self.results )


