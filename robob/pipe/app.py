
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
		self.stdin = None

		# Parse arguments
		if 'args' in config:
			if type(config['args']) in [str, str]:
				self.args = shlex.split(config['args'])
			elif isinstance(config['args'], list):
				self.args = config['args']
			else:
				raise AssertionError("Application's arguments must be a string or list!")

		# Process stdin
		if 'stdin' in config:
			self.stdin = config['stdin']

		# Parse application environment
		self.env = {}
		if 'env' in config:
			n = "env.%s" % config['env']
			if not n in self.context:
				raise AssertionError("Unknown environment '%s' in application specs" % config['env'])
			self.env = self.context[ n ]

	def pipe_stdin(self):
		"""
		Return app stdin buffer (if any)
		"""
		return self.stdin

	def pipe_cmdline(self):
		"""
		Pipe local arguments to command-line
		"""

		# Prepare args
		args = [ self.binary ]
		args += self.args

		# Append child command-lines
		args += super(Pipe, self).pipe_cmdline()

		# If we have environment wrap in 'env'
		if self.env:
			env_prefix = [ 'env' ]
			for k,v in self.env.items():
				env_prefix.append( "%s=%s" % (k,v) )

			# Update with prefix
			args = env_prefix + args

		# Return new arguments
		return args

