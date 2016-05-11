
import logging

(BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE) = list(range(8))

#These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

#: Color lookup table for formatter
COLORS = {
	'WARNING': YELLOW,
	'INFO': GREEN,
	'DEBUG': BLUE,
	'CRITICAL': YELLOW,
	'ERROR': RED
}

#: Aliases for constant-sized names
ALIASES = {
	'WARNING' : 'WARN',
	'INFO'	  : 'INFO',
	'DEBUG'	  : 'DEBG',
	'CRITICAL': 'CRIT',
	'ERROR'	  : 'FAIL'
}

def formatter_message(message, use_color=True):
	"""
	Message formatter that expands $RESET and $BOLD macros
	"""
	if use_color:
		message = message.replace("$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
	else:
		message = message.replace("$RESET", "").replace("$BOLD", "")
	return message

class ColoredFormatter(logging.Formatter):
	"""
	Colored formatter
	"""

	def __init__(self, msg, use_color = True):
		logging.Formatter.__init__(self, msg)
		self.use_color = use_color

	def format(self, record):
		"""
		Format the specified log line
		"""

		levelname = record.levelname
		if self.use_color and levelname in COLORS:

			# Add color to level name
			levelname_color = COLOR_SEQ % (30 + COLORS[levelname]) + ALIASES[levelname] + RESET_SEQ
			record.levelname = levelname_color

			# Make name
			record.name = COLOR_SEQ % (30 + WHITE) + record.name + RESET_SEQ

		return logging.Formatter.format(self, record)


def init(logLevel=logging.INFO):
	"""
	Call this function to initialize global logger
	"""

	# Custom logger class with multiple destinations
	class RobobLogger(logging.Logger):

		FORMAT = "[$BOLD%(levelname)s$RESET][%(name)s] %(message)s"
		COLOR_FORMAT = formatter_message(FORMAT, True)

		def __init__(self, name):
			logging.Logger.__init__(self, name, logLevel)                

			# Use colored formatter
			color_formatter = ColoredFormatter(self.COLOR_FORMAT)

			# Add console target
			console = logging.StreamHandler()
			console.setFormatter(color_formatter)
			self.addHandler(console)

	# Set robob logger
	logging.setLoggerClass(RobobLogger)

