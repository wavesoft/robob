
from robob.pipe import PipeListener
from robob.component import ComponentBase

class ParserBase(ComponentBase, PipeListener):
	"""
	Base class for implementing stream output parser
	"""

	def __init__(self, ctx, metrics):
		"""
		Initialize parser base class
		"""
		ComponentBase.__init__(self, ctx)
		PipeListener.__init__(self)

		# Initialize metrics
		self._metrics = metrics

	def got_stdout(self, line):
		"""
		Process an stdout line
		"""
		pass

	def got_stderr(self, line):
		"""
		Process an stderr line
		"""
		pass

	def reset(self):
		"""
		[Public] Reset the parser for a new stream
		"""
		self._metrics.reset()

	def update(self, metric, value):
		"""
		[Private] Update the value of the specified metric
		"""
		# Forward to metrics
		self._metrics.update( metric, value )

