
import os
import yaml
import itertools
import datetime
import logging

from collections import OrderedDict

from robob.util import time2sec
from robob.reporter import Reporter
from robob.metrics import Metrics
from robob.context import Context
from robob.stream import Stream, streamContext

def deepupdate(original, update):
	"""
	Recursively update a dict.
	Subdict's won't be overwritten but also updated.
	"""
	for key, value in original.items(): 
		if key not in update:
			update[key] = value
		elif isinstance(value, dict):
			deepupdate(value, update[key]) 
		elif isinstance(value, list):
			update[key] = value + update[key]
	return update

def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
	class OrderedLoader(Loader):
		pass
	def construct_mapping(loader, node):
		loader.flatten_mapping(node)
		return object_pairs_hook(loader.construct_pairs(node))
	OrderedLoader.add_constructor(
		yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
		construct_mapping)
	return yaml.load(stream, OrderedLoader)

class Specs(object):
	"""
	Specifications file with nested specifications resolution support
	"""

	def __init__(self, filename):
		"""
		Initialize a specifications object from the given filename
		"""

		self.filename = filename
		self.specs = OrderedDict()

	def getTestVariables(self):
		"""
		Return the variable names of the test-cases
		"""

		# Return keys of test-cases
		return list(self.specs['test-cases'].keys())

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
		for k,v in self.specs['test-cases'].items():
			keys.append(k)
			values.append(v)

		# Generate test cases as product of combinations
		contexts = []
		for v in itertools.product(*values):

			# Fork context
			ctx = self.context.fork()

			# Update and collect
			test_keys = dict(list(zip( keys, v)))
			ctx.update( test_keys ) # Insert in global scope
			ctx.set( "curr", test_keys ) # And in curr scope
			contexts.append( ctx )

		return contexts

	def createStreams(self, testContext, testMetrics, iteration):
		"""
		Create a stream contexts using the specified test context as base
		"""
		ans = []


		# Create a stream object for every stream defined in specs
		for specs in self.specs['streams']:

			# Create and configure a stream
			stream = Stream( testContext, testMetrics, iteration )
			stream.configure( specs )

			# Append to list
			ans.append( stream )

		# Return streams
		return ans

	def createReporter(self):
		"""
		Create a reporter according to the specifications
		"""

		# Calculate filename
		filename = self.context['report.path'] + "/"
		filename += self.context['report.name']
		filename += "-%s" % self.context['report.timestamp']
		filename += ".csv"

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
				specs = ordered_load(buf, yaml.SafeLoader)

			# Check if there are other files to
			# load, and therefore add them on filestack
			if 'load' in specs:

				# Make sure it's list
				if type(specs['load']) in [str, str]:
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

		# Apply test specs
		if 'test' in self.specs:
			self.context.set( 'test', self.specs['test'] )

		# Import environments
		if 'environments' in self.specs:
			for k,v in self.specs['environments'].items():
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

		# Import report
		if 'report' in self.specs:
			self.context.set("report", self.specs['report'])

		# Initialize report defaults
		if not 'report.name' in self.specs:
			name = "test"
			if 'name' in self.specs:
				name = self.specs['name']
			self.context.set('report.name', name)
		if not 'report.path' in self.specs:
			baseDir = "."
			if os.path.isdir("./reports"):
				baseDir = "./reports"
			self.context.set('report.path', baseDir)

		# Define report timestamp
		d = datetime.datetime.now()
		self.context.set( 'report.timestamp', d.strftime("%Y%m%d%H%M%S") )
