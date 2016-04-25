
from robob.metrics import MetricAggregator

class Aggregate(MetricAggregator):
	"""
	Average aggregator calculates the average of the collected values
	"""

	def configure(self, config):
		"""
		Configure aggregator
		"""
		self.title = "(Avg)"
		if 'title' in config:
			self.title = config['title']

	def collect(self, values):
		"""
		Run aggregator for the specified values and collect results
		"""

		# Summarize
		num = 0
		for v in values:
			num += v.number()

		# Return average suffix
		if len(values) == 0:
			return [ 0 ]
		return [ float(num) / len(values) ]

	def titles(self):
		"""
		Return the titles of this aggregator values
		"""
		return [ self.title ]
