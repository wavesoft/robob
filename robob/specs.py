
import os
import yaml
from robob.context import Context

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
			update[key] = value + original[value]
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

		# Import nodes
		if 'nodes' in self.specs:
			for v in self.specs['nodes']:
				self.context.set("node.%s" % v['name'], v)
