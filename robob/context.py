
import re
import copy

#: Macro regex
RE_MACRO = re.compile(r'\$\{(\w+)\}')

class Context(dict):
	"""
	An environment variable and context
	"""

	def fork(self):
		"""
		Deep copy current context into another context
		"""
		return Context( copy.deepcopy(self) )

	def set(self, name, value):
		"""
		Flat-import the specified dictionary and/or variable
		"""

		if isinstance(value, dict):
			for k,v in value.iteritems():
				self.set( "%s.%s" % (name,k), v )
		elif isinstance(value, list):
			i = 0
			for v in value:
				if 'name' in v:
					self.set( "%s.%s" % (name,v['name']), v )
				else:
					self.set( "%s.%i" % (name,i), v )
				i += 1
		else:
			self[name] = value

	def replaceMacros(self, where):
		"""
		Replace all macros in context to the given string
		"""

		# Replace helper
		def replace(m):
			return self.get(m.group(1), "")

		# Replace all macros in dict
		if isinstance(where, dict):
			ans = {}
			for k,v in where.iteritems():
				ans[k] =replaceMacros(v)
			return ans

		# Replace all macros in list
		elif isinstance(where, list):
			ans = []
			for v in where:
				ans.append( replaceMacros(v) )
			return ans

		# Replace all macros in string
		elif type(where) in [str, unicode]:
			return RE_MACRO.sub( replace, where )

		# Pass through everything else
		else:
			return where

