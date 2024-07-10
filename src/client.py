""" LIBRARIES """

import discord
from discord.ext import commands,tasks
from dotenv import load_dotenv
import logging as log
import os

from src._logging_ import configureProjectLogging
from src.constants import ClientMessages, ErrorMessages
from src.Groovester import GroovesterEventHandler


""" GLOBAL VARIABLES """

absPathGroovester = ""
client = None
groovesterEventHandler = None


""" FUNCTIONS """

#* Todo: Pass system argument to identify if OS is Linux or Windows. Helps setup FS.
#* Todo: Create a thread that goes through and verifies the videos stored in /tmp are still there. Compare against list.
def setupTmpDirectory() :
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

    # prevent bot from responding to itself
    if message.author == client.user :
        return True

    log.debug(
        f"Message received from {message.author}: {message.content}"
    )

    if message.content == "!help" :
        await message.channel.send(_helpPlayCommand)
    
    # !play: Downloads video to local file system and enrolls song in queue.
    elif message.content.startswith("!play") :
        return await groovesterEventHandler.playClientEvent(message)

    #* Todo: !clear, which clears the queue and deletes any downloaded videos.
    #* Todo: !pause, which pauses the audio the bot is playing.
    #* Todo: !next, skips to the next song and deletes the current song being played.
    #* Todo: !queue, list the items stored in queue.

    # !join, Groovester will connect to the voice channel that the user is connected to.
    elif message.content == "!join" :
        return await groovesterEventHandler.joinClientEvent(message)

    # !leave, Groovester will disconnect from the voice channel it is currently connected to.
    elif message.content == "!leave" :
        return await groovesterEventHandler.leaveClientEvent(message)

    return True



if __name__ == "__main__" :

    # Create Discord client instance.
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    groovesterEventHandler = GroovesterEventHandler()
    configureProjectLogging()
    setupTmpDirectory() # Setup temporary location to store downloaded YouTube videos.
    load_dotenv() # Retrieve Groovester's API token from a .env file within the file system.

    # Start Groovester.
    try : 
        log.debug("Attempting to start Groovester!")
        client.run(os.getenv("botToken"))
    except Exception as err :
        print
        log.error("An error occurred while starting the bot!")
        print(err)