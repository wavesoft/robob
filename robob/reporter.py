
import datetime

class Reporter(object):
	"""
	A class tha generates reports
	"""

	def __init__(self, filename, meta={}):
		"""
		Initialize a new test report, keeping the data in the output specified
		"""

		self.filename = filename
		self.meta = meta
		self.fd = None
		self.testID = 0
		self.activeTest = []
		self.testVariables = []

	def start( self, specs ):
		"""
		Start a test putting metadata and columns in the file
		"""

		# Reset properties
		self.testID = 0
		self.activeTest = []
		self.testVariables = specs.getTestVariables()

		# Open file descriptor
		self.fd = open(self.filename, "w")

		# Write title & Columns
		for k,v in self.meta.iteritems():
			self.fd.write("%s,%s\n" % (k, v))
		self.fd.write("Started on,%s\n" % str(datetime.datetime.now()))
		self.fd.write("\n")
		self.fd.write("Num,Started,Ended,Status,%s,%s\n" % \
			( ",".join(self.testVariables),  ",".join(specs.getMetricTitles()) ) )

	def close(self):
		"""
		Close test report
		"""

		# Close file descriptor if open
		if self.fd:
			self.fd.close()
			self.fd = None

	def log_start( self, testContext ):
		"""
		Log the start of a test
		"""

		# Prepare properties
		self.testID += 1
		self.activeTest = [ testContext[x] for x in self.testVariables ]

		# Log the beginning of test and starting date
		self.fd.write("%i,%s" % ( self.testID, str(datetime.datetime.now()) ) )

	def log_error(self, error):
		"""
		Log the failure of a test
		"""

		# Write end and values
		self.fd.write(",%s,Error,%s,%s\n" % ( str(datetime.datetime.now()), ",".join(self.activeTest), error ) )

	def log_end(self, results ):
		"""
		Log the completion of a test
		"""

		# Write end and values
		self.fd.write(",%s,OK,%s,%s\n" % ( str(datetime.datetime.now()), ",".join(self.activeTest), ",".join(results.render()) ) )

