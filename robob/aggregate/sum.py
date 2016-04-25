
from robob.metrics import MetricAggregator

class Aggregate(MetricAggregator):
	"""
	Sum aggregator calculates the sum of collected values
	"""

	def configure(self, config):
		"""
		Configure aggregator
		"""
		self.title = "(Sum)"
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

		# Return sum
		return [ num ]

	def titles(self):
		"""
		Return the titles of this aggregator values
		"""
		return [ self.title ]
