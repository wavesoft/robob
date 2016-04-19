
import importlib

def _class_by_name( module, className ):
	"""
	Helper function to extract a class from module
	"""
	# Import module
	mod = importlib.import_module(module)
	# Get class
	return getattr(mod, className)

def parserFactory( specs, context, metrics ):
	"""
	Create a parser from the specs dict
	"""

	# Extract class
	cls_name = specs['class']
	del specs['class']

	# Get class
	cls = _class_by_name( cls_name, 'Parser' )

	# Instantiate and configure
	inst = cls( context, metrics )
	inst.configure( specs )

	# Return instance
	return inst

def pipeFactory( specs, context ):
	"""
	Create a pipe from the specs dict
	"""

	# Extract class
	cls_name = specs['class']
	del specs['class']

	# Get class
	cls = _class_by_name( cls_name, 'Pipe' )

	# Instantiate and configure
	inst = cls( context )
	inst.configure( specs )

	# Return instance
	return inst

def aggregateFactory( specs, metric ):
	"""
	Create an aggregator from the specs dict
	"""

	# Extract class
	cls_name = specs['class']
	del specs['class']

	# Get class
	cls = _class_by_name( cls_name, 'Aggregate' )

	# Instantiate and configure
	inst = cls( metric )
	inst.configure( specs )

	# Return instance
	return inst

