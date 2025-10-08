import logging
from logging.handlers import RotatingFileHandler



api_id = 12380656
api_hash = "d927c13beaaf5110f25c505b7c071273"
bot_token = "your_bot_token"
owener_id = 1679112664
audio_channel_id = -1001942636044
video_channel_id = -1001942636044
channel_id = -1003015175237
sudo_users = [7615306685]

main_mongo_url = "your_mongo_db_url"
db_name = "eravibesdb"
api_key = "your_api_key_here"



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