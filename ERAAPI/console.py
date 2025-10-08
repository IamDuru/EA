import logging, os
from logging.handlers import RotatingFileHandler



api_id = int(os.getenv("API_ID", 0))
api_hash = os.getenv("API_HASH", "")
bot_token = os.getenv("BOT_TOKEN", "")
owner_id = int(os.getenv("OWNER_ID", 7616808278))

audio_channel_id = int(os.getenv("AUDIO_CHANNEL_ID", 0))
video_channel_id = int(os.getenv("VIDEO_CHANNEL_ID", 0))
channel_id = int(os.getenv("CHANNEL_ID", 0))

# space separated IDs → list of ints
sudo_users = list(map(int, os.getenv("SUDO_USERS", "0").split()))

main_mongo_url = os.getenv("MAIN_MONGO_URL", "")
db_name = os.getenv("DB_NAME", "eravibesdb")
api_key = os.getenv("API_KEY", "")




logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s:\n%(message)s\n",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler(
            "logs.txt", maxBytes=5000000, backupCount=10
        ),
        logging.StreamHandler(),
    ],
)

logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

def logs(name: str) -> logging.Logger:
    return logging.getLogger(name)

