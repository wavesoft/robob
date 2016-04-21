
import os
import yaml
import itertools
import datetime
import logging

from robob.reporter import Reporter
from robob.metrics import Metrics
from robob.context import Context
from robob.stream import Stream, streamContext

def deepupdate(original, update):
	"""
	Recursively update a dict.
	Subdict's won't be overwritten but also updated.
	"""
	for key, value in original.iteritems(): 
		if key not in update:
			update[key] = value
		elif isinstance(value, dict):
			deepupdate(value, update[key]) 
		elif isinstance(value, list):
			update[key] = value + update[key]
	return update

class StatsSpecs(object):
	"""
	Statistics specicis
	"""

	def __init__(self):
		"""
		Initialize specs defaults
		"""
		self.iterations = 1

	def configure(self, specs):
		"""
		Configure stats specs
		"""
		if 'iterations' in specs:
			self.iterations = int( specs['iterations'] )

class Specs(object):
	"""
	Specifications file with nested specifications resolution support
	"""

	def __init__(self, filename):
		"""
		Initialize a specifications object from the given filename
		"""

		self.stats = StatsSpecs()
		self.filename = filename
		self.specs = {}

	def getTestVariables(self):
		"""
		Return the variable names of the test-cases
		"""

		# Return keys of test-cases
		return self.specs['test-cases'].keys()

	def getMetricTitles(self):
		"""
		There is already some work done on the metrics class
		so we are going to re-use it
		"""

		# Create a metrics object
		metrics = Metrics()
		metrics.configure( self.context )

		# Return titles
		return metrics.titles()

	def createTestContexts(self):
		"""
		Create test contexts according to specs
		"""

		# Prepare product components
		values = []
		keys = []
		for k,v in self.specs['test-cases'].iteritems():
			keys.append(k)
			values.append(v)

		# Generate test cases as product of combinations
		contexts = []
		for v in itertools.product(*values):

			# Fork context
			ctx = self.context.fork()

			# Update and collect
			ctx.update( dict(zip( keys, v)) )
			contexts.append( ctx )

		return contexts

	def createStreams(self, testContext, testMetrics):
		"""
		Create a stream contexts using the specified test context as base
		"""
		ans = []

		# Create a stream object for every stream defined in specs
		for specs in self.specs['streams']:

			# Create and configure a stream
			stream = Stream( testContext, testMetrics )
			stream.configure( specs )

			# Append to list
			ans.append( stream )

		# Return streams
		return ans

	def createReporter(self):
		"""
		Create a reporter according to the specifications
		"""

		# Get report specifics
		report = {}
		if 'report' in self.specs:
			report = self.specs['report']

		# Get test name
		name = "test"
		if 'name' in self.specs:
			name = self.specs['name']
		if 'name' in report:
			name = report['name']

		# Get base dir
		baseDir = "."
		if os.path.isdir("./reports"):
			baseDir = "./reports"
		if 'path' in report:
			baseDir = report['path']

		# Calculate timestamp
		d = datetime.datetime.now()
		name += "-%s" % d.strftime("%Y%m%d%H%M%S")

		# Calculate filename
		filename = "%s/%s.csv" % (baseDir, name)

		# Create reporter
		return Reporter( filename, self )

	def load(self):
		"""
		Load the specifications file
		"""
		logger = logging.getLogger("specs")

		# Prepare stack
		filestack = [ self.filename ]
		specsstack = [ ]

		# Start processing items on filestack
		while len(filestack):

			# Get filename and base dir to load
			fname = filestack.pop(0)
			logger.info("Loading %s" % fname)
			bdir = os.path.dirname( fname )
			if not bdir:
				bdir = "."

			# Load specs
			with open(fname, 'r') as f:
				buf = f.read()
				specs = yaml.load(buf)

			# Check if there are other files to
			# load, and therefore add them on filestack
			if 'load' in specs:

				# Make sure it's list
				if type(specs['load']) in [str, unicode]:
					specs['load'] = [ specs['load'] ]

				# Iterate over specs
				for f in specs['load']:
					if f[0] == "/":
						filestack.append(f)
					else:
						filestack.append( "%s/%s" % (bdir, f) )

				# Remove 'load'
				del specs['load']

			# Keep specs
			specsstack.append( specs )

		# Merge specs in reverse order so that loaded
		# files have lower priority than the ones that loaded them
		for specs in reversed( specsstack ):
			self.specs = deepupdate( self.specs, specs )

		# Open a global context & import global variables
		self.context = Context()
		if 'globals' in self.specs:
			self.context.update( self.specs['globals'] )

		# Apply stats
		if 'stats' in self.specs:
			self.stats.configure( self.specs['stats'] )

		# Import environments
		if 'environments' in self.specs:
			for k,v in self.specs['environments'].iteritems():
				self.context.set("env", self.specs['environments'])

		# Import metrics
		if 'metrics' in self.specs:
			self.context.set("metric", self.specs['metrics'])

		# Import nodes
		if 'nodes' in self.specs:
			self.context.set( 'node', self.specs['nodes'] )

		# Import parsers
		if 'parsers' in self.specs:
			self.context.set( 'parser', self.specs['parsers'] )

		# Import apps
		if 'apps' in self.specs:
			self.context.set( 'app', self.specs['apps'] )

		# Import streamlets
		if 'streamlets' in self.specs:
			self.context.set( 'streamlet', self.specs['streamlets'] )

		# Import notes
		if 'notes' in self.specs:
			self.context.set( 'notes', self.specs['notes'] )
