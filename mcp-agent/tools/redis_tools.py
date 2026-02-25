"""
Redis MCP Tools — Real-time digital twin state from Redis.
Connects to Redis running on EKS.
"""

import os
import json
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

_redis = None


def get_redis():
    global _redis
    if _redis is None:
        _redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    return _redis


def get_live_state(asset_id: str) -> str:
    """Get the real-time state of an asset from Redis.

    Args:
        asset_id: The asset identifier (e.g. 'truck-01')

    Returns:
        JSON string with current state from Redis (temperature, door, compressor, etc.)
    """
    r = get_redis()
    key = f"twin:{asset_id}"
    data = r.hgetall(key)

    if not data:
        return json.dumps({"message": f"No live state found in Redis for {asset_id}"})

    return json.dumps({"asset_id": asset_id, "source": "redis_live", **data})


def get_all_live_states() -> str:
    """Get real-time state for ALL assets from Redis.

    Returns:
        JSON string with all asset states.
    """
    r = get_redis()
    keys = r.keys("twin:*")

    results = []
    for key in sorted(keys):
        asset_id = key.replace("twin:", "")
        data = r.hgetall(key)
        if data:
            results.append({"asset_id": asset_id, **data})

    if not results:
        return json.dumps({"message": "No live states found in Redis"})

    return json.dumps(results)


def get_alerts_from_redis(asset_id: str = None) -> str:
    """Get recent alerts stored in Redis.

    Args:
        asset_id: Optional — filter by asset. If None, returns all recent alerts.

    Returns:
        JSON string with recent alert data.
    """
    r = get_redis()

    if asset_id:
        key = f"alerts:{asset_id}"
        data = r.lrange(key, 0, 19)  # Last 20 alerts
    else:
        # Get alerts for all assets
        keys = r.keys("alerts:*")
        data = []
        for key in sorted(keys):
            items = r.lrange(key, 0, 9)
            data.extend(items)

    if not data:
        scope = f"for {asset_id}" if asset_id else ""
        return json.dumps({"message": f"No recent alerts found {scope} in Redis"})

    parsed = []
    for item in data:
        try:
            parsed.append(json.loads(item))
        except (json.JSONDecodeError, TypeError):
            parsed.append({"raw": str(item)})

    return json.dumps(parsed)
