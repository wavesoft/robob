#!/usr/bin/env python

import sys
import logging
import robob.logger

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

# Create stream context for every test
test_id = 0
for test in tests:

	# Create a test driver
	driver = TestDriver( specs, test )

	# Start reporting the test
	reporter.test_start( test )

	# Run multiple iterations of the test
	for i in range( 0, specs.stats.iterations ):

		# Start log
		logger.info("Running test %i/%i (iteration %i/%i)" % (test_id+1, len(tests), i+1, specs.stats.iterations))
		reporter.iteration_start( i+1 )

		# Run driver
		driver.run()
		reporter.iteration_end( driver.lastResults )

	# Summarize iterations and finalize test
	reporter.test_end( driver.summarize() )

	# Increment test ID
	test_id += 1

# Finalize reporter
reporter.finalize()
reporter.close()
