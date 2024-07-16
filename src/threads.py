import os
import logging as log
from threading import Condition
from time import sleep

from src.Groovester import downloadYouTubeVideo, GroovesterEventHandler

log.getLogger(__name__)  # Set same logging parameters as client.py.

LIMIT_OF_SONGS_TO_DOWNLOAD = 10


def acquireReaderLock(handler: GroovesterEventHandler):
    with handler.readerCv:
        while (  # Fall through if there are no active readers or writers.
            handler.numReaders > 0
            or handler.numWriters > 0
            or handler.listOfDownloadedSongsToPlay.size() == 0
        ):
            handler.readerCv.wait()
        handler.numReaders = handler.numReaders + 1

    return True


def acquireWriterLock(handler: GroovesterEventHandler):
    # Acquire lock and await signal.
    with handler.writerCv:
        while (  # Fall through if there are no active readers or writers.
            handler.numReaders > 0 or handler.numWriters > 0
        ):
            handler.writerCv.wait()
        handler.numWriters = handler.numWriters + 1

    return True


def releaseReaderLock(handler: GroovesterEventHandler):
    with handler.readerCv:
        handler.numReaders = handler.numReaders - 1
        handler.readerCv.notify()

    with handler.writerCv:
        handler.writerCv.notify()

    return True


def releaseWriterLock(handler: GroovesterEventHandler):
    with handler.writerCv:
        handler.numWriters = handler.numWriters - 1
        handler.writerCv.notify()

    with handler.readerCv:
        handler.readerCv.notify()

    return True


def checkSongsInQueueExistOnFileSystem(handler: GroovesterEventHandler):
    """
    Thread that executes every 10 seconds and verifies the next ten
            songs exist on the local file system. If not, it downloads
            them.
    """

    queue = handler.listOfDownloadedSongsToPlay

    # Thread should continue through the duartion of Groovester's execution.
    while True:

        # Claim reader lock and condition variable.
        acquireReaderLock(handler)

        if len(queue) < 0:

            # Scope the range of iterations for upcoming "for" loop. By default,
            # 	only download the first ten songs in queue.
            itrRange = 0
            if len(queue) < LIMIT_OF_SONGS_TO_DOWNLOAD:
                itrRange = len(queue)
            else:
                itrRange = 10

            # Iterate queue and validate songs have been downloaded to local
            # 	file system.
            for idx in range(itrRange):
                if not os.path.exists(queue[idx]):
                    #! Todo: invoke download video function.
                    #! Todo: Add new class to track URL and absolute file path
                    # 	on local file system.
                    downloadYouTubeVideo("")

        # Unclaim reader lock and signal readers and writers.
        releaseReaderLock(handler)

        sleep(10)

    return True


# Get signaled to play audio in a Discord channel.
async def playDownloadedSongViaDiscordAudio(handler: GroovesterEventHandler):
    log.info("playSongsInDiscordAudioThread has started!")

    queue = handler.listOfDownloadedSongsToPlay

    while True:

        # Spin lock until various conditions are met.
        with handler.readerCv:
            # Check that there are songs in the queue.
            while len(queue) <= 0:
                log.debug("Giving up time slice, waiting for songs in queue.")
                handler.readerCv.wait()
            # Check if the Voice Cleint has been instantiated.
            while handler.voiceClient is None:
                log.debug(
                    "Giving up time slice, waiting for voice client to instantiate."
                )
                handler.readerCv.wait()
            # Check if the Voice Client is connected to a Voice Channel.
            while not handler.voiceClient.is_connected():
                log.debug(
                    "Giving up time slice, waiting for voice client to connect to a voice channel."
                )
                handler.readerCv.wait()
            # Check if the Voice Client instance is already playing a song.
            while handler.voiceClient.is_playing():
                log.debug(
                    "Giving up time slice, Groovester's voice client is already playing a song."
                )
                handler.readerCv.wait()
            while (  # Fall through if there are no active readers or writers.
                handler.numReaders > 0 or handler.numWriters > 0
            ):
                log.debug("Giving up time slice, there are active readers or writers.")
                handler.readerCv.wait()

            handler.numReaders = handler.numReaders + 1

        # At this point, Groovester can start playing audio.

        # Store absolute path to downloaded song to play and remove it from queue.
        absPathToDownloadedVideoToPlay = queue[0]
        handler.listOfDownloadedSongsToPlay = queue[1:]

        releaseReaderLock(handler)

        # Play song through the Discord voice channel.
        await handler.speakInVoiceChannel()

        # Delete the downloaded file after song ends.
        if os.path.exists(absPathToDownloadedVideoToPlay):
            try:
                os.remove(absPathToDownloadedVideoToPlay)
            except OSError as err:
                log.error(err)
                return False

    return True
