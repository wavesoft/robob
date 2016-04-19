
from robob.metrics import MetricAggregator

#: The metric shows how many bytes are transfered till now
#: (ex. 10, 20, 50, 100, etc.)
MODE_INCREMENTING = 0

#: The metric shows how many bytes are transfered per operation
#: (ex. 10, 10, 30, 50, etc..)
MODE_PARTIAL = 1

#: The metric shows how many transfer operations are completed
#: (ex. 1, 1, 3, 5, etc...)
MODE_OPERATIONS = 2

class Aggregate(MetricAggregator):
	"""
	Calculate bandwidth based on how many bytes are transfered over time
	"""

	def __init__(self, metric):
		"""
		Initialize aggregator
		"""
		MetricAggregator.__init__(self, metric)
		self.mode = MODE_INCREMENTING
		self.opsize = 1

	def configure(self, config):
		"""
		Configure bandwidth calculator
		"""

		MODES = {
			"incrementing": MODE_INCREMENTING,
			"partial": MODE_PARTIAL,
			"operations": MODE_OPERATIONS,
			"0": MODE_INCREMENTING,
			"1": MODE_PARTIAL,
			"2": MODE_OPERATIONS,
		}

		if 'mode' in config:
			m = config['mode'].lower()
			if not m in MODES:
				raise AssertionError("Unknown operation mode '%s'" % m)
			self.mode = MODES[ m ]

		if 'opsize' in config:
			self.opsize = float(config['opsize'])

	def collect(self, values):
		"""
		Run aggregator for the specified values and collect results
		"""

		# Min max and avereage
		v_min = None
		v_max = None
		v_avg = 0

		# Get lat value
		if self.mode == MODE_PARTIAL:
			last_v = self.metric.initial
			last_t = self.metric.resetTime
		else:
			last_v = None
			last_t = None

		# Iterate over values
		for v in values:
			if last_v:

				# Calculate time difference (sec)
				time_diff = v.t - prev.t

				# Calculate bandwidth
				if self.mode == MODE_INCREMENTING:
					bw_diff = last_v - v.v
				elif self.mode == MODE_PARTIAL:
					bw_diff = v.v
				elif self.mode == MODE_OPERATIONS:
					bw_diff = v.v * self.opsize

				# Calculate bandwidth (bytes/sec)
				bw = bw_diff / time_diff

				# Update
				if v_min is None:
					v_min = bw
					v_max = bw
					v_avg = bw
				else:
					if bw < v_min:
						v_min = bw
					if bw > v_max:
						v_max = bw
					v_avg += bw

			last_v = v.v
			last_t = v.t

		# Average
		v_avg /= len(values)

		# Return bandwidth suffixes
		return [ v_avg, v_min, v_max ]

	def titles(self):
		"""
		Return the titles of this aggregator values
		"""
		return [ "(Average B/w)", "(Min B/w)", "(Max B/w)" ]

