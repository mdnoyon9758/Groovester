""" LIBRARIES """

import discord
from discord.ext import commands,tasks
from dotenv import load_dotenv
import logging as log
import os

from src._logging_ import configureProjectLogging
from src.constants import ClientMessages, DebugMessages, ErrorMessages, InfoMessages
from src.Groovester import setupTmpDirectory, GroovesterEventHandler


""" GLOBAL VARIABLES """

# Create Discord client instance.
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
groovesterEventHandler = None


""" CLIENT EVENTS """

@client.event
async def on_ready() :

    log.info(InfoMessages._groovesterStartedSuccessfully)
    print(InfoMessages._groovesterStartedSuccessfully)

    return True

@client.event
async def on_message(message) : # Message procedure

    # Groovester won't respond to itself.
    if message.author == client.user :
        return True

    log.debug(
        f"Message received from {message.author}: {message.content}"
    )

    if message.content == "!help" :
        await message.channel.send(ClientMessages._helpPlayCommand)

    # !join, Groovester will connect to the voice channel that the user is connected to.
    elif message.content == "!join" :
        return await groovesterEventHandler.joinClientEvent(message)

    # !leave, Groovester will disconnect from the voice channel it is currently connected to.
    elif message.content == "!leave" :
        return await groovesterEventHandler.leaveClientEvent(message)

    # !play: Downloads video to local file system and enrolls song in queue.
    elif message.content.startswith("!play") :
        return await groovesterEventHandler.playClientEvent(message)

    #* Todo: !clear, which clears the queue and deletes any downloaded videos.
    elif message.content == "!clear" :
        pass

    #* Todo: !next, skips to the next song and deletes the current song being played.
    elif message.content == "!next" :
        pass
    
    #* Todo: !pause, which pauses the audio the bot is playing.
    elif message.content == "!pause" :
        pass

    #* Todo: !queue, list the items stored in queue.
    elif message.content == "!queue" :
        pass

    return True



if __name__ == "__main__" :

    groovesterEventHandler = GroovesterEventHandler()
    configureProjectLogging()
    setupTmpDirectory() # Setup temporary location to store downloaded YouTube videos.
    load_dotenv() # Retrieve Groovester's API token from a .env file within the file system.

    # Start Groovester.
    try : 
        log.debug(DebugMessages._clientRunAttempt)
        client.run(os.getenv("botToken"))
    except Exception as err :
        print
        log.error(f"{ErrorMessages._clientRunException} {err}")