from Bot2 import setup_bot, run_bot
import logging
import os
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='discord_bot.log',
                    filemode='w')
logger = logging.getLogger(__name__)

# Load environment variables
env_loaded = load_dotenv('/home/skrody/Discord/Apps/.env')
if not env_loaded:
    raise ValueError("Failed to load .env file")

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not DISCORD_BOT_TOKEN:
    raise ValueError("No DISCORD_BOT_TOKEN found in environment variables")


if __name__ == '__main__':
    setup_bot()
    run_bot(DISCORD_BOT_TOKEN)
