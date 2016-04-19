
import time
from robob.factories import aggregateFactory

#: SI prefix metric (ex. 10^3->k, 10^6->M)
METRIC_SI = 1

#: IEC prefix metric (ex. 1024->k, 1024^2->M)
METRIC_IEC = 2

def _apply_prefix( value, base, prefixes ):
	"""
	Test what's the maximum prefix we can apply to the specified
	value with the specified base
	"""
	nv = value
	np = ""

	# Test given prefixes
	for i in range(1, len(prefixes)):
		v = pow(base, i)

		if v >= 1:
			if v > value:
				break
		else:
			if v < value:
				break

		# Apply scaling & pick prefix
		nv = value / v
		np = prefixes[i]

	# Return tuple
	return (nv, np)

def summarize( results ):
	"""
	Summarize multiple results into a single one
	"""

	# Create a results were to collect everything
	ans = MetricsResults()

	# Metrics are always the same, so just get the first ones
	ans.metrics = results[0].metrics
	ans.values = [0] * len(results[0].values)

	# Summarize values
	for r in results:
		ans.values = [x + y for x, y in zip(ans.values, r.values)]

	# Average
	num = len(results)
	ans.values = [ x / num for x in ans.values ]

	# Return results
	return ans

class MetricAggregator(object):
	"""
	Default metric aggregator
	"""

	def __init__(self, metric):
		"""
		Initialize a metric aggregator
		"""
		self.metric = metric

	def configure(self, config):
		"""
		Configure metrics aggregator
		"""
		pass

	def collect(self, values):
		"""
		Run aggregator over the given timeseries values and
		return an array of values
		"""
		return []

	def titles(self):
		"""
		Return the title suffixes for the values returned by
		the previous function.
		"""
		return []

class MetricValue(object):
	"""
	A value with a timestamp used in the timeseries
	"""

	def __init__(self, value):
		"""
		Keep value and timestamp
		"""
		self.t = time.time()
		self.v = value

class Metric(object):
	"""
	A single metric on the metrics array
	"""

	def __init__(self, config):
		"""
		Initialize metric
		"""

		# Defaults and required properties
		self.name = config['name']
		self.title = self.name
		self.initial = 0
		self.series = []
		self.units = ""
		self.metric = 0
		self.scale = 1.0
		self.decimals = 2
		self.aggregators = []
		self.resetTime = 0

		# Update optional
		if 'title' in config:
			self.title = config['title']
		if 'units' in config:
			self.units = config['units']
		if 'initial' in config:
			self.initial = config['initial']
		if 'metric' in config:
			m = config['metric'].lower()
			if m == 'si':
				self.metric = METRIC_SI
			elif m == 'iec':
				self.metric = METRIC_IEC
			else:
				raise AssertionError("Unknown metrix prefix '%s'. Expecting 'si' or 'iec'")
		if 'scale' in config:
			self.scale = float(config['scale'])
		if 'dec' in config:
			self.decimals = int(config['dec'])
		if 'aggregate' in config:
			aggregate = config['aggregate']
			if type(aggregate) in [str, unicode]:
				aggregate = [ {"class": aggregate} ]
			if type(aggregate) is dict:
				aggregate = [ aggregate ]
			for a in aggregate:
				self.aggregators.append( aggregateFactory(a, self) )

		# If we have no aggregators, add a default
		# average aggregator
		if not self.aggregators:
			self.aggregators.append( aggregateFactory({
					"class": "robob.aggregate.avg"
				}, self) )

		# Reset
		self.reset()

	def update(self, value):
		"""
		Add a value in the time series
		"""
		self.series.append( MetricValue(value) )

	def reset(self):
		"""
		Reset to default
		"""
		self.series = []
		self.resetTime = time.time()

	def format(self, value):
		"""
		Human-readable formatting of the given metric value
		"""

		# Get units
		u = self.units

		# Apply scale to value
		v = value * self.scale

		# Apply prefix
		if self.metric == METRIC_SI:
			if v < 1:
				(v, sf) = _apply_prefix( v, 0.001, [ 'm','u','n','p','f','a' ] )
			else:
				(v, sf) = _apply_prefix( v, 1000, [ 'k','M','G','T','P','E' ] )
			u = sf + u
		elif self.metric == METRIC_IEC:
			(v, sf) = _apply_prefix( v, 1024, [ 'k','M','G','T','P','E' ] )
			u = sf + u

		# Format decimals
		s = ('{0:.%ig}' % self.decimals).format(v)

		# Return value with units
		return s + " " + u

	def titles(self):
		"""
		Return the titles fo the values returned by this metric
		"""
		titles = []

		# Collect titles from aggregators
		for a in self.aggregators:
			for t in a.titles():
				titles.append( self.title + " " + t )

		# Return titles
		return titles

	def values(self):
		"""
		Return metric values as collected from the aggregators
		"""
		values = []

		# Create values from aggregators
		for a in self.aggregators:
			values += a.collect( self.series )

		# Return values
		return values

class MetricsResults(object):
	"""
	An abstract representation of metrics results that can be summarized
	with other metrics results before finalized to renderable results.
	"""

	def __init__(self):
		"""
		Initialize a results class
		"""

		self.values = []
		self.metrics = []

	def updateFrom(self, metric):
		"""
		Update values of the specified metric
		"""

		# Get aggregated values
		values = metric.values()

		# Update value and linked metric for it
		for v in values:
			self.values.append( v )
			self.metrics.append( metric )

	def render(self):
		"""
		Render the results to human-readable indicators
		"""
		results = []

		# Iterate over values and render them
		for i in range(0, len(self.values)):
			results.append( self.metrics[i].format( self.values[i] ) )

		# Return results
		return results

class Metrics(object):
	"""
	Metrics class is responsible for keeping track for metrics
	updates and for summarizing it's results.
	"""

	def __init__(self):
		"""
		Initialize metrics object
		"""
		self.metrics = {}

	def configure(self, config):
		"""
		Configure metrics object
		"""

		# Initialize metrics from their config
		for m in config['metrics']:
			self.metrics[ m['name'] ] = Metric( m )

	def reset(self):
		"""
		Reset all metrics
		"""
		for m in self.metrics.values():
			m.reset()

	def update(self, name, value):
		"""
		Update the specified value to a metric
		"""

		# Update the specified metric
		if name in self.metrics:
			self.metrics[name].update( value )
		else:
			raise AssertionError("Trying to update an undefined metric: '%s'" % name)

	def titles(self):
		"""
		Return the titles of the metrics
		"""
		titles = []

		# Get the aggregator titles of each metric
		for m in self.metrics.values():
			titles += m.titles()

		# Return titles
		return titles

	def results(self):
		"""
		Collect current results in a result object
		"""

		# Create new metrics results using the specs from the metrics
		results = MetricsResults()

		# Start aggregating results
		for m in self.metrics.values():
			results.updateFrom( m )

		# Return resultset
		return results

