""" LIBRARIES """

import discord
from discord.ext import commands,tasks
from dotenv import load_dotenv
import logging as log
import os
from pytube import YouTube as yt
from threading import Condition, Lock, Thread
from time import sleep
from validators import url


""" GLOBAL VARIABLES """

absPathGroovester = ""
listOfDownloadedSongsToPlay = []

# Create Discord bot and client instance.
intents = discord.Intents.default()
intents.message_content = True
# bot = commands.Bot(command_prefix='!', intents=intents)
client = discord.Client(intents=intents)

# Synchronization variables.
# Either one reader or one writer at a time.
numReaders = 0
numWriters = 0
_readerLock = Lock() # Used when the Discord bot will load next song to local variable.
_writerLock = Lock() # Used when commands like "!play" are issued.
readerCv = Condition(lock=_readerLock)
writerCv = Condition(lock=_writerLock)

# Help messages.
_helpPlayCommand = (
    "!play usage:\t !play *URL to YouTube URL*\n"
    + "\tGroovester will download YouTube video and play it in a voice channel!"
)

# Error messages
_joinCommandNoActiveVoiceChannel = (
    "Incorrect !join usage...\n"
    + "\tYou are not currently in a voice channel."
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


""" FUNCTIONS """

def playDownloadedSongViaDiscordAudio() :
    global listOfDownloadedSongsToPlay, numReaders, numWriters

    with readerCv :
        while ( # Fall through if there are no active readers or writers.
            numReaders > 0 
            or numWriters > 0 
            or listOfDownloadedSongsToPlay.size() == 0
        ) : # ! Todo: For now spin-lock, evenutally have bounded-buffer
            readerCv.wait()
        numReaders = numReaders + 1

        # Store absolute path to downloaded song to play
        tempAbsPathToDownloadedVideoToPlay = ""
        tempAbsPathToDownloadedVideoToPlay = listOfDownloadedSongsToPlay[0]
        listOfDownloadedSongsToPlay = listOfDownloadedSongsToPlay[1:]

        numReaders = numReaders - 1
        with writerCv :
            writerCv.signal()

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

def setupFs() :
    global absPathGroovester

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


""" CLIENT EVENTS """

@client.event
async def on_ready() :
    strToLog = "Groovester started Successfully!"

    log.info(strToLog)
    print(strToLog)

    return True

# @bot.command(name="send", help=_helpPlayCommand)
# async def playCommand(context) :
#     await ctx.send("Hellow!")

@client.event
async def on_message(message) : # Message procedure
    global listOfDownloadedSongsToPlay, numReaders, numWriters

    # prevent bot from responding to itself
    if message.author == client.user :
        pass

    log.debug(
        f"Message received from {message.author}: {message.content}"
    )

    if message.content == "!help" :
        await message.channel.send(_helpPlayCommand)
    
    # !play: Downloads video to local file system and enrolls song in queue.
    elif message.content.startswith("!play") :

        # Input validation.

        # Isolate URL parameter from command.
        linkToYouTubeVideo = str(message.content)

        # Ensure format of "!play " (emphasis on ' '), not "!play-" or "!play#"
        if (len(message.content) > 5 
            and linkToYouTubeVideo[5] == " ") : 
            linkToYouTubeVideo = message.content.split(" ")[1]
        # Else, error handle incorrect URL.

        #* Todo: How do I make it so I don't rewrite this seciton over and over. Maybe use GOTO?
        else :
            await message.channel.send(_playCommandIncorrectParameters)
            return False

        # Check domain is what is expected. 
        if not linkToYouTubeVideo.startswith("https://youtube.com/") :
            await message.channel.send(_playCommandIncorrectDomain)
            return False

        # Test if the Domain is reachable and valid. (Emphasis on Domain)
        if not url(linkToYouTubeVideo) :
            await message.channel.send(_playCommandUnreachableDomain)
            return False

        # Download video via pytube API.
        ytObj = yt(linkToYouTubeVideo)
        ytObj = ytObj.streams.get_highest_resolution()
        try :
            ytObj.download()
            log.debug("!play successfully downloaded: " + linkToYouTubeVideo)
        except :
            log.error("!play failed, an error has occurred with downloading the YouTube video")

            return False

        # Acquire lock and await signal.
        with writerCv :
            while ( # Fall through if there are no active readers or writers.
                    numReaders > 0 
                    or numWriters > 0
                ) :
            
                writerCv.wait()
            numWriters = numWriters + 1

            # Enter mutual exclusion and add song to queue.
            absPathToYtAudio = (
                absPathGroovester + ytObj.title
            )
            listOfDownloadedSongsToPlay.append[absPathToYtAudio]
            log.debug("Adding YouTube video URL to queue: " + absPathToYtAudio)

            numWriters = numWriters - 1
            # Signal any threads waiting to run.
            with readerCv :
                readerCv.signal()
            writerCv.signal() 

    #* Todo: !clear, which clears the queue and deletes any downloaded videos.
    #* Todo: !pause, which pauses the audio the bot is playing.
    #* Todo: !next, skips to the next song and deletes the current song being played.
    #* Todo: !queue, list the items stored in queue.

    #* Todo: !join, bot will join the voice channel that the user is connect to.
    elif message.content == "!join" :
        # Validate author is in a voice channel
        if message.author.voice :
            try :
                print("before")
                await message.author.voice.channel.connect() #* Todo: This doesn't seem to do anything...
                print("after") #* Todo: The thread never reaches this point...
                log.debug("!join successfully joined the bot to the voice channel.") #* Todo: Add VC's name to the message.
            except Exception as err :
                log.error(err)

                return False
        else :
            log.error("!join failed, author is not in a voice channel.")
            await message.channel.send(_joinCommandNoActiveVoiceChannel)

            return False

        # Send a list of useful commands to the text channel.
        await message.channel.send(_helpPlayCommand)

    return True



if __name__ == "__main__" :
    log.basicConfig(
        datefmt="%Y-%m-%d %H:%M:%S", 
        filename='Groovester.log', 
        format='%(asctime)s;%(levelname)s;%(message)s', 
        level=log.DEBUG
    )

    setupFs()

    # Retrieve bot's API token from a .env file within the file system.
    load_dotenv()
    try : 
        log.debug("Attempting to start Groovester!")
        client.run(os.getenv("botToken"))
    except Exception as err :
        print
        log.error("An error occurred while starting the bot!")
        print(err)