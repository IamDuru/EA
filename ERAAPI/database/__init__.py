from pymongo import MongoClient
from .. import console

# Connect to Common MongoDB for audio, video files (using synchronous client for simplicity)
mongodb = MongoClient(console.mongodb_url)[console.db_name]
audiodb = mongodb.audiodb
videodb = mongodb.videodb

# Connect to Common MongoDB for users
mongo = MongoClient(console.mongo_url)[console.db_name]
usersdb = mongo.users
chachedb = mongo.chache
apidb = mongo.apidb



from .database import *
from .apidb import *
from .cachedb import *
from .dowmp3 import *
from .dowmp4 import *
from .poxy import *
from .utils import *
from .ytdow import *