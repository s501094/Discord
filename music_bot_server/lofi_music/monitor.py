import os
import asyncio
import logging
from utils import get_last_url
from commands import handle_play_command

logger = logging.getLogger(__name__)


async def monitor_sound(client):
    while True:
        for vc in client.voice_clients:
            if vc.is_playing():
                # Check if the bot is outputting sound
                if not vc.is_playing() or not vc.is_connected():
                    logger.info("No sound detected. Restarting service...")
                    await restart_service(vc.guild.id, client)
        await asyncio.sleep(30)  # Check every 30 seconds


async def restart_service(guild_id, client):
    global current_url
    # Restart the bot service
    os.system(f"sudo systemctl restart discordbot.service")

    # Wait for the bot to reconnect and resume playback
    await asyncio.sleep(10)  # Wait 10 seconds for the bot to restart
    guild = client.get_guild(guild_id)
    # Change to your specific channel name
    channel = discord.utils.get(guild.voice_channels, name='General')
    voice_client = await channel.connect()
    logger.info(f"Reconnected to {channel.name}")

    last_url = get_last_url()  # Read the last URL from the log
    if last_url:
        await handle_play_command(await guild.get_channel(channel.id).fetch_message(last_url))
