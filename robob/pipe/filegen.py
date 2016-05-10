
import random
import string
from robob.pipe import PipeBase

class Pipe(PipeBase):
	"""
	Implementation of the file generator pipe item
	"""

	def configure(self, config):
		"""
		Configure cmdline
		"""

		# Prepare file generator
		self.name = config['name']
		self.path = config['path']
		self.contents = config['contents']

	def pipe_cmdline(self):
		"""
		Return script components as cmdline
		"""

		# A unique contents separator
		eof_indicator = "CONTENTS_"
		eof_indicator += ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))

		# Prepare script
		genscript  = "WFILE=\"%s\"\n" % self.path
		genscript += "cat <<'%s' > $WFILE\n" % eof_indicator
		genscript += self.contents
		genscript += "\n%s\n" % eof_indicator

		# Return script that generates the given file
		return [ "eval", genscript ]
