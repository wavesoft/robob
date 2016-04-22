
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
		self._alias = {}
		self._filter = None

	def got_stdout(self, line):
		"""
		[Public] Process an stdout line
		"""
		pass

	def got_stderr(self, line):
		"""
		[Public] UProcess an stderr line
		"""
		pass

	def reset(self):
		"""
		[Public] Reset the parser for a new stream
		"""
		self._metrics.reset()

	def set_alias(self, aliases):
		"""
		[Public] Update alias mapping
		"""
		self._alias = aliases

	def set_filter(self, metrics):
		"""
		[Public] Update metrics filter
		"""
		self._filter = metrics

	def update(self, metric, value):
		"""
		[Private] Update the value of the specified metric
		"""

		# Skip metrics in filter
		if not self._filter is None and not metric in self._filter:
			return

		# Replace alias if found
		if metric in self._alias:
			metric = self._alias[metric]

		# Forward to metrics
		self._metrics.update( metric, value )

