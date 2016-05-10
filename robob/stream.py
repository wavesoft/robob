
import os
import re
import logging
import random
import string

from robob.util import time2sec
from robob.factories import pipeFactory, parserFactory
from robob.metrics import Metrics
from robob.logpipe import LogPipe
from robob.pipe.bashwrap import Pipe as BashWrapPipe
from robob.pipe.app import Pipe as AppPipe
from robob.pipe.filegen import Pipe as FileGenPipe
from robob.pipe.filedel import Pipe as FileDelPipe

def streamContext( context, specs ):
	"""
	Update given context for use by the stream with the given specs
	"""

	# Fork context
	context = context.fork()

	# Get node
	node = specs['node']
	if not "node.%s" % node in context:
		raise AssertionError("Node '%s' was not defined in the specs" % node)
	node = context["node.%s" % node]

	# Get app
	app = specs['app']
	if not "app.%s" % app in context:
		raise AssertionError("App '%s' was not defined in the specs" % app)
	app = context["app.%s" % app]

	# Get optional app env
	env = None
	if 'env' in app:
		env = app['env']
		if not "env.%s" % env in context:
			raise AssertionError("env '%s' was not defined in the specs" % env)
		env = context["env.%s" % env]

	########################################
	# Initialize context variables
	########################################

	# Define context of current node, parser, app
	context.set( "stream", specs )
	context.set( "node", node )
	context.set( "app", app )
	if env:
		context.set( "env", env )
		context.update( env )

	# Update custom variable definitions
	if 'define' in node:
		context.update( node['define'] )
	if 'define' in app:
		context.update( app['define'] )
	if 'define' in specs:
		context.update( specs['define'] )

	# Update app file paths if temporary
	if 'app.files' in context:
		for f in context['app.files']:

			# Create filename of temporary file
			if not 'path' in f:

				# Calcuate suffix
				suffix = ".tmp"
				if 'suffix' in f:
					suffix = f['suffix']

				# Calculate temporary path
				tmp_path = "/tmp/robob.%s-%s%s" % (
						f['name'],
						''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(24)),
						suffix
					)

				# Update context
				f['path'] = tmp_path
				f['temp'] = True
				context.set("app.files.%s.path" % f['name'], tmp_path)
				context.set('app.files.%s.temp' % f['name'], True)

			else:

				# Mark as non-temporary
				f['temp'] = False
				context.set('app.files.%s.temp' % f['name'], False)

	# Render and return context
	return context.render()

RE_SANITIZE = re.compile(r"[^A-Za-z0-9]+")

def sanitize_fname(v):
	"""
	Sanitize fileame
	"""
	return RE_SANITIZE.sub("-", str(v))

class Stream(object):
	"""
	A stram on which tests can run
	"""

	# Last stream ID
	LAST_STREAM_ID = 0

	def __init__(self, context, metrics, iteration):
		"""
		Initialize a new stream
		"""

		self.delay = 0
		self.name = "stream_%i" % Stream.LAST_STREAM_ID
		self.pipe = None
		self.bashPipe = None
		self.appPipe = None
		self.accessPipe = None
		self.metrics = metrics
		self.context = context
		self.timeout = None
		self.idletimeout = None
		self.active = True
		self.iteration = iteration

		# Open logger
		self.logger = logging.getLogger("stream.%s" % self.name)

		# Update last stream ID
		Stream.LAST_STREAM_ID += 1

	def openLogPipe(self):
		"""
		Open a pipe to the filename that will hold the output of the application
		"""

		# If missing, return none
		if not 'report.keep_output' in self.context:
			return None

		# Calculate filename
		testval = "+".join([ "%s-%s" % (k, sanitize_fname(v)) for k,v in self.context['curr'].items() ])
		filename = "out-%s-%s-%i" % (self.name, testval, self.iteration+1)
		filename += ".log"

		# Calculate directory name
		basedir = self.context['report.keep_output'] + "/"
		basedir += self.context['report.name']
		basedir += "-%s" % self.context['report.timestamp']

		# Make directory
		if not os.path.exists(basedir):
			os.mkdir(basedir)
		elif not os.path.isdir(basedir):
			raise AssertionError("Directory %s is not directory!" % basedir)

		# Log
		filename = "%s/%s" % (basedir, filename)
		self.logger.info("Logging STDOUT to %s" % filename)

		# Create and return a new logpipe
		return LogPipe(filename)

	def configure(self, specs):
		"""
		Configure stream from the specified specs context
		"""

		# Get simple properties
		self.delay = 0
		if 'delay' in specs:
			self.delay = time2sec(specs['delay'])
		if 'timeout' in specs:
			self.timeout = time2sec(specs['timeout'])
		if 'idle' in specs:
			self.idletimeout = time2sec(specs['idle'])
		if 'name' in specs:
			self.name = specs['name']
			self.logger = logging.getLogger("stream.%s" % self.name)

		# Initialize context
		self.context = streamContext( self.context, specs )

		# Check if stream is active
		if 'stream.active' in self.context:
			self.active = self.context['stream.active']
			if type(self.active) in [str, str]:
				self.active = self.active.lower() in [ "1", "yes", "true", "on" ]

		# If not active exit
		if not self.active:
			return

		########################################
		# Initialize pipes
		########################################

		# Factory app pipe
		self.appPipe = AppPipe( self.context )
		self.appPipe.configure( self.context['app'] )

		# Factory bash multiplexer/wrapper
		self.bashPipe = BashWrapPipe( self.context )
		self.bashPipe.plug( self.appPipe )

		# Factory log pipe to capture output
		out = self.openLogPipe()
		if out:
			self.appPipe.listen( out )

		########################################
		# Initialize file generators
		########################################

		# Instantiate file generators
		if 'app.files' in self.context:
			for filegen in self.context['app.files']:

				# Instantiate and configure filegen pipe
				fpipe = FileGenPipe( self.context )
				fpipe.configure( filegen )

				# Add precondition to bash pipe
				self.bashPipe.plug_pre( fpipe )

				# If this is temporary, add cleanup pipe
				if filegen['temp']:

					# Instantiate and configure file delete pipe
					dpipe = FileDelPipe( self.context )
					dpipe.configure( fpipe.path )

					# Add post-condition to bash pipe
					self.bashPipe.plug_post( dpipe )

		########################################
		# Initialize parsers
		########################################

		# Instantiate app parsers
		parser_names = []
		if 'app.parser' in self.context:
			parser_names.append( self.context['app.parser'] )
		elif 'app.parsers' in self.context:
			parser_names += self.context['app.parsers']
		else:
			raise AssertionError("It's required to define at least one parser on app '%s'" % self.context['app.name'])

		# Instantiate parsers
		for n in parser_names:
			if not "parser.%s" % n in self.context:
				raise AssertionError("Parser '%s' was not defined in the specs" % n)

			# Factory parser
			parser = parserFactory(self.context["parser.%s" % n], self.context, self.metrics )

			# Apply alias mapping & filter if exists
			if 'stream.alias' in self.context:
				self.logger.debug("Adding alias mapping to %s: %r" % (n, self.context['stream.alias']))
				parser.set_alias( self.context['stream.alias'] )
			if 'stream.filter' in self.context:
				self.logger.debug("Adding metrics filter to %s: %r" % (n, self.context['stream.filter']))
				parser.set_filter( self.context['stream.filter'] )

			# Listen for app output
			self.logger.debug("Adding parser %s to app listeners" % n)
			self.appPipe.listen( parser )

		# Instantiate streamlets
		if 'streamlets' in specs:
			for slt in specs['streamlets']:

				# Expand string shorthand
				if type(slt) in [str, str]:
					slt = { "streamlet": slt }

				# Get name
				if not 'streamlet' in slt:
					raise AssertionError("Missing 'streamlet' keyword in specs of stream '%s'" % self.name)
				n = slt['streamlet']

				# Get streamlet
				if not "streamlet.%s" % n in self.context:
					raise AssertionError("Streamlet '%s' was not defined in specs" % n)
				streamlet = self.context["streamlet.%s" % n]

				# Create a streamlet context & merge definitions
				streamlet_context = self.context.fork()
				streamlet_context.set( "streamlet", streamlet )
				streamlet_context.set( "streamlet", slt )

				# Render context
				streamlet_context = streamlet_context.render()

				# Instantiate streamlet pipe
				if not 'class' in streamlet:
					streamlet['class'] = "robob.pipe.script"
				pipe = pipeFactory( streamlet, streamlet_context )

				# Plug it on bash pipe
				self.logger.debug("Adding streamlet %s" % n)
				self.bashPipe.plug( pipe )

				# Get parser(s)
				parser_names = []
				if 'streamlet.parser' in streamlet_context:
					parser_names.append( streamlet_context['streamlet.parser'] )
				elif 'streamlet.parsers' in streamlet_context:
					parser_names += streamlet_context['streamlet.parsers']

				# Instantiate parsers
				for n in parser_names:
					if not "parser.%s" % n in streamlet_context:
						raise AssertionError("Parser '%s' was not defined in the specs" % n)

					# Factory parser
					parser = parserFactory(streamlet_context["parser.%s" % n], streamlet_context, self.metrics )

					# Apply stream alias mapping & filter if exists
					if 'stream.alias' in streamlet_context:
						self.logger.debug("Adding alias mapping to %s: %r" % (n, streamlet_context['stream.alias']))
						parser.set_alias( streamlet_context['stream.alias'] )
					if 'stream.filter' in streamlet_context:
						self.logger.debug("Adding metrics filter to %s: %r" % (n, streamlet_context['stream.filter']))
						parser.set_filter( streamlet_context['stream.filter'] )

					# Apply streamlet alias mapping & filter if exists
					if 'streamlet.alias' in streamlet_context:
						self.logger.debug("Adding streamlet alias mapping to %s: %r" % (n, streamlet_context['streamlet.alias']))
						parser.set_alias( streamlet_context['streamlet.alias'] )
					if 'streamlet.filter' in streamlet_context:
						self.logger.debug("Adding streamlet metrics filter to %s: %r" % (n, streamlet_context['streamlet.filter']))
						parser.set_filter( streamlet_context['streamlet.filter'] )

					# Factory parser & listen for app output
					self.logger.debug("Adding parser %s to streamlet listeners" % n)
					pipe.listen( parser )

		########################################
		# Initialize host accessor
		########################################

		# Get node configuration
		node = self.context['node']
		if not 'access' in node:
			raise AssertionError("Required at least one access component on node specs")

		# Create and chain accessor component
		for a in node['access']:

			# Merge node components into the accessor configuration
			specs = dict(node)
			specs.update( a )

			# Create accessor pipe
			pipe = pipeFactory( specs, self.context )

			# Chain them all the way to the bash pipe
			if self.accessPipe is None:
				self.accessPipe = pipe
				self.accessPipe.plug( self.bashPipe )
			else:
				pipe.plug( self.accessPipe )
				self.accessPipe = pipe

		# That's now our master pipe and we are ready to go!
		self.pipe = self.accessPipe


