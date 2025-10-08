from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from .. import console

# Connect to Common MongoDB for audio
audio_client = AsyncIOMotorClient(console.main_mongo_url)[console.db_name]
audiodb = audio_client['audiodb']

# Connect to Common MongoDB for video
video_client = AsyncIOMotorClient(console.main_mongo_url)[console.db_name]
videodb = video_client['videodb']

# Connect to Common MongoDB for users
api_client = MongoClient(console.main_mongo_url)[console.db_name]
api_db = api_client
users_col = api_db['users']

# Connect to Common MongoDB for main
main_client = AsyncIOMotorClient(console.main_mongo_url)[console.db_name]
main_db = main_client

# Use separate audio and video collections for audio_db and video_db
audio_db = audiodb
video_db = videodb
