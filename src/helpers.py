import logging as log
import os

import discord
from pytube import YouTube

from src.constants import ClientMessages, DebugMessages, ErrorMessages, InfoMessages
from src.Groovester import GroovesterEventHandler

ABS_PATH_TO_TMP_GROOVESTER_DOWNLOADS = None
log.getLogger(__name__)  # Set same logging parameters as client.py.


#! Todo: Make class that can store URL and absolute file path on local file
#!  system.
def downloadYouTubeVideo(linkToYouTubeVideo: str):
    """Helper function used to download a YouTube video given a valid URL."""

    #!  Todo: Ensure that the local file system has enough space for the video.
    ytObj = YouTube(linkToYouTubeVideo)
    audioStream = ytObj.streams.get_audio_only()  # Only download audio, saves as .mp4

    # Download video via pytube API.
    try:
        absPathToDownloadedVideo = audioStream.download()
        if os.path.exists(absPathToDownloadedVideo):
            if absPathToDownloadedVideo.__contains__(" "):
                os.rename(
                    absPathToDownloadedVideo, absPathToDownloadedVideo.replace(" ", "_")
                )
                absPathToDownloadedVideo = absPathToDownloadedVideo.replace(" ", "_")
        log.debug(
            "%s %s", InfoMessages._playSuccessfulyDownloadedVideo, linkToYouTubeVideo
        )
    except OSError as err:
        log.error("%s %s", ErrorMessages._playFailedToDownloadVideoException, err)
        return None
    except Exception as err:
        log.error(err)
        return None

    return absPathToDownloadedVideo


#!  Todo: Pass system argument to identify if OS is Linux or Windows. Helps setup FS.
#!  Todo: Create a thread that goes through and verifies the videos stored in /tmp are still there.
#!       Compare against list.
def setupTmpDirectory():
    """Used to setup the directory to store YouTube videos."""

    global ABS_PATH_TO_TMP_GROOVESTER_DOWNLOADS
    ABS_PATH_TO_TMP_GROOVESTER_DOWNLOADS = ""

    ABS_PATH_TO_TMP_GROOVESTER_DOWNLOADS = (
        ABS_PATH_TO_TMP_GROOVESTER_DOWNLOADS + "/tmp/Groovester/"
    )
    if not os.path.exists(ABS_PATH_TO_TMP_GROOVESTER_DOWNLOADS):
        try:
            os.mkdir(ABS_PATH_TO_TMP_GROOVESTER_DOWNLOADS)
        except OSError as err:
            log.error(err)
            return False
        except Exception as err:
            log.error(err)
            return False

    ABS_PATH_TO_TMP_GROOVESTER_DOWNLOADS = (
        ABS_PATH_TO_TMP_GROOVESTER_DOWNLOADS + "downloads/"
    )
    if not os.path.exists(ABS_PATH_TO_TMP_GROOVESTER_DOWNLOADS):
        try:
            os.mkdir(ABS_PATH_TO_TMP_GROOVESTER_DOWNLOADS)
        except OSError as err:
            log.error(err)
            return False
        except Exception as err:
            log.error(err)
            return False

    os.chdir(ABS_PATH_TO_TMP_GROOVESTER_DOWNLOADS)

    return True


async def speakInVoiceChannel(
    handler: GroovesterEventHandler, absPathToVideoToPlay: str
):
    """Function used to allow Groovester to stream audio to the voice channel."""

    # await self.lastChannelCommandWasEntered.send("Let's play some audio!")
    # ffmpegKwargs = { # Optimized settings for ffmpeg for audio streaming, https://stackoverflow.com/questions/75493436/why-is-the-ffmpeg-process-in-discordpy-terminating-without-playing-anything
    # #   'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    #   'options': '-vn -filter:a "volume=0.75"'
    # }
    #! Todo: Optimize settings for crisp audio streaming.
    handler.audioSource = discord.FFmpegOpusAudio(
        executable="/usr/bin/ffmpeg",
        source="/tmp/Groovester/downloads/Porter_Robinson_\&_Madeon_-_Shelter_\(Wedding_Edit\)",  # absPathToVideoToPlay
    )
    log.debug(handler.audioSource)

    # Check that bot is in voice channel.
    if not handler.voiceClient.is_connected():
        log.error(
            "Groovester failed to play audio! "
            + "Groovester has not connected to a voice channel yet!"
        )
        return False

    # Check if Groovester is already playing a song.
    if handler.voiceClient.is_playing():
        log.error(
            "Groovester failed to play audio! " + "Groovester is already playing audio!"
        )
        return False

    try:
        log.debug("Attempting to play audio source: %s", absPathToVideoToPlay)
        handler.voiceClient.play(handler.audioSource)
        log.debug(
            "Groovester successfully played an audio source: %s",
            absPathToVideoToPlay,
        )
    except discord.ClientException as err:
        handler.voiceClient.stop()
        log.error(err)
        return False

    return True
