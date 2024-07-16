""" LIBRARIES """

import logging as log
import os
from threading import Condition, Lock

import discord
from pytube import YouTube
from validators import url

from src.constants import ClientMessages, DebugMessages, ErrorMessages, InfoMessages

absPathGroovester = None
log.getLogger(__name__)  # Set same logging parameters as client.py.


#! Todo: Make class that can store URL and absolute file path on local file
#   system.
def downloadYouTubeVideo(linkToYouTubeVideo: str):
    # * Todo: Ensure that the local file system has enough space for the video.
    ytObj = YouTube(linkToYouTubeVideo)
    audioStream = ytObj.streams.get_audio_only()  # Only download audio, saves as .mp4

    # Download video via pytube API.
    try:
        audioStream.download()
        log.debug(
            "%s %s", InfoMessages._playSuccessfulyDownloadedVideo, linkToYouTubeVideo
        )
    except OSError as err:
        log.error("%s %s", ErrorMessages._playFailedToDownloadVideoException, err)
        return None
    except Exception as err:
        log.error(err)
        return None

    return ytObj


# * Todo: Pass system argument to identify if OS is Linux or Windows. Helps setup FS.
# * Todo: Create a thread that goes through and verifies the videos stored in /tmp are still there.
# *      Compare against list.
def setupTmpDirectory():
    """Used to setup the directory to store YouTube videos."""
    global absPathGroovester
    absPathGroovester = ""

    absPathGroovester = absPathGroovester + "/tmp/Groovester"
    if not os.path.exists(absPathGroovester):
        try:
            os.mkdir(absPathGroovester)
        except OSError as err:
            log.error(err)
            return False
        except Exception as err:
            log.error(err)
            return False

    absPathGroovester = absPathGroovester + "/downloads"
    if not os.path.exists(absPathGroovester):
        try:
            os.mkdir(absPathGroovester)
        except OSError as err:
            log.error(err)
            return False
        except Exception as err:
            log.error(err)
            return False

    os.chdir(absPathGroovester)

    return True


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

        # * Todo: Send a list of useful commands to the text channel.
        await message.channel.send(
            "!join successfully completed, here are some useful commands to get you started: "
        )

        return True

    async def leaveClientEvent(self, message):

        # Validate Groovester is in a voice channel
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
        # * Todo: print the number of songs still in queue.

        return True

    async def playClientEvent(self, message):

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
        ytObj = downloadYouTubeVideo(linkToYouTubeVideo)
        if ytObj is None:
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
            absPathToYtAudio = absPathGroovester + ytObj.title
            self.listOfDownloadedSongsToPlay.append(absPathToYtAudio)
            log.debug("%s %s", DebugMessages._playAddingVideoToQueue, absPathToYtAudio)

            self.numWriters = self.numWriters - 1
            # Signal any threads waiting to run.
            with self.readerCv:
                self.readerCv.notify()
            self.writerCv.notify()

    async def speakInVoiceChannel(self, channel):
        absPathToSongToPlay = self.listOfDownloadedSongsToPlay[0]

        await channel.send("Let's play some audio!")
        # ffmpegKwargs = { # Optimized settings for ffmpeg for audio streaming, https://stackoverflow.com/questions/75493436/why-is-the-ffmpeg-process-in-discordpy-terminating-without-playing-anything
        # #   'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        #   'options': '-vn -filter:a "volume=0.75"'
        # }
        self.audioSource = discord.FFmpegOpusAudio(
            executable="/usr/bin/ffmpeg", source=absPathToSongToPlay
        )
        log.debug(self.audioSource)

        # Check that bot is in voice channel.
        if not self.voiceClient.is_connected():
            log.error(
                "Groovester failed to play audio! "
                + "Groovester has not connected to a voice channel yet!"
            )
            await channel.send(
                "Groovester failed to play audio! "
                + "Groovester has not connected to a voice channel yet!\n"
                + "Please issue the !join command while connected to a voice channel..."
            )
            return False

        # Check if Groovester is already playing a song.
        if self.voiceClient.is_playing():
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

        try:
            log.debug("Attempting to play audio source: %s", absPathToSongToPlay)
            self.voiceClient.play(self.audioSource)
            log.debug(
                "Groovester successfully played an audio source: %s",
                absPathToSongToPlay,
            )
        except discord.ClientException as err:
            self.voiceClient.stop()
            log.error(err)
            await channel.send(
                "An exception was caught while Groovester was playing audio, see Groovester.log for details."
            )
            return False

        return True

    async def stopClientEvent(self, channel):

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
