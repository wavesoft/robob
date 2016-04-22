
import re
from robob.parser import ParserBase

class Parser(ParserBase):
	"""
	The simple split parser gives you the ability to extract a particular
	column from a specific line in the output.

	  class: robob.parser.grid 
	  separator: \s+				# How to split each line
	  anchor: 						# Keyword were line index resets to 0
	  match:
	    - name: sample1				# Match on exact line/column
	      line: 1
	      col: 1

	    - name: sample2				# Match column on every line
	      col: 1

	    - name: sample3				# Get the column of a line that matches
	      anchor: "name:"			# the given anchor
	      col: 1

	"""

	def configure(self, config):
		"""
		Apply the specified configuration
		"""
		self.line = 0
		self.col_any = []
		self.col_line = {}
		self.col_anchor = []

		# Column separator
		self.colsep = re.compile(r"\s+")
		if 'separator' in config:
			self.colsep = re.compile(config['separator'])


		# anchor indicator
		self.anchor = None
		if 'anchor' in config:
			self.anchor = re.compile(config['anchor'])

		# Separate specified configuration to per-line
		for cfg in config['match']:

			# Get column separator
			colsep = self.colsep
			if 'separator' in cfg:
				colsep = re.compile(cfg['separator'])

			# Check per-line config
			if 'line' in cfg:
			
				# Ensure a col_line entry
				l = str(cfg['line'])
				if not l in self.col_line:
					self.col_line[l] = []

				# Append
				self.col_line[l].append( (colsep, int(cfg['col']), cfg['name']) ) 

			# Check per-anchor config
			elif 'anchor' in cfg:

				# Append to anchor config
				self.col_anchor.append( ( re.compile(cfg['anchor']), colsep, int(cfg['col']), cfg['name']) )

			# No line specification? Match all
			else:

				# Append to any line config
				self.col_any.append( (colsep, int(cfg['col']), cfg['name']) )


	def got_stdout(self, line):
		"""
		Match the specified line against our configuration
		"""

		# Check for line anchor indicator
		if self.anchor and self.anchor.match(line):
			self.line = 0

		# Process anyline config
		for sep, col, name in self.col_any:

			# Get value
			parts = sep.split(line)
			if col < len(parts):
				self.update( name, parts[col] )

		# Get line as string
		l = str(self.line)
		self.line += 1

		# Check if we have a configuration for this line
		if l in self.col_line:
			for sep, col, name in self.col_line[l]:

				# Get value
				parts = sep.split(line)
				if col < len(parts):
					self.update( name, parts[col] )

		# Process lines that contain a known anchor
		for anchor, sep, col, name in self.col_anchor:
			if anchor.match( line ):

				# Get value
				parts = sep.split(line)
				if col < len(parts):
					self.update( name, parts[col] )


	def reset(self):
		"""
		When reset, anchor lines to line #0
		"""
		self.line = 0

