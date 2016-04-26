
import errno
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
		self.fd = None

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
		new = termios.tcgetattr(self.fd)
		new[3] = new[3] & ~termios.ECHO
		termios.tcsetattr(self.fd, termios.TCSADRAIN, new)

	def close(self):
		"""
		Close FDs
		"""

		if self.fd:
			if self.returncode != None:
				os.close(self.fd)
			self.fd = None

	def send_signal(self, sig):
		"""
		Send signal to process
		"""
		try:
			os.kill(self.pid, sig)
		except (OSError, IOError) as e:
			return

	def terminate(self):
		"""
		Send kill signal to process
		"""
		try:
			os.kill(self.pid, signal.SIGTERM)
		except (OSError, IOError) as e:
			return

	def poll(self):
		"""
		Check if thread has exited
		"""

		# Get PID
		if self.returncode is None:
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
		self.interrupted = False
		self.interruptReason = ""
		self.logger = logging.getLogger("stream.%s" % self.stream.name)
		self.lastactivity = time.time()

	def interrupt(self, reason="User interrupt", timeout=5):
		"""
		Interrupt the subprocess
		"""

		# Skip if already interrupted
		if self.interrupted:
			return

		# Mark as interrupted
		self.logger.critical("Interrupting stream")
		self.interrupted = True
		self.interruptReason = reason

		# First gracefully kill the sub-process
		if self.proc:

			# First send sigint
			self.proc.send_signal( signal.SIGINT )

			# Wait 5 seconds to 
			t_timeout = time.time() + timeout
			while True:

				# Check if this was enough
				if self.proc.poll() != None:
					self.logger.warn("Stream interrupted")
					break

				# Check for timeouts
				if time.time() > t_timeout:

					# Terminate
					self.proc.terminate()
					self.logger.warn("Stream terminated")
					break

			# Reap process
			self.proc.close()
			self.proc = None

			# Set return code to -1
			self.returncode = -1

	def run(self):
		"""
		Main run function
		"""
		pipe = self.stream.pipe

		# Apply delay
		if self.stream.delay:
			self.logger.info("Delaying for %i seconds" % self.stream.delay)
			q_time = time.time() + self.stream.delay
			while time.time() < q_time:
				time.sleep(0.1)
				if self.interrupted:
					self.logger.warn("Interrupted while in delay")
					return

		# Prepare expiration time
		t_expire = None
		if self.stream.timeout:
			t_expire = time.time() + self.stream.timeout

		# Open process
		self.logger.debug("Process starting %r" % pipe.pipe_cmdline())
		self.proc = proc = PtyProcess( pipe.pipe_cmdline() )

		# Get a sequence of optional expect entries
		expect_out = pipe.pipe_expect_stdout()
		expect_err = pipe.pipe_expect_stderr()
		self.has_expect = True

		# Send stdin if there are no expect entries
		if (len(expect_out) == 0) and (len(expect_err) == 0):
			self.logger.debug("Sending STDIN payload")
			try:
				os.write( proc.fd, pipe.pipe_stdin() )
				os.write( proc.fd, "\x04") # End-of-transmission
			except (OSError, IOError) as e:
				self.logger.warn("%s occured: %s" % (e.__class__.__name__, str(e)))
				self.interrupt("%s: %s" % (e.__class__.__name__, str(e)))
				return
			self.has_expect = False

		# Flag that keeps line polling activ
		active = True

		# Helper function to handle lines
		def handle_line(read):

			# Consider this an "activity" action
			self.lastactivity = time.time()

			# Skip empty lines
			if not read.strip():
				return

			# Ignore '\r'
			read = read.replace("\r", "")

			# Guard against exceptions
			self.logger.debug("STDIN: %s" % read)
			try:

				# First apply over expect
				handled = False
				for i in range(0, len(expect_out)):
					if expect_out[i].matches( read ):
						self.logger.debug("Expect matched as /%s/ on stdin" % str(expect_out[i]))
						os.write( proc.fd, expect_out[i].render() )
						del expect_out[i]
						handled = True
						break

				# If not handled, pass to pipe
				if not handled:
					pipe.pipe_stdout( read )

			except Exception as e:

				import traceback
				traceback.print_exc()

				# In case something went wrong while processing the streams,
				# kill the process
				self.logger.error("%s occured: %s" % (e.__class__.__name__, str(e)) )
				active = False

				# Interrupt
				self.interrupt("%s: %s" % (e.__class__.__name__, str(e)))
				return

			# If we have processed all expect entries, send STDIN
			if self.has_expect and (len(expect_out) == 0) and (len(expect_err) == 0):
				self.logger.debug("No more expects left, sending STDIN payload")
				os.write( proc.fd, pipe.pipe_stdin() )
				os.write( proc.fd, "\x04") # End-of-transmission
				self.has_expect = False

		# Read stdout/err
		self.logger.debug("Processing output")
		data = ""
		data_flush_t = 0
		while active:
			ts = time.time()

			# If interrupted, quit
			if self.interrupted:
				pipe.pipe_close()
				return

			# Forward incomplete data as incomplete line
			if data and (ts > data_flush_t):
				handle_line(data)
				data = ""

			# Wait for data within 100ms
			if proc.fd in select.select([proc.fd], [], [], 0.1)[0]:

				# If interrupted, quit
				if self.interrupted:
					pipe.pipe_close()
					return

				# Read data
				buf = os.read( proc.fd, 4096)
				if buf:

					# Stack buffers
					data += buf

					# Replace windows newlines & process lines
					data = data.replace("\r\n", "\n")
					while "\n" in data:
						(line, data) = data.split("\n",1)
						handle_line(line)

					# Note when we received the data
					# in order to forward them as-is as
					# incomplete line data after a timeout
					data_flush_t = ts + 0.1

			# Check for process exit
			if proc.poll() != None:
				self.logger.debug("Process exited with code %i" % proc.returncode)
				break

			# Check if timeout expired
			if t_expire and (ts > t_expire):
				self.logger.critical("Timeout of %s seconds expired" % self.stream.timeout)
				self.interrupt("Timeout after %s sec" % self.stream.timeout)
				pipe.pipe_close()
				return

			# Check if idle timeout expired
			if self.stream.idletimeout and (ts > (self.lastactivity + self.stream.idletimeout)):
				self.logger.critical("Timeout after %s seconds of inactivity" % self.stream.idletimeout)
				self.interrupt("Timeout after %s seconds of inactivity" % self.stream.idletimeout)
				return

		# If not interrupted, clean shutdown
		if not self.interrupted and self.proc:
			pipe.pipe_close()
			proc.close()
			self.returncode = proc.returncode
			self.proc = None

		# Cleanup
		if self.returncode != 0:
			self.logger.warn("Stream closed with error code=%i" % proc.returncode)
		else:
			self.logger.info("Stream closed successfuly")

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
		self.logger = logging.getLogger("driver")

		self.metrics = Metrics()
		self.metrics.configure( test )

		self.results = []
		self.lastResults = None
		self.lastStatus = ""
		self.lastComment = ""

	def run(self, iteration):
		"""
		Start the tests on the test driver
		"""

		# Create all stream specifications on this context
		streams = self.specs.createStreams( self.test, self.metrics, iteration )

		# Reset metrics
		self.metrics.reset()
		self.lastStatus = "Completed"
		self.lastComment = ""

		# Launch them
		self.threads = []
		self.logger.debug("Starting %i streams" % len(streams))
		for s in streams:

			# Skip inactive streams
			if not s.active:
				self.logger.info("Not starting inactive stream '%s'" % s.name)
				continue

			# Create a test stream thread
			t = TestStreamThread( s )

			# Start and keep
			t.start()
			self.threads.append(t)

		# Wait for all threads to complete
		self.logger.debug("Waiting for stream threads to exit")
		hasAlive = True
		hasInterrupt = False
		while hasAlive:

			# Check status of all items
			hasAlive = False
			for t in self.threads:
				if t.interrupted:
					hasInterrupt = True
					break
				if t.is_alive():
					hasAlive = True
					break

			# If something interrupted, interrupt everything
			if hasInterrupt:
				self.logger.warn("Thread '%s' interrupted, so collapsing this test-case" % t.stream.name)
				self.interrupt(t.interruptReason)
				break

			# Otherwise wait for a sec before retry
			if hasAlive:
				time.sleep(0.1)

		# Update exit code status
		for t in self.threads:
			if t.returncode != 0:
				if self.lastComment:
					self.lastComment += "; "
				self.lastComment += "%s returned=%i" % (t.stream.name, t.returncode)

				# Switch to error only if not completed (it might be timeout for example)
				if self.lastStatus == "Completed":
					self.lastStatus = "Error"

		# Reap threads
		for t in self.threads:
			t.join()

		# Reset thread list
		self.threads = []

		# Collect results
		self.logger.debug("Threads exited, collecting results")
		self.lastResults = self.metrics.results()
		self.results.append( self.lastResults )

	def summarize(self):
		"""
		Summarize results
		"""

		# Summarize results
		return summarize( self.results )

	def interrupt(self, reason="Interrupted"):
		"""
		Interrupt current run
		"""

		# Collect results
		self.logger.warn("Driver interrupted (%s), stopping all threads" % reason)
		self.lastStatus = reason
		self.lastResults = self.metrics.results()
		self.results.append( self.lastResults )

		# Interrupt and join all threads
		for t in self.threads:
			self.logger.debug("Interrupting stream thread %s" % t.stream.name)
			t.interrupt()
			self.logger.debug("Joining stream thread %s" % t.stream.name)
			t.join()
