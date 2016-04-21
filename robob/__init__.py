
def time2sec(timestr):
	"""
	Conver time specs to seconds
	"""

	if timestr[-1] == "s":
		return int(timestr[0:-1])
	elif timestr[-1] == "m":
		return int(timestr[0:-1]) * 60
	elif timestr[-1] == "h":
		return int(timestr[0:-1]) * 60 * 60
	else:
		return int(timestr)
