import discord
import logging
import yt_dlp as youtube_dl
from utils import log_url
import asyncio
import time
from discord.ext import commands as ext_commands
import subprocess
import re
from config import ffmpeg_options


yt_dl_options = {
    "format": "bestaudio/best",
    "noplaylist": True,  # Disable playlist extraction
    "quiet": False,       # Disable verbose logging
    "no_warnings": False,  # Disable warnings
    "default_search": "auto",  # Search automatically if URL is incomplete
}


logger = logging.getLogger(__name__)
current_url = None

# Set up Discord intents
intents = discord.Intents.default()
intents.message_content = True  # Enable intents for message content

# Create a bot instance with intents
bot = ext_commands.Bot(command_prefix='!', intents=intents)


@bot.command(name="play")
async def play(ctx, url=None):
    await handle_play_command(ctx, url)


async def handle_play_command(ctx, url=None):
    if url is None:
        parts = ctx.message.content.split()
        if len(parts) < 2:
            await ctx.send("Please provide a URL.")
            return
        url = parts[1]

    if not ctx.author.voice:
        await ctx.send(
            "You must be in a voice channel to use the play command."
        )
        return

    try:
        voice_channel = ctx.author.voice.channel
        voice_client = ctx.guild.voice_client
        if not voice_client:
            voice_client = await voice_channel.connect()
            logger.info(f"Connected to {voice_channel.name}")
        else:
            if voice_client.is_playing():
                voice_client.stop()
                logger.info("Stopped the currently playing stream.")

        logger.debug("Extracting information from URL...")
        start_time = time.time()
        data = await extract_audio_data(url)
        extract_time = time.time() - start_time
        logger.debug(f"Time taken to extract URL: {extract_time} seconds")

        if not isinstance(data, dict) or 'url' not in data:
            await ctx.send("Could not extract audio from the provided URL.")
            return

        song_url = data['url']
        logger.debug(f"Audio URL extracted: {song_url}")

        if not isinstance(song_url, str):
            raise ValueError("Extracted song URL is not a valid string")

        # Ensure bitrate is only passed once
        audio_options = {k: v for k,
                         v in ffmpeg_options.items() if k != 'bitrate'}
        audio_source = discord.FFmpegOpusAudio(
            song_url, bitrate=ffmpeg_options.get(
                'bitrate', 128
            ), **audio_options)
        voice_client.play(audio_source, after=lambda e: logger.error(
            'Player error: %s', e) if e else logger.info("Done playing!"))
        await ctx.send("Now playing your requested track!")

        # Log the current URL
        log_url(url)

    except Exception as e:
        logger.error(
            "An error occurred while attempting to play audio", exc_info=True)
        await ctx.send(f"An error occurred: {str(e)}")


@bot.command(name="stop")
async def stop(ctx):
    await handle_stop_command(ctx)


async def handle_stop_command(ctx):
    if ctx.guild.voice_client:
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Stopped playing and disconnected.")
        logger.info("Stopped and disconnected successfully.")
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command(name="pause")
async def pause(ctx):
    await handle_pause_command(ctx)


async def handle_pause_command(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await ctx.send("Playback paused.")
    else:
        await ctx.send("No audio is playing.")


@bot.command(name="resume")
async def resume(ctx):
    await handle_resume_command(ctx)


async def handle_resume_command(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await ctx.send("Playback resumed.")
    else:
        await ctx.send("Audio is not paused.")


@bot.command(name="commands")
async def commands_list(ctx):  # Renamed to avoid conflict with module name
    await handle_commands_command(ctx)


async def handle_commands_command(ctx):
    commands_description = """
    **!play [URL]** - Plays the audio from the URL.
    **!stop** - Stops the audio and disconnects the bot.
    **!pause** - Pauses the currently playing audio.
    **!resume** - Resumes paused audio.
    **!commands** - Lists all available commands.
    **!ping [host]** - Checks network latency to the specified host.
    """
    await ctx.send(commands_description)


@bot.command(name="ping")
async def ping(ctx, host='google.com'):
    result = await handle_ping_command(host)
    await ctx.send(result)


async def handle_ping_command(host):
    def ping_host(host):
        process = subprocess.Popen(
            ['ping', '-c', '4', host],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            return f"Error pinging {host}: {stderr.decode('utf-8')}"
        stdout = stdout.decode('utf-8')
        match = re.search(r'avg = ([\d\.]+) ms', stdout)
        if match:
            avg_latency = match.group(1)
            return f"Average latency to {host} is {avg_latency} ms"
        else:
            return f"Could not parse ping output: {stdout}"

    return ping_host(host)


async def extract_audio_data(url):
    loop = asyncio.get_event_loop()
    ytdl = youtube_dl.YoutubeDL(yt_dl_options)
    return await loop.run_in_executor(
        None, lambda: ytdl.extract_info(
            url, download=False
        )
    )

# Registering commands with bot instance


def setup_commands(bot_instance):
    bot_instance.add_command(play)
    bot_instance.add_command(stop)
    bot_instance.add_command(pause)
    bot_instance.add_command(resume)
    bot_instance.add_command(commands_list)
    bot_instance.add_command(ping)
