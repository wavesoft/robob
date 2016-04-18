
from robob.access import Access

class Access(Access):
	"""
	SSH Tunelling application
	"""

	def configure(self, specs, config):
		"""
		Configure access object
		"""

		this.user = ""
		this.host = ""

		# Factory a gateway
		this.gateway = None
		if 'gateway' in config:
			this.gateway = specs.accessFactory( config['gateway'] )

	def execute(self, cmdline):
		"""
		Chain cmdline to ssh
		"""

		# Prepare cmdline
		cmdline = "ssh %s@%s -- %s" % (self.user, self.host, cmdline)

		# Nest cmdline
		if this.gateway:
			cmdline = this.gateway.execute( cmdline )

		# Return new cmdline
		return cmdline

	def chain(self, stdin, stdout, stderr):
		"""
		Chainable pipes
		"""

		# Nest gateway if needed
		if this.gateway:
			return this.gateway.chain( stdin, stdout, stderr )

		# Pass-through
		return (stdin, stdout, stderr)

