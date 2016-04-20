
import time
import signal
import select
import logging

import pty, os, fcntl, termios

from threading import Thread
from subprocess import Popen, PIPE
from robob.metrics import Metrics, summarize

class PtyProcess:

	def __init__(self, cmdline, **kwargs):
		"""
		Initialize a pty process control
		"""

		self.cmdline = cmdline
		self.kwargs = kwargs
		self.returncode = None

		# Fork into a new pty
		self.pid, self.fd = pty.fork()
		if self.pid == 0:
			self._init_child()
		else:
			self._init_host()

	def _init_child(self):
		"""
		Child process
		"""
		os.execv( self.cmdline[0], self.cmdline )

	def _init_host(self):
		"""
		Host process
		"""

		# Disable echo in the tty
		old = termios.tcgetattr(self.fd)
		new = termios.tcgetattr(self.fd)
		new[3] = new[3] & ~termios.ECHO
		termios.tcsetattr(self.fd, termios.TCSADRAIN, new)

		# Create an FD for reading
		fd_read = os.dup(self.fd)
		fcntl.fcntl(fd_read, fcntl.F_SETFL, os.O_RDONLY)

		# Create an FD for writing
		fd_write = os.dup(self.fd)
		fcntl.fcntl(fd_write, fcntl.F_SETFL, os.O_WRONLY)

		# Wrap file descriptors in file objects
		self.stdin = os.fdopen( fd_write, 'wb', 0 )
		self.stdout = os.fdopen( fd_read, 'rb', 0 )

	def send_signal(self, sig):
		"""
		Send signal to process
		"""
		os.kill(self.pid, sig)

	def terminate(self):
		"""
		Send kill signal to process
		"""
		os.kill(self.pid, signal.SIGTERM)

	def poll(self):
		"""
		Check if thread has exited
		"""

		# Get PID
		try:
			pid, sts = os.waitpid(self.pid, os.WNOHANG)
			if pid == self.pid:
				self._handle_exitstatus(sts)
		except os.error as e:
			self.returncode = None

		return self.returncode

	def wait(self):
		"""
		Wait for thread to exit and return exit code
		"""

		# Get PID
		while self.returncode is None:
			try:
				pid, sts = os.waitpid(self.pid, 0)
				if pid == self.pid:
					self._handle_exitstatus(sts)
			except (OSError, IOError) as e:
				if e.errno == errno.EINTR:
					continue
			except os.error as e:
				self.returncode = None

		return self.returncode

	def _handle_exitstatus(self, sts, _WIFSIGNALED=os.WIFSIGNALED,
			_WTERMSIG=os.WTERMSIG, _WIFEXITED=os.WIFEXITED,
			_WEXITSTATUS=os.WEXITSTATUS):
		# This method is called (indirectly) by __del__, so it cannot
		# refer to anything outside of its local scope.
		if _WIFSIGNALED(sts):
			self.returncode = -_WTERMSIG(sts)
		elif _WIFEXITED(sts):
			self.returncode = _WEXITSTATUS(sts)
		else:
			# Should never happen
			raise RuntimeError("Unknown child exit status!")


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
		logger = logging.getLogger("stream.%s" % self.stream.name)

		# Apply delay
		if self.stream.delay:
			logger.info("Delaying for %i seconds" % self.stream.delay)
			time.sleep( self.stream.delay )


		# Open process
		logger.debug("Process starting %r" % pipe.pipe_cmdline())
		self.proc = proc = PtyProcess( pipe.pipe_cmdline() )

		# Get a sequence of optional expect entries
		expect_out = pipe.pipe_expect_stdout()
		expect_err = pipe.pipe_expect_stderr()
		self.has_expect = True

		# Send stdin if there are no expect entries
		if (len(expect_out) == 0) and (len(expect_err) == 0):
			logger.debug("Sending STDIN payload")
			os.write( proc.fd, pipe.pipe_stdin() )
			os.write( proc.fd, "\x04") # End-of-transmission
			self.has_expect = False

		# Helper function to handle lines
		def handle_line(read):

			# Skip empty lines
			if not read.strip():
				return

			# Guard against exceptions
			logger.debug("STDIN: %s" % read)
			try:

				# First apply over expect
				handled = False
				for i in range(0, len(expect_out)):
					if expect_out[i].matches( read ):
						logger.debug("Expect matched as /%s/ on stdin" % str(expect_out[i]))
						os.write( proc.fd, expect_out[i].render() )
						del expect_out[i]
						handled = True
						break

				# If not handled, pass to pipe
				if not handled:
					pipe.pipe_stdout( read )

			except Exception as e:

				# In case something went wrong while processing the streams,
				# kill the process
				logger.error("%s occured: %s" % (e.__class__.__name__, str(e)) )

				# First send sigint
				proc.send_signal( signal.SIGINT )

				# Wait 5 seconds to 
				timeout = time.time() + 5
				while True:

					# Check if this was enough
					if proc.poll() != None:
						logger.warn("Stream interrupted")
						proc.stdout.close()
						self.proc = None
						self.returncode = -1
						return

					# Check for timeouts
					if time.time() > timeout:

						# Terminate
						proc.terminate()
						logger.warn("Stream terminated")

						# Cleanup
						proc.stdout.close()
						self.proc = None
						self.returncode = -1
						return

			# If we have processed all expect entries, send STDIN
			if self.has_expect and (len(expect_out) == 0) and (len(expect_err) == 0):
				logger.debug("No more expects left, sending STDIN payload")
				os.write( proc.fd, pipe.pipe_stdin() )
				os.write( proc.fd, "\x04") # End-of-transmission
				self.has_expect = False

		# Read stdout/err
		logger.debug("Processing output")
		data = ""
		while True:

			# Read a chunk of data
			buf = os.read( proc.fd, 1024)
			if buf:

				# Process lines
				data += buf
				while "\n" in data:
					(line, data) = data.split("\n",1)
					handle_line(line)

				# If there are more data don't consider incomplete
				# lines as part of the output
				if len(buf) < 1024:
					handle_line(data)
					data = ""

			elif data:

				# Consider this an incomplete line that just finished
				handle_line(data)
				data = ""

			# Check for process exit
			if proc.poll() != None:
				logger.debug("Process exited with code %i" % proc.returncode)
				break


		# Clear
		proc.stdout.close()

		# Cleanup
		self.proc = None
		self.returncode = proc.returncode
		if self.returncode > 0:
			logger.warn("Stream exited with code=%i" % proc.returncode)
		else:
			logger.debug("Stream exited")

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
		self.lastResults = None

	def run(self):
		"""
		Start the tests on the test driver
		"""
		logger = logging.getLogger("driver")

		# Create all stream specifications on this context
		streams = self.specs.createStreams( self.test, self.metrics )

		# Reset metrics
		self.metrics.reset()

		# Launch them
		threads = []
		logger.debug("Starting %i streams" % len(streams))
		for s in streams:

			# Create a test stream thread
			t = TestStreamThread( s )

			# Start and keep
			t.start()
			threads.append(t)

		# Wait for the to complete
		logger.debug("Waiting for stream threads to exit")
		for t in threads:
			t.join()

		# Collect results
		logger.debug("Threads exited, collecting results")
		self.lastResults = self.metrics.results()
		self.results.append( self.lastResults )

	def summarize(self):
		"""
		Summarize results
		"""

		# Summarize results
		return summarize( self.results )


