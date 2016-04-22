
import re
import copy

from collections import OrderedDict

#: Macro regex
RE_MACRO = re.compile(r'\$\{([\w\.]+)\}')

class Context(OrderedDict):
	"""
	An environment variable and context
	"""

	def fork(self):
		"""
		Deep copy current context into another context
		"""
		return Context( copy.deepcopy(self) )

	def set(self, name, value, include_flag=True):
		"""
		Set the specified value in the context and optionally
		also update a flat representation of the value.
		"""

		# Set value
		self[name] = value

		# Update flat representation
		if include_flag:
	
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

	def merge(self, name, value, include_flag=True):
		"""
		Merge the specified value in the context and optionally
		also update a flat representation of the value.
		"""

		# Set value
		if name in self:
			if isinstance(value, dict):

				# Merge list
				i = len(self[name])
				self[name] += value

				# Update flat representation
				if include_flag:
					for v in value:
						if 'name' in v:
							self.set( "%s.%s" % (name,v['name']), v )
						else:
							self.set( "%s.%i" % (name,i), v )
						i += 1

				# Don't continue
				return

			elif isinstance(value, list):

				# Merge dictionary
				self[name].update( value )

				# Update flat representation
				if include_flag:
					for k,v in value.iteritems():
						self.set( "%s.%s" % (name,k), v )

				# Don't continue
				return

		# Update value
		self[name] = value

	def render(self):
		"""
		Replace all macros in this context and return a
		dictionary with all values
		"""
		dictionary = copy.deepcopy(self)
		replaced = True

		# Keep replacing until there are no other macros to replace
		while replaced:
			# Replace and check if this was indeed replaced
			(dictionary, replaced) = self.replaceMacros( dictionary )

		# Return a new context with the new dictionary
		return Context( dictionary )

	def replaceMacros(self, where, _firstCall=True):
		"""
		Replace all macros in context to the given string
		"""
		unused = False

		# Check if a value was indeed updated
		if _firstCall:
			self._did_replace = False

		# Replace helper
		def replace(m):
			key = m.group(1)
			if key in self:
				# Return replaced & mark action
				self._did_replace = True
				return str(self[key])
			else:
				# Return un-replaced
				return m.group(0)

		# Replace all macros in dict
		if isinstance(where, dict):
			ans = {}
			for k,v in where.iteritems():
				(ans[k], unused) = self.replaceMacros(v, False)
			return (ans, self._did_replace)

		# Replace all macros in list
		elif isinstance(where, list):
			ans = []
			for v in where:
				ans.append( self.replaceMacros(v, False)[0] )
			return (ans, self._did_replace)

		# Replace all macros in string
		elif type(where) in [str, unicode]:
			return (RE_MACRO.sub( replace, where ), self._did_replace)

		# Pass through everything else
		else:
			return (where, self._did_replace)

