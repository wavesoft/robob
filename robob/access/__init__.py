
from robob.pipeline import ExecPipelineItem

class Access(ExecPipelineItem):
	"""
	Base class for implementing access providers
	"""

	def configure(self, config):
		"""
		Configure access object
		"""
		pass


