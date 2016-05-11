
import logging
import re
from robob.component import ComponentBase

class PipeListener(object):
	"""
	A class that can receives stdout/stderr events
	"""

	def got_stdout(self, line):
		"""
		Process an stdout line
		"""
		pass

	def got_stderr(self, line):
		"""
		Process an stderr line
		"""
		pass

	def got_eof(self):
		"""
		Process end of stream
		"""
		pass

class PipeExpect(object):
	"""
	A pipe expect entry
	"""

	def __init__(self, match, callback=None, call_always=False, send=None, repeat=False):
		"""
		Initialize a pipe expect entry
		"""

		# Initialize properties
		self.repr = match
		self.match = re.compile(match)
		self.callback = callback
		self.send = send
		self.repeat = repeat
		self.sent = False
		self.call_always = call_always

		# Get a logger
		self.logger = logging.getLogger("pipe.expect")

		# Flags for driver
		self.do_reply = None
		self.do_remove = False

	def apply(self, line):
		"""
		Apply expect rule on the specified line and update
		the do_reply and do_remove flags accordingly
		"""

		# Reset flags
		self.do_reply = None
		self.do_remove = False

		# Pass through if not found
		found = self.match.search( line )
		if not found:

			# If we must always call the callback, call it now
			if self.call_always:
				self.callback( self, None, line )

			# Don't continue
			return

		# If we have a string reply right away
		if self.send:
			self.do_reply = self.send
			self.do_remove = not self.repeat

		# Otherwise pass request to callback
		elif self.callback:
			self.callback( self, found, line )

		# Error
		else:
			self.logger.warn("Empty expect object encountered!")
			self.do_remove = True

	def __str__(self):
		return self.repr

class PipeBase(ComponentBase):
	"""
	A chainable pipe object
	"""

	def __init__(self, context):
		"""
		Initialize pipe base
		"""
		super(PipeBase, self).__init__(context)

		self.pipes = []
		self.listeners = []

	def configure(self, specs):
		"""
		Configure specs
		"""
		pass

	def pipe_stdin(self):
		"""
		Return the pipe's stdin buffer
		"""
		stdin = ""
		for p in self.pipes:
			stdin += p.pipe_stdin()
		return stdin

	def pipe_cmdline(self):
		"""
		Return pipe's cmdline
		"""
		cmdline = []
		for p in self.pipes:
			cmdline += p.pipe_cmdline()
		return cmdline

	def pipe_stdout(self, stdout):
		"""
		Handle stdout line
		"""

		# Trigger to listeners
		for l in self.listeners:
			l.got_stdout( stdout )

		# Forward to children
		for p in self.pipes:
			p.pipe_stdout( stdout )

	def pipe_stderr(self, stderr):
		"""
		Handle stderr line
		"""

		# Trigger to listeners
		for l in self.listeners:
			l.got_stderr( stderr )

		# Forward to children
		for p in self.pipes:
			p.pipe_stderr( stderr )

	def pipe_expect_stdout(self):
		"""
		Collect expect entries on stdout
		"""
		entries = []
		for p in self.pipes:
			entries += p.pipe_expect_stdout()
		return entries

	def pipe_expect_stderr(self):
		"""
		Collect expect entries on stdout
		"""
		entries = []
		for p in self.pipes:
			entries += p.pipe_expect_stderr()
		return entries

	def pipe_close(self):
		"""
		Request to close all pipe resources
		"""

		# Trigger to listeners
		for l in self.listeners:
			l.got_eof()

		# Forward to children
		for p in self.pipes:
			p.pipe_close()

	def plug(self, pipe):
		"""
		Plug a pipe in the this
		"""
		if not isinstance(pipe, PipeBase):
			raise AssertionError("The given pipe object is not instance of PipeBase")
		self.pipes.append(pipe)

	def listen(self, listener):
		"""
		Listen for input events
		"""
		if not isinstance(listener, PipeListener):
			raise AssertionError("The given listener object is not instance of PipeListener")
		self.listeners.append(listener)
