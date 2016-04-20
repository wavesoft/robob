
from robob.pipe import PipeBase

class Pipe(PipeBase):
	"""
	Local access is just a pass-through pipe
	"""

	def pipe_cmdline(self):
		"""
		Pipe local arguments to command-line
		"""

		# Prepare args
		args = [ "/bin/bash", "/dev/stdin" ]

		# Append child command-lines
		args += super(Pipe, self).pipe_cmdline()

		# Return new arguments
		return args

