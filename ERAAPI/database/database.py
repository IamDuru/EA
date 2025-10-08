from . import audiodb, videodb

async def is_served_audio(id: str) -> bool:
    doc = await audiodb.find_one({"id": id})
    return doc is not None


async def add_served_audio(id: str, link: str) -> bool:
    if await is_served_audio(id):
        return False

    await audiodb.insert_one({"id": id, "link": link})
    return True


async def get_served_audio(id: str) -> dict | None:
    return await audiodb.find_one({"id": id})


async def delete_served_audio(id: str) -> bool:
    result = await audiodb.delete_one({"id": id})
    return result.deleted_count > 0

# --- video -----
async def is_served_video(id: str) -> bool:
    doc = await videodb.find_one({"id": id})
    return doc is not None


async def add_served_video(id: str, link: str) -> bool:
    if await is_served_video(id):
        return False

    await videodb.insert_one({"id": id, "link": link})
    return True


async def get_served_video(id: str) -> dict | None:
    return await videodb.find_one({"id": id})


async def delete_served_video(id: str) -> bool:
    result = await videodb.delete_one({"id": id})
    return result.deleted_count > 0
