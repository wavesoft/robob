
import re
from robob.parser import Parser as BaseParser

class Parser(BaseParser):
	"""
	The regular expression parser matches each line against
	a set of regex rules and extracts the matches into metrics.

	Example:

	  class: robob.parser.regex
	  match:
	    - "^.*?Got (?P<CQ>[0-9]+) CQ.*$"

	"""

	def configure(self, config):
		"""
		Apply the specified configuration
		"""
		self.matches = []

		# Separate specified configuration to per-line
		for cfg in config['match']:
			self.matches.append( re.compile(cfg) )

	def parse(self, line):
		"""
		Match the specified line against our configuration
		"""

		for m in self.matches:

			# Check for match
			grp = m.match(line)
			if grp:

				# Update values
				for k,v in grp.groupdict():
					self.update( k, v )

