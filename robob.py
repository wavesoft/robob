#!/usr/bin/env python

import sys
import time
import signal
import logging
import robob.logger

from robob.util import time2sec
from robob.specs import Specs
from robob.driver import TestDriver

def help():
	"""
	Show help screen
	"""
	print "Use: run.sh <path-to-benchmark>"
	sys.exit(1)

# Show help screen if missing arguments
if len(sys.argv) < 2:
	help()

# Get a logger
logger = logging.getLogger("robob")

# Load specs
specs = Specs( sys.argv[1] )
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

		# Start log
		logger.info("Running test %i/%i (iteration %i/%i) (%s)" % (test_id+1, len(tests), i+1, iterations, \
			", ".join([ "%s=%s" % (k, str(v)) for k,v in test['curr'].iteritems() ]) ))
		reporter.iteration_start( i+1 )

		# Run driver
		driver.run()
		reporter.iteration_end( driver.lastResults, driver.lastStatus )

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
