
import random
import string
import shlex
import subprocess
from robob.pipe import PipeBase

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

	def pipe_cmdline(self):
		"""
		Return piped command-line
		"""

		# We are piping everything to bash
		return [ "/bin/bash" ]

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
				frag_script = subprocess.list2cmdline(cmdline)

			# Add semi-colon at the end of the fragment if we don't already
			# have a command terminator
			if not frag_script[-1] in ["\n", ";"]:
				frag_script += ";"

			# Define fragment with prefixed stdout & stderr
			s_defs += "function frag_%i {\n" % (i,)
			s_defs += "{ { %s } 2>&3 | awk >&2 '$0=\"%s\"$0'; } 3>&1 1>&2 | awk '$0=\"%s\"$0';\n" % \
				(frag_script, prefix, prefix)
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
		script = "# Definitions\n"
		script += s_defs
		script += "# Signal hooks\n"
		script += s_killtrap.replace("@@", "SIGINT")
		script += s_killtrap.replace("@@", "SIGHUP")
		script += s_killtrap.replace("@@", "SIGKILL")
		script += "# Run script\n"
		script += s_run
		script += "# Wait for first fragment complete\n"
		script += "wait $FRAG_PID_0\n"
		script += "RET=$?\n"
		script += "# Interrupt the rest\n"
		script += "killer_SIGINT\n"
		script += "exit $RET\n"

		# Return script
		return script

	def pipe_stdout(self, stdout):
		"""
		Forward stdout line to the appropriate pipe
		"""

		# Trigger to local listeners
		for l in self.listeners:
			l.got_stdout( stdout )

		# Validate line
		if stdout[0:2] != "::":
			raise RuntimeError("Malformed stdout line received (Missing prefix)")

		# Find end
		end = stdout.find("::",2)
		if end < 0:
			raise RuntimeError("Malformed stdout line received (Missing suffix)")

		# Extract ID
		uid = int(stdout[2:end])
		if uid >= len(self.pipes):
			raise RuntimeError("Malformed stdout line received (Invalid pipe ID)")

		# Forward to the correct pipe
		self.pipes[uid].pipe_stdout( stdout[end+2:] )

	def pipe_stderr(self, stderr):
		"""
		Forward stderr line to the appropriate pipe
		"""

		# Trigger to local listeners
		for l in self.listeners:
			l.got_stderr( stderr )

		# Validate line
		if stderr[0:2] != "::":
			raise RuntimeError("Malformed stderr line received (Missing prefix)")

		# Find end
		end = stderr.find("::",2)
		if end < 0:
			raise RuntimeError("Malformed stderr line received (Missing suffix)")

		# Extract ID
		uid = int(stderr[2:end])
		if uid >= len(self.pipes):
			raise RuntimeError("Malformed stderr line received (Invalid pipe ID)")

		# Forward to the correct pipe
		self.pipes[uid].pipe_stderr( stderr[end+2:] )
