import os

from src.Groovester import downloadYouTubeVideo, GroovesterEventHandler

LIMIT_OF_SONGS_TO_DOWNLOAD = 10

def acquireReaderLock(
	handler: GroovesterEventHandler
) :
	with handler.readerCv :
		while ( # Fall through if there are no active readers or writers.
	        handler.numReaders > 0
	        or handler.numWriters > 0
	        or handler.listOfDownloadedSongsToPlay.size() == 0
	    ) :
	        handler.readerCv.wait()
	    handler.numReaders = handler.numReaders + 1

    return True

def acquireWriterLock(
	handler: GroovesterEventHandler
) :
	# Acquire lock and await signal.
    with handler.writerCv :
        while ( # Fall through if there are no active readers or writers.
                handler.numReaders > 0
                or handler.numWriters > 0
        ) :
            handler.writerCv.wait()
        handler.numWriters = handler.numWriters + 1

    return True

def releaseReaderLock(
	handler: GroovesterEventHandler, 
	readerCv: Condition,
	writerCv: Condition
) :
	with readerCv :
		handler.numReaders = handler.numReaders - 1
		readerCv.notify()
		writerCv.notify()

	return True

def releaseWritererLock(
	handler: GroovesterEventHandler, 
	readerCv: Condition,
	writerCv: Condition
) :
	with readerCv :
		handler.numWriters = handler.numWriters - 1
		readerCv.notify()
		writerCv.notify()

	return True

def checkSongsInQueueExistOnFileSystem(
	handler: GroovesterEventHandler
) :
	""" 
		Thread that executes every 10 seconds and verifies the next ten 
			songs exist on the local file system. If not, it downloads 
			them. 
	"""

	queue = handler.listOfDownloadedSongsToPlay

	# Thread should continue through the duartion of Groovester's execution.
	while True : 

		# Claim reader lock and condition variable.
		acquireReaderLock(handler)	

		if len(queue) < 0 :
			
			# Scope the range of iterations for upcoming "for" loop. By default,
			# 	only download the first ten songs in queue.
			itrRange = 0
			if len(queue) < LIMIT_OF_SONGS_TO_DOWNLOAD :
				itrRange = len(queue)
			else :
				itrRange = 10

			# Iterate queue and validate songs have been downloaded to local
			# 	file system.
			for idx in range(itrRange) :
				if not os.path.exists(queue[idx]) :
					#! Todo: invoke download video function.
					#! Todo: Add new class to track URL and absolute file path 
					# 	on local file system.
					downloadYouTubeVideo("")

		# Unclaim reader lock and signal readers and writers.
		releaseReaderLock(handler)

		sleep(10)

	return True

#! Get signaled 