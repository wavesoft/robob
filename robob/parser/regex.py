
import re
from robob.parser import ParserBase

class Parser(ParserBase):
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

	def got_stdout(self, line):
		"""
		Match the specified line against our configuration
		"""

		for m in self.matches:

			# Check for match
			grp = m.match(line)
			if grp:

				# Update values
				for k,v in grp.groupdict().items():
					self.update( k, float(v) )

