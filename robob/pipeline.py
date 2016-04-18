
from subprocess import Popen, PIPE
from robob.context import Context

class ExecPipelineItem(object):
	"""
	A chainable pipeline item
	"""

	def execute(self, cmdline):
		"""
		Chainable command-line
		"""
		return cmdline

	def chain(self, stdin, stdout, stderr):
		"""
		Chainable pipes
		"""
		# Pass-through
		return (stdin, stdout, stderr)

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

	def run(self, cmdline):
		"""
		Run the pipeline and return a popen object
		"""

		# Calculate command-line
		cmd = cmdline
		for s in self.sequence:
			cmd = s.execute( s, cmd )

		# Open a process there
		self.proc = Popen( cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE )

		# Chain pipes
		stdin = self.proc.stdin
		stdout = self.proc.stdout
		stderr = self.proc.stderr
		for s in self.sequence:
			(stdin, stdout, stderr) = s.chain( stdin, stdout, stderr )


