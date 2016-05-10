
import datetime
import logging
from collections import OrderedDict

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
		self.iterations = int(specs.specs.get("test.iterations", 1))
		self.testVariables = specs.getTestVariables()
		self.testTitles = specs.getMetricTitles()
		self.activeTest = []
		self.summaryLines = []

		self.in_iteration = False
		self.in_test = False
		self.cur_iterations = 0
		self.ok_iterations = 0

		# Calculate maximum title width
		self.testTitleWidth = 1
		for t in self.testTitles:
			if len(t) > self.testTitleWidth:
				self.testTitleWidth = len(t)

		# Open logger
		self.logger = logging.getLogger("report")

		# Collect metadata
		self.notes = OrderedDict()
		if 'title' in specs.specs:
			self.notes['Title'] = specs.specs['title']
		if 'desc' in specs.specs:
			self.notes['Description'] = specs.specs['desc']
		if 'notes' in specs.context:
			self.notes.update( specs.context['notes'] )

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
		for k,v in self.notes.items():
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
		self.fd.write("Num,Started,Ended,Iterations,Successful,%s,%s,Comment\n" % \
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

		# Enter iteration
		self.in_iteration = True
		self.cur_iterations += 1

	def iteration_end(self, results, status="Completed", comment="" ):
		"""
		Log the completion of a test
		"""

		# Write end and values
		self.fd.write(",%s,%s,%s,%s,%s\n" % \
			( str(datetime.datetime.now()), status, ",".join(self.activeTest), ",".join(results.render()), comment ) )
		self.fd.flush()

		# Count successful iterations
		if status == "Completed":
			self.ok_iterations += 1

		# Exit iteration
		self.in_iteration = False

		# Print values
		rendered = results.render( True )
		self.logger.info( "-" * (self.testTitleWidth + 20) )
		for i in range(0, len(self.testTitles)):
			self.logger.info(
				(("%%%is : ") % self.testTitleWidth) % self.testTitles[i] + rendered[i]
			)
		self.logger.info( "-" * (self.testTitleWidth + 20) )

	def test_start( self, testContext ):
		"""
		Log the start of a groupped test
		"""

		# Reset iterations
		self.iterations = int(testContext.get("test.iterations", 1))
		self.cur_iterations = 0
		self.ok_iterations = 0

		# Prepare properties
		self.testID += 1
		self.activeTest = [ str(testContext[x]) for x in self.testVariables ]
		self.in_test = True

		# Keep for summary
		self.summaryLines.append(
				"%i,%s" % ( self.testID, str(datetime.datetime.now()) )
			)

	def test_end( self, results, comment="" ):
		"""
		Log the end of a groupped test
		"""

		# Write end and values
		self.summaryLines[ len(self.summaryLines)-1 ] += \
			",%s,%i,%i,%s,%s,%s\n" % ( str(datetime.datetime.now()), self.cur_iterations, self.ok_iterations, ",".join(self.activeTest), ",".join(results.render()), comment ) 

		self.in_test = False


	def interrupt(self, results, reason="Interrupted by the user"):
		"""
		User interrupted the test, log the action
		"""

		# Finalize iterations
		if self.in_iteration:
			self.fd.write(",%s,%s,%s,%s,%s\n" % \
				( str(datetime.datetime.now()), "Interrupted", ",".join(self.activeTest), ",".join( [""] * len(self.testTitles) ), reason ) )

		# Finalize test
		if self.in_test:
			if not results:
				self.fd.write(",%s,%s,%s,%s,%s\n" % \
					( str(datetime.datetime.now()), "Interrupted", ",".join(self.activeTest), ",".join( [""] * len(self.testTitles) ), reason ) )
			else:
				self.summaryLines[ len(self.summaryLines)-1 ] += \
					",%s,%i,%i,%s,%s,%s\n" % ( str(datetime.datetime.now()), self.cur_iterations, self.ok_iterations, ",".join(self.activeTest), ",".join(results.render()), reason ) 

		# Finalize
		self.finalize()

