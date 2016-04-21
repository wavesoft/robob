#!/usr/bin/python
import time
import signal
import pty, os, fcntl, termios
import threading

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

		# Close tty FD
		# os.close(self.fd)

		# Wrap file descriptors in file objects
		self.stdin = os.fdopen( fd_write, 'wb', 0 )
		self.stdout = os.fdopen( fd_read, 'rU', 0 )

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


class Threaded(threading.Thread):
	"""
	"""

	def run(self):
		"""
		"""

		p = PtyProcess( [ "/usr/bin/ssh", "lxplus.cern.ch" ] )

		time.sleep(5)
		print "- Sending password"
		p.stdin.write("DepiZumi1\r")
		p.stdin.close()
		# time.sleep(10)
		# p.terminate()

		print "- Reading lines"

		data = ""
		while True:

			# Read a chunk of data
			buf = os.read( p.fd, 1024)
			print "~~ %s" % buf
			if buf:

				# Stack
				data += buf

				# Process new lines
				while "\n" in data:
					(line, data) = data.split("\n",1)
					print ":: %s" % line

				# If there are more data don't consider incomplete
				# lines as part of the output
				if len(buf) < 1024:
					print ":> %s" % data
					data = ""

			elif data:

				# Consider this an incomplete line that just finished
				print ":> %s" % data
				data = ""

			# Check for process exit
			if p.poll() != None:
				print "<> Exited"
				break

		print "Exited with %s" % p.wait()


t = Threaded()
t.start()
t.join()
