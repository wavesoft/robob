
import shlex
from robob.pipe import PipeBase

class Pipe(PipeBase):
	"""
	Implementation of the application pipe item
	"""

	def configure(self, config):
		"""
		Configure cmdline
		"""

		# Prepare
		self.binary = config['binary']
		self.args = []

		# Parse arguments
		if 'args' in config:
			if type(config['args']) in [str, unicode]:
				self.args = shlex.split(config['args'])
			elif isinstance(config['args'], list):
				self.args = config['args']
			else:
				raise AssertionError("Application's arguments must be a string or list!")

	def pipe_cmdline(self):
		"""
		Pipe local arguments to command-line
		"""

		# Prepare args
		args = [ self.binary ]
		args += self.args

		# Append child command-lines
		args += super(Pipe, self).pipe_cmdline()

		# Return new arguments
		return args

