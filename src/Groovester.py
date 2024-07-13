""" LIBRARIES """

import logging as log
import os
from threading import Condition, Lock, Thread

from discord import AudioSource, DiscordException, FFmpegPCMAudio
from pytube import YouTube
from validators import url

from src.constants import ClientMessages, DebugMessages, ErrorMessages, InfoMessages

absPathGroovester = None
log.getLogger(__name__) # Set same logging parameters as client.py.

#! Todo: Make class that can store URL and absolute file path on local file
#   system.
def downloadYouTubeVideo(
    linkToYouTubeVideo: str
) :
    #* Todo: Ensure that the local file system has enough space for the video.
    try :
        ytObj = YouTube(linkToYouTubeVideo)
        # Download video via pytube API.
        audioStream = ytObj.streams.get_audio_only()
        audioStream.download()
        log.debug(
            "%s %s", 
            InfoMessages._playSuccessfulyDownloadedVideo, 
            linkToYouTubeVideo
        )
    except OSError as err:
        log.error(
            "%s %s", 
            ErrorMessages._playFailedToDownloadVideoException, 
            err
        )

        return False

    return True

#* Todo: Pass system argument to identify if OS is Linux or Windows. Helps setup FS.
#* Todo: Create a thread that goes through and verifies the videos stored in /tmp are still there. 
#*      Compare against list.
def setupTmpDirectory() :
    """ Used to setup the directory to store YouTube videos. """
    global absPathGroovester
    absPathGroovester = ""

    absPathGroovester = (
        absPathGroovester + "/tmp/Groovester"
    )
    if not os.path.exists(absPathGroovester) :
        try :
            os.mkdir(absPathGroovester)
        except OSError as err :
            log.error(err)

            return False

    absPathGroovester = (
        absPathGroovester + "/downloads"
    )
    if not os.path.exists(absPathGroovester) :
        try :
            os.mkdir(absPathGroovester)
        except OSError as err :
            log.error(err)

            return False

    os.chdir(absPathGroovester)

    return True

class GroovesterEventHandler :

    def __init__(self) :

        """ MEMBER VARIABLES """

        # List to store absolute path of audio files to play.
        self.listOfDownloadedSongsToPlay = []

        # Synchronization variables.
        # Either one reader or one writer at a time.
        self.numReaders = 0
        self.numWriters = 0
        self._readerLock = Lock() # Used when the Discord bot will load next song to local variable.
        self._writerLock = Lock() # Used when commands like "!play" are issued.
        self.readerCv = Condition(lock=self._readerLock)
        self.writerCv = Condition(lock=self._writerLock)

        self.voiceClient = None

    async def joinClientEvent(self, message) :

        # Validate author is in a voice channel.
        if message.author.voice :
            # Connect Groovester to voice channel.
            try :
                channel = message.author.voice.channel
                self.voiceClient = await channel.connect()
                log.debug(
                    "!join successfully connected to the voice channel: %s (ID: %s)", 
                    channel.name, 
                    channel.id
                )

                await self.playDiscordAudio("", message.channel)
            except Exception as err :
                log.error(err)

                return False
        else :
            log.error("!join failed, author is not in a voice channel.")
            await message.channel.send(ErrorMessages._joinCommandNoActiveVoiceChannel)

            return False

        #* Todo: Send a list of useful commands to the text channel.
        await message.channel.send(
            "!join successfully completed, here are some useful commands to get you started: "
        )

        return True

    async def leaveClientEvent(self, message) :

        # Validate Groovester is in a voice channel
        if not self.voiceClient == None :
            # If connected to a voice channel, disconnect Groovester.
            if self.voiceClient.is_connected() :
                try :
                    channel = message.author.voice.channel
                    self.voiceClient = await self.voiceClient.disconnect()
                    log.debug(
                        "!leave successfully disconnected from the voice channel: %s (ID: %s)", 
                        channel.name, 
                        channel.id
                    )
                except Exception as err :
                    log.error(err)

                    return False
        else :
            log.error("!leave failed, Groovester is not in a voice channel.")
            await message.channel.send(ErrorMessages._leaveCommandNoActiveVoiceChannel)

            return False

        await message.channel.send("Bye, bye! :(")
        #* Todo: print the number of songs still in queue.

        return True

    async def playClientEvent(self, message) :

        # Input validation.

        # Isolate URL parameter from command.
        linkToYouTubeVideo = str(message.content)

        # Ensure format of "!play " (emphasis on ' '), not "!play-" or "!play#"
        if (len(message.content) > 5
            and linkToYouTubeVideo[5] == " ") :
            linkToYouTubeVideo = message.content.split(" ")[1]
        else :
            await message.channel.send(ErrorMessages._playCommandIncorrectParameters)

            return False

        # Check domain is what is expected.
        if not linkToYouTubeVideo.startswith("https://www.youtube.com/") :
            await message.channel.send(ErrorMessages._playCommandIncorrectDomain)

            return False

        # Test if the Domain is reachable and valid. (Emphasis on Domain)
        if not url(linkToYouTubeVideo) :
            await message.channel.send(ErrorMessages._playCommandUnreachableDomain)

            return False

        #! Todo: Add logic to limit the number of downlaoded videos to ten.
        # Download the YouTube video.
        if not downloadYouTubeVideo(linkToYouTubeVideo) :
            await message.channel.send("Groovester failed to download the requested video!")

            return False

        # Acquire lock and await signal.
        with self.writerCv :
            while ( # Fall through if there are no active readers or writers.
                    self.numReaders > 0
                    and self.numWriters > 0
                ) :

                self.writerCv.wait()
            self.numWriters = self.numWriters + 1

            # Enter mutual exclusion and add song to queue.
            absPathToYtAudio = (
                absPathGroovester + ytObj.title
            )
            self.listOfDownloadedSongsToPlay.append(absPathToYtAudio)
            log.debug(
                "%s %s",
                DebugMessages._playAddingVideoToQueue,
                absPathToYtAudio
            )

            self.numWriters = self.numWriters - 1
            # Signal any threads waiting to run.
            with self.readerCv :
                self.readerCv.notify()
            self.writerCv.notify()

    async def playDiscordAudio(self, absPathToSongToPlay, channel) :
        await channel.send("Let's play some audio!")
        audioSource = FFmpegPCMAudio("/tmp/Groovester/downloads/analog fade (new bule sky)  hot mulligan.mp4") # /tmp/Groovester/downloads/analog fade (new bule sky)  hot mulligan.mp4

        # Check that bot is in voice channel.
        if not self.voiceClient.is_connected() :
            log.error(
                "Groovester failed to play audio! "
                + "Groovester has not connected to a voice channel yet!"
            )
            await channel.send(
                "Groovester failed to play audio! "
                + "Groovester has not connected to a voice channel yet!\n"
                + "Please issue the !join command while in a voice channel..."
            )

            return False

        if not self.voiceClient.is_playing() :
            log.error(
                "Groovester failed to play audio! "
                + "Groovester is already playing audio!"
            )
            await channel.send(
                "Groovester failed to play audio! "
                + "Groovester is already playing audio!\n"
                + "Please wait for the current song to end..."
            )

            return False

        try :
            log.debug(
                "Attempting to play audio source: %s", 
                absPathToSongToPlay
            )
            self.voiceClient.play(audioSource, after=None)
            log.debug(
                "Groovester successfully played an audio source: %s", 
                absPathToSongToPlay
            )

        except DiscordException as err :
            log.error(err)
            await channel.send(
                "An exception was caught while Groovester was play audio."
            )

            return False

        return True

    def playDownloadedSongViaDiscordAudio(self) :

        with readerCv :
            while ( # Fall through if there are no active readers or writers.
                self.numReaders > 0
                or self.numWriters > 0
                or self.listOfDownloadedSongsToPlay.size() == 0
            ) :
                readerCv.wait()
            numReaders = numReaders + 1

            # Store absolute path to downloaded song to play
            tempAbsPathToDownloadedVideoToPlay = ""
            tempAbsPathToDownloadedVideoToPlay = self.listOfDownloadedSongsToPlay[0]
            self.listOfDownloadedSongsToPlay = self.listOfDownloadedSongsToPlay[1:]

            self.numReaders = self.numReaders - 1
            with self.writerCv :
                self.writerCv.notify()

            # Play song through the Discord voice channel.
            playDiscordAudio(tempAbsPathToDownloadedVideoToPlay)

            # Delete the downloaded file after song ends.
            if os.path.exists(tempAbsPathToDownloadedVideoToPlay) :
                try :
                    os.rm(tempAbsPathToDownloadedVideoToPlay)
                except OSError as err :
                    log.error(err)

                    return False

        return True
