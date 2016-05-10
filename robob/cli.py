import sys
import os
import time
import signal
import logging
import robob.logger

from robob.util import time2sec
from robob.specs import Specs
from robob.driver import TestDriver

def help(verbose=False):
	"""
	Show help screen
	"""
	print("RoBOB - Simplify collection of measurements over repetitive tasks")
	print("Read more: https://github.com/wavesoft/robob/wiki")
	print("")
	print("Usage: robob <path-to-benchmark.yaml>")
	print("")
	sys.exit(1)

def main():

	# Get a logger
	logger = logging.getLogger("robob")

	# Show help screen if missing arguments
	if len(sys.argv) < 2:
		help()
		return 2

	# Check for help
	if sys.argv[1] in ['-h', '--help']:
		help(True)
		return 0

	# Validate file
	specsfile = sys.argv[1]
	if not os.path.isfile(specsfile):
		logger.error("The specified file '%s' was not found!" % specsfile)
		help()
		return 1

	# Load specs
	specs = Specs( specsfile )
	specs.load()

	# Create test contexts
	tests = specs.createTestContexts()

	# Create reporter
	reporter = specs.createReporter()
	reporter.start()

	# Gracefully shutdown
	def cleanup(signal, frame):

		# Interrupt reporter
		logger.warn("Received break signal from the user")	

		# Interrupt driver and reporter
		driver.interrupt()
		reporter.interrupt( driver.summarize() )
		reporter.close()

		# Exit with error
		sys.exit(1)

	# Trap shutdown signal
	signal.signal(signal.SIGINT, cleanup)

	# Create stream context for every test
	driver = None
	test_id = 0
	for test in tests:

		# Create a test driver
		driver = TestDriver( specs, test )

		# Get some values from test specs
		iterations = int(test.get("test.iterations", 1))
		cooldown = time2sec(test.get("test.cooldown", 0))

		# Start reporting the test
		reporter.test_start( test )

		# Run multiple iterations of the test
		for i in range( 0, iterations ):

			# Calculate progress
			p_total = (len(tests) * iterations)
			p_curr = test_id * iterations + i

			# Start log
			logger.info("Running %i/%i (test: %i/%i, iteration: %i/%i, values: {%s})" % (p_curr+1, p_total, test_id+1, len(tests), i+1, iterations, \
				", ".join([ "%s=\"%s\"" % (k, str(v)) for k,v in test['curr'].iteritems() ]) ))
			reporter.iteration_start( i+1 )

			# Run driver
			driver.run(i)
			reporter.iteration_end( driver.lastResults, driver.lastStatus, driver.lastComment )

			# Apply cooldown
			if cooldown:
				logger.info("Waiting for %s sec before next test" % test.get("test.cooldown", "0"))
				time.sleep(cooldown)

		# Summarize iterations and finalize test
		reporter.test_end( driver.summarize() )

		# Increment test ID
		test_id += 1

	# Finalize reporter
	reporter.finalize()
	reporter.close()
	return 0
