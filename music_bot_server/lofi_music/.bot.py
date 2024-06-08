import logging
import os
import asyncio
import yt_dlp as youtube_dl
from datetime import datetime
from dotenv import load_dotenv
from discord.ext import commands
from commands import handle_play_command
import discord

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

if not DISCORD_BOT_TOKEN:
    raise ValueError("No DISCORD_BOT_TOKEN found in environment variables")

# Configure YouTube download options
yt_dl_options = {"format": "bestaudio/best"}

# Log file for URL history
url_log_file = 'url_log.txt'

intents = discord.Intents.default()
intents.message_content = True

# Create a bot instance
bot = commands.Bot(command_prefix='!', intents=intents)


def setup_bot():
    @bot.event
    async def on_ready():
        logger.info(
            f'{bot.user} has successfully logged in and is ready to jam!')
        bot.loop.create_task(monitor_sound(bot))


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
        logger.error(f"Failed to read the last URL from log file: {
                     e}", exc_info=True)
    return None


async def monitor_sound(bot):
    while True:
        await asyncio.sleep(60)  # Check every minute
        for vc in bot.voice_clients:
            if not vc.is_playing():
                logger.warning(
                    "Voice client is not playing. Restarting stream.")
                last_url = get_last_url()
                if last_url:
                    await handle_play_command(bot.get_channel(vc.channel.id), last_url)
                else:
                    logger.error("No URL found to restart the stream.")


def run_bot():
    bot.run(DISCORD_BOT_TOKEN)
