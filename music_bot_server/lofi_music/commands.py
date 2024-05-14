import discord
import logging
import yt_dlp as youtube_dl
from utils import log_url, get_last_url

yt_dl_options = {"format": "bestaudio/best"}
ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                  'options': '-vn -filter:a "volume=0.50"'}

logger = logging.getLogger(__name__)
current_url = None


async def handle_play_command(message):
    global current_url  # Declare as global to modify the variable
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

        # Connect to the voice channel if not already connected
        if not voice_client:
            voice_client = await voice_channel.connect()
            logger.info(f"Connected to {voice_channel.name}")
        else:
            # Stop the currently playing audio if any
            if voice_client.is_playing():
                voice_client.stop()
                logger.info(
                    "Stopped playing current stream to play new stream.")

        logger.debug("Extracting information from URL...")
        data = await extract_audio_data(url)

        if 'url' not in data:
            await message.channel.send("Could not extract audio from the provided URL.")
            return

        song_url = data['url']
        current_url = url  # Store the current URL
        log_url(url)  # Log the current URL
        logger.debug(f"Audio URL extracted: {song_url}")

        audio_source = discord.FFmpegOpusAudio(song_url, **ffmpeg_options)
        voice_client.play(audio_source, after=lambda e: logger.error(
            'Player error:', e) if e else logger.info("Done playing!"))
        await message.channel.send("Now playing your requested track!")
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


async def handle_pause_command(message):
    voice_client = message.guild.voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await message.channel.send("Playback paused.")
    else:
        await message.channel.send("No audio is playing.")


async def handle_resume_command(message):
    voice_client = message.guild.voice_client
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await message.channel.send("Playback resumed.")
    else:
        await message.channel.send("Audio is not paused.")


async def handle_commands_command(message):
    commands_description = """
    **!play [URL]** - Plays the audio from the URL.
    **!stop** - Stops the audio and disconnects the bot.
    **!pause** - Pauses the currently playing audio.
    **!resume** - Resumes paused audio.
    **!commands** - Lists all available commands.
    """
    await message.channel.send(commands_description)


async def extract_audio_data(url):
    loop = asyncio.get_event_loop()
    ytdl = youtube_dl.YoutubeDL(yt_dl_options)
    return await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
