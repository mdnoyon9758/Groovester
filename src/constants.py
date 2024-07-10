class ClientMessages :
	# Help messages.
	_helpPlayCommand = (
	    "!play usage:\t !play *URL to YouTube URL*\n"
	    + "\tGroovester will download YouTube video and play it in a voice channel!"
	)

class ErrorMessages :
	_joinCommandNoActiveVoiceChannel = (
	    "Incorrect !join usage...\n"
	    + "\tYou are not currently in a voice channel."
	)
	_leaveCommandNoActiveVoiceChannel = (
	    "Incorrect !leave usage...\n"
	    + "\tGroovester is not actively connected to a voice channel."
	)
	_playCommandIncorrectDomain = (
	    "Incorrect !play usage...\n"
	    + "\tPlease enter a valid domain."
	)
	_playCommandIncorrectParameters = (
	    "Incorrect !play usage...\n"
	    + "Usage:\t !play *URL to YouTube video*"
	)
	_playCommandUnreachableDomain = (
	    "Incorrect !play usage...\n"
	    + "Enter a valid domain."
	)