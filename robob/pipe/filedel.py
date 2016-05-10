
import random
import string
from robob.pipe import PipeBase

class Pipe(PipeBase):
	"""
	Implementation of the file deleting pipe item
	"""

	def configure(self, filename):
		"""
		Configure cmdline
		"""

		# The filename to delete
		self.name = filename

	def pipe_cmdline(self):
		"""
		Return script components as cmdline
		"""

		# Return script that deletes the given file if it exists
		delscript = "[ -f \"%s\" ] && rm \"%s\"" % (self.name, self.name)
		return [ "eval", delscript ]
