from datetime import datetime
from fastapi import HTTPException
from . import apidb
from .. import console

def check_api_key(key: str):
    if key == console.api_key:
        return True
    user = apidb.find_one({"api_key": key})
    if not user:
        raise HTTPException(403, detail="invalid_api_key")

    # Auto-delete expired keys
    if user.get("expires_at") and user["expires_at"] < datetime.utcnow():
        apidb.delete_one({"api_key": key})
        raise HTTPException(403, detail="api_key_expired")

    ok, info = consume_request(key)
    if not ok:
        code = 429 if info in ("daily_quota_exceeded", "monthly_quota_exceeded") else 403
        raise HTTPException(code, detail=str(info))
    return True


def consume_request(api_key: str):
    user = apidb.find_one({"api_key": api_key})
    if not user:
        return False, "invalid_api_key"
    if user.get("daily_limit") == -1:
        return True, "ok"

    today = datetime.utcnow().strftime("%Y-%m-%d")
    usage = user.get("usage", {})
    today_usage = usage.get(today, 0)
    daily_limit = user.get("daily_limit", 1000)

    if today_usage >= daily_limit:
        return False, "daily_quota_exceeded"

    month = today[:7]
    monthly_usage = user.get("monthly_usage", {})
    month_usage = monthly_usage.get(month, 0)
    monthly_limit = user.get("monthly_limit", 20000)

    if month_usage >= monthly_limit:
        return False, "monthly_quota_exceeded"

    usage[today] = today_usage + 1
    monthly_usage[month] = month_usage + 1
    apidb.update_one({"api_key": api_key}, {"$set": {"usage": usage, "monthly_usage": monthly_usage}})
    return True, "ok"

