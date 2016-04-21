
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

	def __init__(self, match, callback=None, send=None):
		"""
		Initialize a pipe expect entry
		"""

		# Initialize properties
		self.repr = match
		self.match = re.compile(match)
		self.callback = callback
		self.send = send

		# Match function result
		self.found = None

	def matches(self, line):
		"""
		Test if the pipe expects
		"""

		# Return the match if found, None otherwise
		self.found = self.match.search( line )
		return self.found

	def render(self):
		"""
		Render the result to send after expect
		"""

		# Return data if only data specified
		if self.send:
			return self.send

		# Otherwise use callback
		elif self.callback:
			return self.callback( self.found )

		# Nothing found? Return None
		else:
			return ""

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
