
import re
from robob.parser import ParserBase

WS = re.compile(r"\s+")
CPULINE = re.compile(r"^([0-9]+):([0-9]+):([0-9]+)")

class Parser(ParserBase):
	"""
	The mpstat parser parses the output of mpstat utility on linux
	"""

	def configure(self, config):
		"""
		Apply the specified configuration
		"""

		# Data matrix
		self.matrix = {}

		# Local properties
		self.core_parsing = False
		self.metrics = []
		self.prefixmatch = ""

		# Extract what information to track
		self.updateMetrics = {}
		if 'match' in config:
			for k,v in config['match'].items():

				# Update metrics
				parts = v.split(".")
				if len(parts) != 2:
					raise AssertionError("Expecting 'cpu.metric' format for the metrics to track")
				self.updateMetrics[k] = parts

	def got_stdout(self, line):
		"""
		Match the specified line against our configuration
		"""

		if "%usr" in line:

			# Prepare for parsing
			self.core_parsing = True
			self.matrix = {}

			# Split header
			header = WS.split(line)
			if header[2] != "CPU":
				raise AssertionError("This does not look like mpstat output!")

			# Extract metric titles
			self.metrics = [ x.replace("%","") for x in header[3:-1] ]

		elif self.core_parsing:

			if CPULINE.match(line):
				parts = WS.split(line)
				
				# Get key and values
				cpu = parts[2]
				values = [ float(x) for x in parts[3:-1] ]

				# Update CPU details on this matrix
				self.matrix[cpu] = dict(list(zip( self.metrics, values )))

			else:
				self.core_parsing = False
				self._commit()


	def got_eof(self):
		"""
		Transmission completed
		"""
		self._commit()

	def _commit(self):
		"""
		Update metrics according to details
		"""

		for metric, (cpu, track) in self.updateMetrics.items():
			value = None

			# Get this value
			if cpu in self.matrix:
				if track in self.matrix[cpu]:
					value = self.matrix[cpu][track]

			# Update metric
			if not value is None:
				self.update( metric, value )

