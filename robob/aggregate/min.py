
from robob.metrics import MetricAggregator

class Aggregate(MetricAggregator):
	"""
	Average aggregator calculates the minimum of the collected values
	"""

	def configure(self, config):
		"""
		Configure aggregator
		"""
		self.title = "(Min)"
		if 'title' in config:
			self.title = config['title']

	def collect(self, values):
		"""
		Run aggregator for the specified values and collect results
		"""

		# Summarize
		num = None
		if len(values) > 0:
			num = values[0].v
			for v in values:
				n = v.number()
				if n < num:
					num = n

		# Return minimum
		return [ num ]

	def titles(self):
		"""
		Return the titles of this aggregator values
		"""
		return [ self.title ]
