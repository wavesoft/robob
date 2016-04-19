#!/usr/bin/env python

import sys
from robob.specs import Specs

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

# Create stream context for every test
for test in tests:

	# Get stream objects for each test context
	streams = specs.createStreams( test )

	print streams[0].pipe.pipe_stdin()
	# print streams[0].context
	# print streams[0].metrics.titles()

# print specs.specs
# print specs.context

