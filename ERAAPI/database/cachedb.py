from . import chachedb

async def get_task(key: str, default=None):
    try:
        doc = await chachedb.find_one({"_id": "settings"})
        return doc.get(key, default) if doc else default
    except:
        return default

async def set_task(key: str, value):
    try:
        await chachedb.update_one({"_id": "settings"}, {"$set": {key: value}}, upsert=True)
    except:
        pass

async def del_task(key: str):
    try:
        await chachedb.update_one({"_id": "settings"}, {"$unset": {key: ""}})
    except:
        pass