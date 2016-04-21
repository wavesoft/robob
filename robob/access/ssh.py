
import logging
from robob.pipe import PipeBase, PipeExpect

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
		self.password = None

		# Prepare private key or password
		if 'key' in config:
			self.args += [ '-i', config['key'] ]
		elif 'password' in config:
			self.password = config['password']

	def pipe_cmdline(self):
		"""
		Pipe local arguments to command-line
		"""

		# Prepare args
		args = [ "/usr/bin/ssh", "-t", "-q", "-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no" ]
		if self.password:
			args += [ "-o", "PreferredAuthentications=password" ]
		args += [ "%s@%s" % (self.username, self.context["node.host"]) ]
		args += self.args
		args += [ "--" ]

		# Append child command-lines
		args += super(Pipe, self).pipe_cmdline()

		# Return new arguments
		return args

	def pipe_expect_stdout(self):
		"""
		Add an expect entry to send password when requested
		"""

		# Prepare expect
		expect = []
		if self.password:
			expect.append( PipeExpect( r"[Pp]assword:", send=self.password+"\r" ) )

		# Forward
		return expect + PipeBase.pipe_expect_stdout(self)

