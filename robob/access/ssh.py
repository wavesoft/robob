
import logging
from robob.pipe import PipeBase, PipeExpect

class Pipe(PipeBase):
	"""
	SSH Tunelling pipe
	"""

	def __init__(self, *args):
		"""
		Initialize ssh pipe
		"""
		PipeBase.__init__(self, *args)
		self.logger = logging.getLogger("access.ssh")

	def configure(self, config):
		"""
		Configure access object
		"""

		# Prepare command line
		self.username = config['username']
		self.args = []
		self.password = None
		self.host = None

		self.sent_line = ""

		# Prepare private key or password
		if 'key' in config:
			self.args += [ '-i', config['key'] ]
		elif 'password' in config:
			self.password = config['password']

		# Override host if defiend
		if 'host' in config:
			self.host = config['host']

	def pipe_cmdline(self):
		"""
		Pipe local arguments to command-line
		"""

		# Get hostname
		host = self.host
		if host is None:
			host = self.context["node.host"]

		# Prepare args
		args = [ "/usr/bin/ssh", "-t", "-q", "-o", "UserKnownHostsFile=/dev/null", "-o", "StrictHostKeyChecking=no" ]
		if self.password:
			args += [ "-o", "PreferredAuthentications=password" ]
		args += [ "%s@%s" % (self.username, host) ]
		args += self.args
		args += [ "--" ]

		# Append child command-lines
		args += super(Pipe, self).pipe_cmdline()

		# Return new arguments
		return args

	def expect_password(self, expect, match, line):
		"""
		Callback when a password prompt is encountered
		"""

		# If we don't have a match, and we have sent a password
		# the password was correct
		if not match:
			if self.sent_line:
				self.logger.info("Connected to %s" % self.host)
				expect.do_remove = True

		# Otherwise check for password
		else:

			# If the matched line is the same like the line
			# we went a password to, it means that the password
			# was invalid
			if self.sent_line == line:
				raise IOError("Invalid password for %s" % self.host)

			# If we have already sent a line, and the received line
			# does not match, that's OK, we have a chained SSH call
			elif self.sent_line:
				self.logger.info("Connected to %s" % self.host)
				expect.do_remove = True

			# Send authentication information
			else:
				self.sent_line = line
				self.logger.info("Authenticating to %s" % self.host)
				expect.do_reply = self.password + "\r\n\r\n"

	def pipe_expect_stdout(self):
		"""
		Add an expect entry to send password when requested
		"""

		# Prepare expect
		expect = []
		if self.password:
			expect.append( PipeExpect( r"[Pp]assword:", callback=self.expect_password, call_always=True ) )

		# Forward
		return expect + PipeBase.pipe_expect_stdout(self)

