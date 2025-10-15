import logging, os, random, glob
from logging.handlers import RotatingFileHandler


api_id = int(os.getenv("API_ID", 24168862))
api_hash = os.getenv("API_HASH", "916a9424dd1e58ab7955001ccc0172b3")
bot_token = os.getenv("BOT_TOKEN", "8338434628:AAHHS87LJJ-pTrK9mZ8trvVLLoykqPYu6yA")
owner_id = int(os.getenv("OWNER_ID", 1679112664))
channel_id = int(os.getenv("CHANNEL_ID", -1002469453782))
sudo_users = list(map(int, os.getenv("SUDO_USERS", "0").split()))
mongo_url = os.getenv("MONGO_URL", "mongodb+srv://AutoRename3:AutoRename3@autorename3.5kqtqks.mongodb.net/?retryWrites=true&w=majority")
mongodb_url = os.getenv("MONGODB_URL", "mongodb+srv://AutoRename3:AutoRename3@autorename3.5kqtqks.mongodb.net/?retryWrites=true&w=majority")

db_name = os.getenv("DB_NAME", "EraApi")
api_key = os.getenv("API_KEY", "EraApi")

cookies_files = glob.glob("cookies/*")
cookies_path = os.getenv("COOKIES_PATH") or (cookies_files[0] if cookies_files else None)
download_dir = os.getenv("DOWNLOAD_DIR", "downloads")

# Bot settings - load from cache or env
direct_download_enabled = os.getenv("DIRECT_DOWNLOAD_ENABLED", "true").lower() == "true"
max_background_tasks = int(os.getenv("MAX_BACKGROUND_TASKS", 5))



sudoers = set()
for user in sudo_users:
    if user not in sudoers:
        sudoers.add(user)

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

