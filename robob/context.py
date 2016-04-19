
import re

#: Macro regex
RE_MACRO = re.compile(r'\$\{(\w+)\}')

class Context(dict):
	"""
	An environment variable and context
	"""

	def replaceMacros(self, src):
		"""
		Replace all macros in context to the given string
		"""

		# Replace helper
		def replace(m):
			return self.get(m.group(1), "")

		# Replace all macros
		return RE_MACRO.sub( replace, src )