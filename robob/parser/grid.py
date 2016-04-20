
import re
from robob.parser import ParserBase

class Parser(ParserBase):
	"""
	The grid parser gives you the ability to extract a particular
	column from a specific line in the  

	  class: robob.parser.grid  
	  match:
	    - name: mem_total
	      line: 1
	      col: 1

	    - name: mem_total
	      line: 1
	      col: 1

	"""

	def configure(self, config):
		"""
		Apply the specified configuration
		"""
		self.line = 0
		self.lineconfig = {}
		self.anchorconfig = []

		# Column separator
		self.colsep = re.compile(r"\s+")
		if 'separator' in config:
			self.colsep = re.compile(rconfig['separator'])

		# Separate specified configuration to per-line
		for cfg in config['match']:

			# Get column separator
			colsep = self.colsep
			if 'separator' in cfg:
				colsep = re.compile(cfg['separator'])

			# Check per-line config
			if 'line' in cfg:
			
				# Ensure a lineconfig entry
				l = str(cfg['line'])
				if not l in self.lineconfig:
					self.lineconfig[l] = []

				# Append
				self.lineconfig[l].append( (colsep, int(cfg['col']), cfg['name']) ) 

			# Check per-anchor config
			elif 'anchor' in cfg:

				# Append to anchor config
				self.anchorconfig.append( (cfg['anchor'], colsep, int(cfg['col']), cfg['name']) )


	def got_stdout(self, line):
		"""
		Match the specified line against our configuration
		"""

		# Get line as string
		l = str(self.line)
		self.line += 1

		# Check if we have a configuration for this line
		if l in self.lineconfig:
			for sep, col, name in self.lineconfig[l]:

				# Get value
				parts = sep.split(line)
				if col < len(parts):
					self.update( name, parts[col] )

		# Process lines that contain a known anchor
		for anchor, sep, col, name in self.anchorconfig:
			if anchor in line:

				# Get value
				parts = sep.split(line)
				if col < len(parts):
					self.update( name, parts[col] )


	def reset(self):
		"""
		When reset, rewind lines to line #0
		"""
		self.line = 0

