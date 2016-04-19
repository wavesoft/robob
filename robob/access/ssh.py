
from robob.pipe import PipeBase

class Pipe(PipeBase):
	"""
	SSH Tunelling pipe
	"""

	def configure(self, config):
		"""
		Configure access object
		"""

		# Prepare command line
		self.username = config['username']
		self.args = []

		# Prepare private key or password
		if 'key' in config:
			self.args += [ '-i', config['key'] ]

	def pipe_cmdline(self):
		"""
		Pipe local arguments to command-line
		"""

		# Prepare args
		args = [ "/usr/bin/ssh" ]
		args += [ "%s@%s" % (self.username, self.context["node.host"]) ]
		args += [ "--" ]
		args += self.args

		# Append child command-lines
		args += super(Pipe, self).pipe_cmdline()

		# Return new arguments
		return args
