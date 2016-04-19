
import shlex
from robob.pipe import PipeBase

class Pipe(PipeBase):
	"""
	Implementation of the script pipe item
	"""

	def configure(self, config):
		"""
		Configure cmdline
		"""

		# Prepare cmdline
		self.cmdline = ["eval", config['script']]

	def pipe_cmdline(self):
		"""
		Return script components as cmdline
		"""
		return self.cmdline
