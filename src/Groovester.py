""" LIBRARIES """

import logging as log
import os
from pytube import YouTube
from threading import Condition, Lock, Thread
from validators import url

from src.constants import ClientMessages, DebugMessages, ErrorMessages, InfoMessages

absPathGroovester = None
log.getLogger(__name__) # Set same logging parameters as client.py.


""" FUNCTIONS """

#* Todo: Pass system argument to identify if OS is Linux or Windows. Helps setup FS.
#* Todo: Create a thread that goes through and verifies the videos stored in /tmp are still there. Compare against list.
def setupTmpDirectory() :
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


""" CLASSES """

class GroovesterEventHandler :

    """ CONSTRUCTOR """

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

        self.voiceClientInst = None


    """ MEMBER FUNCTIONS """

    async def joinClientEvent(self, message) :
        # Validate author is in a voice channel.
        if message.author.voice :
            # Connect Groovester to voice channel.
            try :
                channel = message.author.voice.channel
                self.voiceClientInst = await channel.connect() 
                log.debug(f"!join successfully connected to the voice channel: {channel.name} (ID: {channel.id})")
            except Exception as err :
                log.error(err)

                return False
        else :
            log.error("!join failed, author is not in a voice channel.")
            await message.channel.send(ErrorMessages._joinCommandNoActiveVoiceChannel)

            return False

        #* Todo: Send a list of useful commands to the text channel.
        await message.channel.send("!join successfully completed, here are some useful commands to get you started: ")

        return True

    async def leaveClientEvent(self, message) :

        # Validate Groovester is in a voice channel
        if not self.voiceClientInst == None :
            # If connected to a voice channel, disconnect Groovester.
            if self.voiceClientInst.is_connected() :
                try :
                    channel = message.author.voice.channel
                    self.voiceClientInst = await self.voiceClientInst.disconnect() 
                    log.debug(f"!leave successfully disconnected from the voice channel: {channel.name} (ID: {channel.id})")
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

        #* Todo: Ensure that the local file system has enough space for the video.
        try :
            ytObj = YouTube(linkToYouTubeVideo)
            # Download video via pytube API.
            audioStream = ytObj.streams.get_audio_only()
            audioStream.download()
            log.debug(f"{InfoMessages._playSuccessfulyDownloadedVideo} {linkToYouTubeVideo}")
        except OSError as err:
            log.error(f"{ErrorMessages._playFailedToDownloadVideoException} {err}")

            return False

        # Acquire lock and await signal.
        with self.writerCv :
            while ( # Fall through if there are no active readers or writers.
                    self.numReaders > 0 
                    or self.numWriters > 0
                ) :
            
                self.writerCv.wait()
            self.numWriters = self.numWriters + 1

            # Enter mutual exclusion and add song to queue.
            absPathToYtAudio = (
                absPathGroovester + ytObj.title
            )
            self.listOfDownloadedSongsToPlay.append(absPathToYtAudio)
            log.debug(f"{DebugMessages._playAddingVideoToQueue} {absPathToYtAudio}")

            self.numWriters = self.numWriters - 1
            # Signal any threads waiting to run.
            with self.readerCv :
                self.readerCv.notify()
            self.writerCv.notify() 


    def playDownloadedSongViaDiscordAudio() :
        with readerCv :
            while ( # Fall through if there are no active readers or writers.
                self.numReaders > 0 
                or self.numWriters > 0 
                or self.listOfDownloadedSongsToPlay.size() == 0
            ) : # ! Todo: For now spin-lock, evenutally have bounded-buffer
                readerCv.wait()
            numReaders = numReaders + 1

            # Store absolute path to downloaded song to play
            tempAbsPathToDownloadedVideoToPlay = ""
            tempAbsPathToDownloadedVideoToPlay = self.listOfDownloadedSongsToPlay[0]
            self.listOfDownloadedSongsToPlay = self.listOfDownloadedSongsToPlay[1:]

            self.numReaders = self.numReaders - 1
            with self.writerCv :
                self.writerCv.notify()

            #! Todo: Check that bot is in voice channel. If not recoomned user issues !join command.

            #! Todo: Begin playing song over the Discord voice channel.

            #! Todo: Delete the downloaded file after song ends.
            if os.path.exists(tempAbsPathToDownloadedVideoToPlay) :
                try :
                    os.rm(tempAbsPathToDownloadedVideoToPlay)
                except OSError as err :
                    log.error(err) 

                    return False

        return True