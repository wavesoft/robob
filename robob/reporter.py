
import datetime
import logging

class Reporter(object):
	"""
	A class tha generates reports
	"""

	def __init__(self, filename, specs):
		"""
		Initialize a new test report, keeping the data in the output specified
		"""

		self.fd = None
		self.testID = 0
		self.specs = specs
		self.filename = filename
		self.iterations = specs.stats.iterations
		self.testVariables = specs.getTestVariables()
		self.testTitles = specs.getMetricTitles()
		self.activeTest = []
		self.summaryLines = []

		# Open logger
		self.logger = logging.getLogger("report")

		# Collect metadata
		self.meta = {}
		if 'meta' in specs.context:
			self.meta.update( specs.context['meta'] )
		if 'title' in specs.specs:
			self.meta['Title'] = specs.specs['title']
		if 'desc' in specs.specs:
			self.meta['Description'] = specs.specs['desc']

	def start( self ):
		"""
		Start a test putting metadata and columns in the file
		"""

		# Reset properties
		self.testID = 0
		self.activeTest = []

		# Open file descriptor
		self.logger.info("Writing report to %s" % self.filename)
		self.fd = open(self.filename, "w")

		# Write title & Columns
		for k,v in self.meta.iteritems():
			self.fd.write("%s,%s\n" % (k, v))
		self.fd.write("Started on,%s\n" % str(datetime.datetime.now()))
		self.fd.write("\n")
		self.fd.write("Test numbers\n")
		self.fd.write("\n")
		self.fd.write("Num,Iteration,Started,Ended,Status,%s,%s,Comment\n" % \
			( ",".join(self.testVariables),  ",".join(self.testTitles) ) )

	def close(self):
		"""
		Close test report
		"""

		# Close file descriptor if open
		if self.fd:
			self.fd.close()
			self.fd = None

	def finalize(self):
		"""
		Finalize report
		"""

		self.logger.info("Finalizing report")

		self.fd.write("\n")
		self.fd.write("Summarized numbers\n")
		self.fd.write("\n")
		self.fd.write("Num,Started,Ended,Status,%s,%s,Comment\n" % \
			( ",".join(self.testVariables),  ",".join(self.testTitles) ) )

		# Write summarization lines
		for l in self.summaryLines:
			self.fd.write(l)

		# Flush
		self.fd.flush()

	def iteration_start( self, iteration ):
		"""
		Log the start of a test
		"""

		# Log the beginning of test and starting date
		self.fd.write("%i,%i of %i,%s" % \
			( self.testID, iteration, self.iterations, str(datetime.datetime.now()) ) )
		self.fd.flush()

	def iteration_end(self, results, status="Completed", comment="" ):
		"""
		Log the completion of a test
		"""

		# Write end and values
		self.fd.write(",%s,%s,%s,%s,%s\n" % \
			( str(datetime.datetime.now()), status, ",".join(self.activeTest), ",".join(results.render()), comment ) )
		self.fd.flush()

	def test_start( self, testContext ):
		"""
		Log the start of a groupped test
		"""

		# Prepare properties
		self.testID += 1
		self.activeTest = [ str(testContext[x]) for x in self.testVariables ]

		# Keep for summary
		self.summaryLines.append(
				"%i,%s," % ( self.testID, str(datetime.datetime.now()) )
			)

	def test_end( self, results, status="Completed", comment="" ):
		"""
		Log the end of a groupped test
		"""

		# Write end and values
		self.summaryLines[ len(self.summaryLines)-1 ] += \
			",%s,%s,%s,%s,%s\n" % ( str(datetime.datetime.now()), status, ",".join(self.activeTest), ",".join(results.render()), comment ) 


