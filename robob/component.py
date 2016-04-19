
class ComponentBase(object):
	"""
	Global base class for all components with shared context and specs
	"""

	def __init__(self, context):
		"""
		Keep context
		"""
		self.context = context

