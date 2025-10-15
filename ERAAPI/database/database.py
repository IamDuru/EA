from . import audiodb, videodb

def is_served_audio(id: str) -> bool:
    doc = audiodb.find_one({"id": id})
    return doc is not None


def add_served_audio(id: str, link: str) -> bool:
    if is_served_audio(id):
        return False

    audiodb.insert_one({"id": id, "link": link})
    return True


def get_served_audio(id: str) -> dict | None:
    return audiodb.find_one({"id": id})


def delete_served_audio(id: str) -> bool:
    result = audiodb.delete_one({"id": id})
    return result.deleted_count > 0

# --- video -----
def is_served_video(id: str) -> bool:
    doc = videodb.find_one({"id": id})
    return doc is not None


def add_served_video(id: str, link: str) -> bool:
    if is_served_video(id):
        return False

    videodb.insert_one({"id": id, "link": link})
    return True


def get_served_video(id: str) -> dict | None:
    return videodb.find_one({"id": id})


def delete_served_video(id: str) -> bool:
    result = videodb.delete_one({"id": id})
    return result.deleted_count > 0
