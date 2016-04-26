
from robob.metrics import MetricAggregator

class Aggregate(MetricAggregator):
	"""
	Average aggregator calculates the maximum of the collected values
	"""

	def configure(self, config):
		"""
		Configure aggregator
		"""
		self.title = "(Max)"
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
				if n > num:
					num = n

		# Return maximum
		return [ num ]

	def titles(self):
		"""
		Return the titles of this aggregator values
		"""
		return [ self.title ]
