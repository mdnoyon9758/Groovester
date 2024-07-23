import logging as log
from threading import Condition, Lock

import discord
from validators import url

from src.constants import ClientMessages, DebugMessages, ErrorMessages, InfoMessages
from src.helpers import downloadYouTubeVideo

log.getLogger(__name__)  # Set same logging parameters as client.py.


class GroovesterEventHandler:

    def __init__(self):

        # List to store absolute path of audio files to play.
        self.listOfDownloadedSongsToPlay = []

        # Synchronization variables.
        # Either one reader or one writer at a time.
        self.numReaders = 0
        self.numWriters = 0
        self._readerLock = (
            Lock()
        )  # Used when the Discord bot will load next song to local variable.
        self._writerLock = Lock()  # Used when commands like "!play" are issued.
        self.readerCv = Condition(lock=self._readerLock)
        self.writerCv = Condition(lock=self._writerLock)

        self.audioSource = None
        self.voiceClient = None

        self.lastChannelCommandWasEntered = None

    async def joinClientEvent(self, message):
        """Client event, which is used to connect Groovester to a Voice Channel."""

        # Validate author is in a voice channel.
        if message.author.voice:
            # Connect Groovester to voice channel.
            try:
                voiceChannel = message.author.voice.channel
                self.voiceClient = await voiceChannel.connect()
                log.debug(
                    "!join successfully connected to the voice channel: %s (ID: %s)",
                    voiceChannel.name,
                    voiceChannel.id,
                )
            except discord.ClientException as err:
                log.error(err)
                return False
            except Exception as err:
                log.error(err)
                return False
        else:
            log.error("!join failed, author is not in a voice channel.")
            await message.channel.send(ErrorMessages._joinCommandNoActiveVoiceChannel)
            return False

        with self.readerCv:
            self.readerCv.notify()

        #! Todo: Send a list of useful commands to the text channel.
        await message.channel.send(
            "!join successfully completed, here are some useful commands to get you started: "
        )

        return True

    async def leaveClientEvent(self, message):
        """Client event, which is used to disconnect Groovester from a Voice Channel."""

        # Validate Groovester is in a voice channel.
        if not self.voiceClient == None:
            # If connected to a voice channel, disconnect Groovester.
            if self.voiceClient.is_connected():
                try:
                    voiceChannel = message.author.voice.channel
                    self.voiceClient = await self.voiceClient.disconnect()
                    log.debug(
                        "!leave successfully disconnected from the voice channel: %s (ID: %s)",
                        voiceChannel.name,
                        voiceChannel.id,
                    )
                except discord.ClientException as err:
                    log.error(err)
                    return False
                except Exception as err:
                    log.error(err)
                    return False
        else:
            log.error("!leave failed, Groovester is not in a voice channel.")
            await message.channel.send(ErrorMessages._leaveCommandNoActiveVoiceChannel)

            return False

        await message.channel.send("Bye, bye! :(")
        #! Todo: print the number of songs still in queue.

        return True

    async def playClientEvent(self, message):
        """Client event to download a song and place it in the queue."""

        # Input validation.

        # Isolate URL parameter from command.
        linkToYouTubeVideo = str(message.content)

        # Ensure format of "!play " (emphasis on ' '), not "!play-" or "!play#"
        if len(message.content) > 5 and linkToYouTubeVideo[5] == " ":
            linkToYouTubeVideo = message.content.split(" ")[1]
        else:
            await message.channel.send(ErrorMessages._playCommandIncorrectParameters)
            return False

        # Check domain is what is expected.
        if not linkToYouTubeVideo.startswith("https://www.youtube.com/"):
            await message.channel.send(ErrorMessages._playCommandIncorrectDomain)
            return False

        # Test if the Domain is reachable and valid. (Emphasis on Domain)
        if not url(linkToYouTubeVideo):
            await message.channel.send(ErrorMessages._playCommandUnreachableDomain)
            return False

        #! Todo: Add logic to limit the number of downloaded videos to ten.
        # Download the YouTube video.
        absPathToDownloadedVideo = downloadYouTubeVideo(linkToYouTubeVideo)
        if absPathToDownloadedVideo is None:
            await message.channel.send(
                "Groovester failed to download the requested video!"
            )
            return False

        # Acquire lock and await signal.
        with self.writerCv:
            while (  # Fall through if there are no active readers or writers.
                self.numReaders > 0 and self.numWriters > 0
            ):

                self.writerCv.wait()
            self.numWriters = self.numWriters + 1

            # Enter mutual exclusion and add song to queue.
            self.listOfDownloadedSongsToPlay.append(absPathToDownloadedVideo)
            log.debug(
                "%s %s", DebugMessages._playAddingVideoToQueue, absPathToDownloadedVideo
            )

            self.numWriters = self.numWriters - 1
            # Signal any threads waiting to run.
            with self.readerCv:
                self.readerCv.notify()
            self.writerCv.notify()

    async def stopClientEvent(self, channel):
        """Helper function, used to stop Groovester from streaming audio to the voice channel."""

        if self.voiceClient is not None:
            if not self.voiceClient.is_connected():
                await channel.send("Groovester is not in a voice channel!")
                return False
            if not self.voiceClient.is_playing():
                await channel.send("Groovester is not playing audio!")
                return False

            self.voiceClient.stop()

        else:
            await channel.send(
                "Groovester's Discord voice client instance hasn't been started!"
            )
            return False

        return True
