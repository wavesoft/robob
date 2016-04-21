
import sys
import logging
import random
import string
import shlex
import subprocess
from robob.pipe import PipeBase

def list2cmdline(seq):
	"""
	Modified version of the original from subprocess.py
	"""
	result = []
	needquote = False
	for arg in seq:
		bs_buf = []

		# Add a space to separate this argument from the others
		if result:
			result.append(' ')

		needquote = (" " in arg) or ("\t" in arg) or (";" in arg) or not arg
		if needquote:
			result.append('"')

		for c in arg:
			if c == '\\':
				# Don't know if we need to double yet.
				bs_buf.append(c)
			elif c == '"':
				# Double backslashes.
				result.append('\\' * len(bs_buf)*2)
				bs_buf = []
				result.append('\\"')
			else:
				# Normal char
				if bs_buf:
					result.extend(bs_buf)
					bs_buf = []
				result.append(c)

		# Add remaining backslashes, if any.
		if bs_buf:
			result.extend(bs_buf)

		if needquote:
			result.extend(bs_buf)
			result.append('"')

	return ''.join(result)

class Pipe(PipeBase):
	"""
	Implementation of the bash wrapper that takes 
	"""

	def __init__(self, ctx):
		"""
		Initialize pipe
		"""
		super(Pipe, self).__init__(ctx)

		# Init properties
		self.script_blocks = []
		self.logger = logging.getLogger("pipe.bashwrap")

	def pipe_cmdline(self):
		"""
		Return piped command-line
		"""

		# We are piping everything to bash
		return [ "/usr/bin/stdbuf", "-oL", "-eL", "/bin/bash", "/dev/stdin" ]

	def pipe_stdin(self):
		"""
		Return piped stdin
		"""

		# Definitions
		s_defs = ""
		s_run = ""
		s_killtrap = "function killer_@@ {\n"

		# Prepare pipe chunks
		for i in range(0, len(self.pipes)):
			p = self.pipes[i]

			# Prepare prefix for this pipe
			prefix = "::%i::" % i

			# Get fragment script
			cmdline = p.pipe_cmdline()
			if cmdline[0] == "eval":
				frag_script = " ".join(cmdline[1:])
			else:
				frag_script = list2cmdline(cmdline)

			# Add semi-colon at the end of the fragment if we don't already
			# have a command terminator
			if not frag_script[-1] in ["\n", ";"]:
				frag_script += ";"

			# Define fragment with prefixed stdout & stderr
			s_defs += "function frag_%i {\n" % (i,)
			s_defs += "{ { %s } 2>&3 | awk >&2 '$0=\"%s\"$0'; exit ${PIPESTATUS[0]}; } 3>&1 1>&2 | awk '$0=\"%s\"$0';\n" % \
				(frag_script, prefix, prefix)
			s_defs += "return ${PIPESTATUS[0]}\n"
			s_defs += "}\n"

			# Define runner function
			s_defs += "function run_%i {\n" % (i,)
			inbuf = p.pipe_stdin()
			if inbuf:
				eof_indicator = "STDIN%i_" % (i,)
				eof_indicator += ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
				s_defs += "cat <<'%s' | frag_%i\n" % (eof_indicator,i)
				s_defs += inbuf
				s_defs += "\n%s" % eof_indicator
			else:
				s_defs += "frag_%i;" % (i,)
			s_defs += "\n}\n"

			# Define run script
			s_run += "run_%i&\nFRAG_PID_%i=$!\n" % (i,i)

			# Define killer trap
			s_killtrap += "kill -@@ $FRAG_PID_%i 2>/dev/null\n" % (i,)

		# Finalize fragments
		s_killtrap += "trap - @@\n"
		s_killtrap += "}\ntrap killer_@@ @@\n"

		# Compile script
		script = "# Prepare\n"
		script += "stty -echo\n"
		script += "# Definitions\n"
		script += s_defs
		script += "# Signal hooks\n"
		script += s_killtrap.replace("@@", "SIGINT")
		script += s_killtrap.replace("@@", "SIGHUP")
		script += s_killtrap.replace("@@", "SIGKILL")
		script += "# Run script\n"
		script += s_run
		script += "echo ::I::Application started\n"
		script += "# Wait for first fragment complete\n"
		script += "wait $FRAG_PID_0\n"
		script += "RET=$?\n"
		script += "echo ::I::Application exited with code=$RET\n"
		script += "# Interrupt the rest\n"
		script += "killer_SIGINT\n"
		script += "exit $RET\n"

		# sys.stdout.write("----BEGIN SCRIPT----\n%s\n----END SCRIPT----" % script)

		# Return script
		return script

	def pipe_stdout(self, stdout):
		"""
		Forward stdout line to the appropriate pipe
		"""

		# Trigger to local listeners
		self.logger.debug("Handling '%s'" % stdout)
		for l in self.listeners:
			l.got_stdout( stdout )

		# Validate line
		if stdout[0:2] != "::":
			self.logger.debug("Ignoring line (Missing prefix): %s" % stdout)
			return

		# Find end
		end = stdout.find("::",2)
		if end < 0:
			self.logger.debug("Ignoring line (Missing suffix): %s" % stdout)
			return

		# Extract line code
		lc = stdout[2:end]
		if lc == "I":
			self.logger.info(stdout[end+2:])
			return
		elif lc == "W":
			self.logger.warn(stdout[end+2:])
			return
		elif lc == "E":
			self.logger.error(stdout[end+2:])
			return

		# Extract ID
		uid = int(lc)
		if uid >= len(self.pipes):
			self.logger.debug("Ignoring line (Invalid pipe ID): %s" % stdout)
			return

		# Forward to the correct pipe
		self.logger.debug("Forwarding '%s' to pipe #%i" % ( stdout[end+2:], uid ))
		self.pipes[uid].pipe_stdout( stdout[end+2:] )

