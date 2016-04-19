
import importlib

def _class_by_name( module, className ):
	"""
	Helper function to extract a class from module
	"""
	# Import module
	mod = importlib.import_module(module)
	# Get class
	return getattr(mod, className)

def accessFactory( specs, name ):
	"""
	Instantiate or get an access object from the 
	specifications with the given name.
	"""
	pass

def aggregateFactory( config, metric ):
	"""
	Create an aggregator factory from the config dict
	"""

	# Extract class
	cls_name = config['class']
	del config['class']

	# Get class
	cls = _class_by_name( cls_name, 'Aggregate' )

	# Instantiate and configure
	inst = cls( metric )
	inst.configure( config )

	# Return instance
	return inst

