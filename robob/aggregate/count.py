
from robob.metrics import MetricAggregator

class Aggregate(MetricAggregator):
	"""
	Simple count aggregator calculates how many times the metric was encountered
	"""

	def configure(self, config):
		"""
		Configure aggregator
		"""
		self.title = "(Count)"
		if 'title' in config:
			self.title = config['title']

	def collect(self, values):
		"""
		Run aggregator for the specified values and collect results
		"""

		# Return numer of values in the timeseries
		return [ len(values) ]

	def titles(self):
		"""
		Return the titles of this aggregator values
		"""
		return [ self.title ]
