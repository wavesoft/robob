
import logging
import re
import copy

from collections import OrderedDict

#: Macro regex
RE_MACRO = re.compile(r'\$\{(.+?)\}')

#: Macro variable regex
RE_MACRO_VAR = re.compile(r'[a-z][a-z0-9\._]*', flags=re.IGNORECASE)

#: Context logger
logger = logging.getLogger('context')

class Context(OrderedDict):
	"""
	An environment variable and context
	"""

	@staticmethod
	def definitions_in( specs_dict ):
		"""
		Traverse specifications dict and detect definitions
		"""

		# Prepare properties
		defs = set()
		stack = [ specs_dict ]

		# Traverse stack
		while stack:
			top = stack.pop(0)
			for k,v in top.items():
				if isinstance(v, dict):
					if k == "define":
						defs.update( v.keys() )
					else:
						stack.append(v)
				elif isinstance(v, list):
					for d in v:
						if isinstance(d, dict):
							stack.append(d)

		# Return definitions
		return defs

	def __init__(self, contents={}, definitions=set()):
		"""
		Initialize parent dictionary
		"""
		OrderedDict.__init__(self, contents)
		self._definitions = definitions

	def fork(self):
		"""
		Deep copy current context into another context
		"""
		return Context( copy.deepcopy(self), self._definitions )

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
				for k,v in value.items():
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
					for k,v in value.items():
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

		# Prepare properties
		self._unreplaced = set()
		replaced = True

		# Deep-copy dictionary
		dictionary = copy.deepcopy(self)

		# Keep replacing until there are no other macros to replace
		while replaced:
			# Replace and check if this was indeed replaced
			(dictionary, replaced) = self.replaceMacros( dictionary )

		# Log unreplaced items
		for m in self._unreplaced:
			if not m in self._definitions:
				logger.warn("Unknown macro '${%s}' encountered in specifications!" % m)

		# Return a new context with the new dictionary
		return Context( dictionary )

	def evaluate(self, expr):
		"""
		Evaluate a macro expression
		"""

		# Reset properties
		self._evalMissing = False

		# Extract default value
		defaultValue = None
		if '|' in expr:
			(expr, defaultValue) = expr.split("|", 1)

		# Check if this is an expression
		if ('*' in expr) or ('+' in expr) or ('/' in expr) or ('%' in expr) or \
			('-' in expr) or ('^' in expr) or ('(' in expr) or (')' in expr):

			# Replace helper
			def replace(m):
				key = m.group(0)

				# Ignore some functions
				if key in [ 'str', 'int', 'float', 'pow', 'round' ]:
					return m.group(0)

				# Replace values
				if not key in self:
					self._evalMissing = True
					return ""
				else:

					# Check if we should wrap value in quotes
					value = str(self[key])
					if value.isdigit() or ((value.count(".") == 1) and value.replace(".","").isdigit()):
						return value
					else:
						return '"%s"' % value.replace('"', '\\"')

			# Expand variables
			eval_expr = RE_MACRO_VAR.sub( replace, expr )

			# Check if we had missing properties
			if self._evalMissing:
				return defaultValue

			# Otherwise evaluate expression
			try:
				return eval(eval_expr)
			except Exception as e:
				logger.warn("Error evaluating macro expression '%s': %s" % (expr, str(e)))
				return defaultValue

		else:

			# It's a plain value, return calculation
			if expr in self:
				return self[expr]
			else:
				return defaultValue

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
			# Try to evaluate expression
			key = m.group(1)
			value = self.evaluate( key )
			if value is None:
				# Return un-replaced
				self._unreplaced.add(key)
				return m.group(0)
			else:
				# Return replaced & mark action
				self._did_replace = True
				# Remove from unreplaced
				if key in self._unreplaced:
					self._unreplaced.remove(key)
				return str(value)

		# Replace all macros in dict
		if isinstance(where, dict):
			ans = {}
			for k,v in where.items():
				(ans[k], unused) = self.replaceMacros(v, False)

			return (ans, self._did_replace)

		# Replace all macros in list
		elif isinstance(where, list):
			ans = []
			for v in where:
				ans.append( self.replaceMacros(v, False)[0] )
			return (ans, self._did_replace)

		# Replace all macros in string
		elif type(where) in [str, str]:
			return (RE_MACRO.sub( replace, where ), self._did_replace)

		# Pass through everything else
		else:
			return (where, self._did_replace)

