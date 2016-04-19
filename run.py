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

print specs.specs
print specs.context

