
from subprocess import Popen, PIPE
from robob.context import Context

class ExecPipelineItem(object):
	"""
	A chainable pipeline item
	"""

	def pipe_execute(self, cmdline):
		"""
		Chainable command-line
		"""
		return cmdline

	def pipe_stdin(self, stdin):
		"""
		Pipe stdin
		"""
		return stdin

	def pipe_stdout(self, stdout, stderr):
		"""
		Chainable pipes
		"""
		# Pass-through
		return (stdout, stderr)

class ExecPipeline(object):
	"""
	A pipeline is a sequence of actions to be executed that can
	be requested to be executed on demand.
	"""

	def __init__(self):
		"""
		Initialize the pipeline
		"""
		self.sequence = []

	def run(self, cmdline, stdin):
		"""
		Run the pipeline and return a popen object
		"""

		# Calculate command-line
		cmd = cmdline
		for s in self.sequence:
			cmd = s.pipe_execute( s, cmd )

		# Open a process there
		self.proc = Popen( cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE )

		# Generate stdin buffer
		sin = stdin
		for s in self.sequence:
			sin = s.pipe_stdin( sin )

		# Pipe everything to stdin
		self.proc.stdin.write(sin)

		# Chain pipes
		stdout = self.proc.stdout
		stderr = self.proc.stderr
		for s in self.sequence:
			(stdout, stderr) = s.pipe_stdout( stdout, stderr )


