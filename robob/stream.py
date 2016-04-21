
import logging

from robob.util import time2sec
from robob.factories import pipeFactory, parserFactory
from robob.pipe.bashwrap import Pipe as BashWrapPipe
from robob.metrics import Metrics
from robob.pipe.app import Pipe as AppPipe

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

	# Render and return context
	return context.render()

class Stream(object):
	"""
	A stram on which tests can run
	"""

	# Last stream ID
	LAST_STREAM_ID = 0

	def __init__(self, context, metrics):
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
		self.active = True

		# Open logger
		self.logger = logging.getLogger("stream.%s" % self.name)

		# Update last stream ID
		Stream.LAST_STREAM_ID += 1

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
		if 'name' in specs:
			self.name = specs['name']
			self.logger = logging.getLogger("stream.%s" % self.name)

		# Initialize context
		self.context = streamContext( self.context, specs )

		# Check if stream is active
		if 'stream.active' in self.context:
			self.active = self.context['stream.active']
			if type(self.active) in [str, unicode]:
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

		########################################
		# Initialize parsers
		########################################

		# Locate parser names
		parser_names = []
		if 'parser' in specs:
			parser_names.append( specs['parser'] )
		elif 'parsers' in specs:
			parser_names += specs['parser']
		else:
			raise AssertionError("It's required to define at least one parser on stream")

		# Instantiate parsers
		for n in parser_names:
			if not "parser.%s" % n in self.context:
				raise AssertionError("Parser '%s' was not defined in the specs" % n)

			# Factory parser & listen for app output
			parser = parserFactory(self.context["parser.%s" % n], self.context, self.metrics )
			self.logger.debug("Adding parser %s to app listeners" % n)
			self.appPipe.listen( parser )

		# Instantiate streamlets
		if 'streamlets' in specs:
			for n in specs['streamlets']:

				# Get streamlet
				if not "streamlet.%s" % n in self.context:
					raise AssertionError("Streamlet '%s' was not defined in specs" % n)
				streamlet = self.context["streamlet.%s" % n]

				# Instantiate streamlet pipe
				if not 'class' in streamlet:
					streamlet['class'] = "robob.pipe.script"
				pipe = pipeFactory( streamlet, self.context )

				# Plug it on bash pipe
				self.logger.debug("Adding streamlet %s")
				self.appPipe.plug( pipe )

				# Get parser(s)
				parser_names = []
				if 'parser' in streamlet:
					parser_names.append( streamlet['parser'] )
				elif 'parsers' in streamlet:
					parser_names += streamlet['parser']

				# Instantiate parsers
				for n in parser_names:
					if not "parser.%s" % n in self.context:
						raise AssertionError("Parser '%s' was not defined in the specs" % n)

					# Factory parser & listen for app output
					parser = parserFactory(self.context["parser.%s" % n], self.context, self.metrics )
					self.logger.debug("Adding parser %s to app listeners" % n)
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


