#!/usr/bin/env python

import sys
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

# Load specs
specs = Specs( sys.argv[1] )
specs.load()

# Create test contexts
tests = specs.createTestContexts()

# Create reporter
reporter = specs.createReporter()

# Create stream context for every test
for test in tests:

	# Create a test driver
	driver = TestDriver( specs, test )

	# Start reporting the test
	reporter.log_start( test )

	# Run multiple iterations of the test
	for i in range( 0, specs.stats.iterations ):
		driver.run()

	# Summarize iterations and finalize test
	reporter.log_end( driver.summarize() )

	# print streams[0].pipe.pipe_stdin()
	# print streams[0].context
	# print streams[0].metrics.titles()

# print specs.specs
# print specs.context

