
def time2sec(timestr):
	"""
	Conver time specs to seconds
	"""

	# Skip numerics
	if type(timestr) in [int, float]:
		return timestr

	# Process strings
	if timestr[-1] == "s":
		return float(timestr[0:-1])
	elif timestr[-1] == "m":
		return float(timestr[0:-1]) * 60
	elif timestr[-1] == "h":
		return float(timestr[0:-1]) * 60 * 60
	else:
		return float(timestr)
