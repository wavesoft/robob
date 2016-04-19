
import os
import yaml
import itertools

from robob.context import Context
from robob.stream import Stream

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


class Specs(object):
	"""
	Specifications file with nested specifications resolution support
	"""

	def __init__(self, filename):
		"""
		Initialize a specifications object from the given filename
		"""
		self.filename = filename
		self.specs = {}

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

	def createStreams(self, testContext):
		"""
		Create a stream contexts using the specified test context as base
		"""
		ans = []

		# Create a stream object for every stream defined in specs
		for ctx in self.specs['streams']:

			# Create and configure a stream
			stream = Stream( testContext )
			stream.configure( ctx )

			# Append to list
			ans.append( stream )

		# Return streams
		return ans

	def load(self):
		"""
		Load the specifications file
		"""

		# Prepare stack
		stack = [ self.filename ]

		# Start processing items on stack
		while len(stack):

			# Get filename and base dir to load
			fname = stack.pop(0)
			print "Loading %s..." % fname
			bdir = os.path.dirname( fname )
			if not bdir:
				bdir = "."

			# Load specs
			with open(fname, 'r') as f:
				buf = f.read()
				specs = yaml.load(buf)

			# Check if there are other files to
			# load, and therefore add them on stack
			if 'load' in specs:

				# Make sure it's list
				if type(specs['load']) in [str, unicode]:
					specs['load'] = [ specs['load'] ]

				# Iterate over specs
				for f in specs['load']:
					if f[0] == "/":
						stack.append(f)
					else:
						stack.append( "%s/%s" % (bdir, f) )

				# Remove 'load'
				del specs['load']

			# Merge specs
			self.specs = deepupdate( self.specs, specs )

		# Open a global context & import global variables
		self.context = Context()
		if 'globals' in self.specs:
			self.context.update( self.specs['globals'] )

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

