""" LIBRARIES """

import asyncio
import logging as log
import os
from threading import Thread

from discord import Client, DiscordException, Intents
from dotenv import load_dotenv

from src._logging_ import configureProjectLogging
from src.constants import ClientMessages, DebugMessages, ErrorMessages, InfoMessages
from src.Groovester import setupTmpDirectory, GroovesterEventHandler
from src.threads import playDownloadedSongViaDiscordAudio


# Create Discord client instance.
intents = Intents.default()
intents.message_content = True
client = Client(intents=intents)

GROOVESTER_EVENT_HANDLER = None


def runPlaySongsInDiscordAudioThread():
    asyncio.run(
        playDownloadedSongViaDiscordAudio(
            GROOVESTER_EVENT_HANDLER,
        )
    )


@client.event
async def on_ready():
    """Prints message when Groovester successfully starts and starts helper threads."""

    log.info("%s", InfoMessages._groovesterStartedSuccessfully)
    print(InfoMessages._groovesterStartedSuccessfully)

    # Start various helper threads.
    playSongsInDiscordAudioThread = Thread(
        target=runPlaySongsInDiscordAudioThread, args=()
    )
    try:
        playSongsInDiscordAudioThread.start()
    except Exception as err:
        log.error(err)

    return True


@client.event
async def on_message(message):  # Message procedure
    """Message procedure for the Discord client."""

    # Groovester won't respond to itself.
    if message.author == client.user:
        return True

    log.debug("Message received from %s: %s", message.author, message.content)
    GROOVESTER_EVENT_HANDLER.lastChannelCommandWasEntered = message.channel

    if message.content == "!help":
        await message.channel.send(ClientMessages._helpPlayCommand)

    # !join, Groovester will connect to the voice channel that the user is connected to.
    elif message.content == "!join":
        return await GROOVESTER_EVENT_HANDLER.joinClientEvent(message)

    # !leave, Groovester will disconnect from the voice channel it is currently connected to.
    elif message.content == "!leave":
        return await GROOVESTER_EVENT_HANDLER.leaveClientEvent(message)

    # !play: Downloads video to local file system and enrolls song in queue.
    elif message.content.startswith("!play"):
        return await GROOVESTER_EVENT_HANDLER.playClientEvent(message)

    elif message.content == "!stop":
        return await GROOVESTER_EVENT_HANDLER.stopClientEvent(message.channel)

    # * Todo: !clear, which clears the queue and deletes any downloaded videos.
    elif message.content == "!clear":
        pass

    # * Todo: !next, skips to the next song and deletes the current song being played.
    elif message.content == "!next":
        pass

    # * Todo: !pause, which pauses the audio the bot is playing.
    elif message.content == "!pause":
        pass

    # * Todo: !queue, list the items stored in queue.
    elif message.content == "!queue":
        pass

    return True


if __name__ == "__main__":

    GROOVESTER_EVENT_HANDLER = GroovesterEventHandler()
    configureProjectLogging()
    setupTmpDirectory()  # Setup temporary location to store downloaded YouTube videos.
    load_dotenv()  # Retrieve Groovester's API token from a .env file within the file system.

    # Start the Groovester client thread.
    try:
        log.debug("%s", DebugMessages._clientRunAttempt)
        client.run(os.getenv("botToken"))
    except DiscordException as err:
        log.error("%s %s", ErrorMessages._clientRunException, err)
