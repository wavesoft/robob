
from robob.component import ComponentBase

class ParserBase(ComponentBase):
	"""
	Base class for implementing stream output parser
	"""

	def configure(self, config):
		"""
		[Public] Apply the specified configuration
		"""
		self.config = config

	def parse(self, line):
		"""
		[Public] Parse the specified line
		"""
		pass

	def reset(self):
		"""
		[Public] Reset the parser for a new stream
		"""
		pass

	def update(self, metric, value):
		"""
		[Private] Update the value of the specified metric
		"""
		pass

