import discord
import logging
import os
import asyncio
import yt_dlp as youtube_dl
from datetime import datetime
from dotenv import load_dotenv
from commands import handle_play_command, handle_stop_command, handle_pause_command, handle_resume_command, handle_commands_command
import traceback

# Initialize logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='discord_bot.log',
                    filemode='w')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('/home/skrody/Discord/Apps/.env')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Configure YouTube download options and FFMPEG options
yt_dl_options = {"format": "bestaudio/best"}
ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                  'options': '-vn -filter:a "volume=1.0"'}

# Discord client with intents
intents = discord.Intents.default()
intents.message_content = True  # Enable intents for message content
client = discord.Client(intents=intents)

# Log file for URL history
url_log_file = 'url_log.txt'


def setup_bot():
    @client.event
    async def on_ready():
        logger.info(
            f'{client.user} has successfully logged in and is ready to jam!')
        client.loop.create_task(monitor_sound(client))

    @client.event
    async def on_message(message):
        if message.content.startswith("!play"):
            await handle_play_command(message)
        elif message.content.startswith("!stop"):
            await handle_stop_command(message)
        elif message.content.startswith("!pause"):
            await handle_pause_command(message)
        elif message.content.startswith("!resume"):
            await handle_resume_command(message)
        elif message.content.startswith("!commands"):
            await handle_commands_command(message)


async def handle_play_command(message):
    parts = message.content.split()
    if len(parts) < 2:
        await message.channel.send("Please provide a URL.")
        return

    url = parts[1]
    if not message.author.voice:
        await message.channel.send("You must be in a voice channel to use the play command.")
        return

    try:
        voice_channel = message.author.voice.channel
        voice_client = message.guild.voice_client
        if not voice_client:
            voice_client = await voice_channel.connect()
            logger.info(f"Connected to {voice_channel.name}")
        else:
            if voice_client.is_playing():
                voice_client.stop()
                logger.info("Stopped the currently playing stream.")

        logger.debug("Extracting information from URL...")
        data = await extract_audio_data(url)

        if 'url' not in data:
            await message.channel.send("Could not extract audio from the provided URL.")
            return

        song_url = data['url']
        logger.debug(f"Audio URL extracted: {song_url}")

        audio_source = discord.FFmpegOpusAudio(song_url, **ffmpeg_options)
        voice_client.play(audio_source, after=lambda e: logger.error(
            'Player error:', e) if e else logger.info("Done playing!"))
        await message.channel.send("Now playing your requested track!")

        # Log the current URL
        log_url(url)

    except Exception as e:
        logger.error(
            "An error occurred while attempting to play audio", exc_info=True)
        await message.channel.send(f"An error occurred: {str(e)}")


async def handle_stop_command(message):
    if message.guild.voice_client:
        await message.guild.voice_client.disconnect()
        await message.channel.send("Stopped playing and disconnected.")
        logger.info("Stopped and disconnected successfully.")
    else:
        await message.channel.send("The bot is not connected to a voice channel.")


async def extract_audio_data(url):
    loop = asyncio.get_event_loop()
    ytdl = youtube_dl.YoutubeDL(yt_dl_options)
    return await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))


def log_url(url):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(url_log_file, 'a') as f:
        f.write(f"{now} - {url}\n")
    manage_log_size()


def manage_log_size():
    with open(url_log_file, 'r') as f:
        lines = f.readlines()
    if len(lines) > 25:
        with open(url_log_file, 'w') as f:
            f.writelines(lines[-25:])


def get_last_url():
    try:
        with open(url_log_file, 'r') as f:
            lines = f.readlines()
            if lines:
                last_line = lines[-1]
                last_url = last_line.split(' - ')[1].strip()
                return last_url
    except Exception as e:
        logger.error(
            "Failed to read the last URL from log file", exc_info=True)
    return None


async def monitor_sound(client):
    while True:
        await asyncio.sleep(60)  # Check every minute
        for vc in client.voice_clients:
            if not vc.is_playing():
                logger.warning(
                    "Voice client is not playing. Restarting stream.")
                last_url = get_last_url()
                if last_url:
                    await handle_play_command(client.get_channel(vc.channel.id), last_url)
                else:
                    logger.error("No URL found to restart the stream.")


def run_bot():
    client.run(DISCORD_BOT_TOKEN)
