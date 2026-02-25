"""
MongoDB MCP Tools — Historical telemetry + Digital Twin state queries.
Connects to MongoDB on the private EC2 instance within the VPC.
"""

import os
import json
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "coldchain")

_client = None
_db = None


def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI)
        _db = _client[MONGO_DB]
    return _db


def query_telemetry(asset_id: str, hours: int = 2, limit: int = 50) -> str:
    """Query historical telemetry readings for an asset.

    Args:
        asset_id: The asset identifier (e.g. 'truck-01', 'cold-room-site-1-room-1')
        hours: How many hours of history to look back (default 2)
        limit: Maximum number of readings to return (default 50)

    Returns:
        JSON string with telemetry readings sorted by timestamp descending.
    """
    db = get_db()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    cursor = db.telemetry.find(
        {"asset_id": asset_id, "timestamp": {"$gte": since}},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit)

    results = []
    for doc in cursor:
        if "timestamp" in doc and isinstance(doc["timestamp"], datetime):
            doc["timestamp"] = doc["timestamp"].isoformat()
        results.append(doc)

    if not results:
        return json.dumps({"message": f"No telemetry found for {asset_id} in last {hours}h"})

    return json.dumps(results, default=str)


def get_twin_state(asset_id: str) -> str:
    """Get the current digital twin state for an asset from the twin_states collection.

    Args:
        asset_id: The asset identifier (e.g. 'truck-01')

    Returns:
        JSON string with the current twin state including SLA metrics.
    """
    db = get_db()
    state = db.twin_states.find_one(
        {"asset_id": asset_id},
        {"_id": 0}
    )

    if not state:
        return json.dumps({"message": f"No twin state found for {asset_id}"})

    if "last_updated" in state and isinstance(state["last_updated"], datetime):
        state["last_updated"] = state["last_updated"].isoformat()

    return json.dumps(state, default=str)


def get_sla_metrics(asset_id: str) -> str:
    """Get SLA compliance metrics for an asset — time-in-band percentage,
    breach count, and compliance score.

    Args:
        asset_id: The asset identifier

    Returns:
        JSON string with SLA metrics.
    """
    db = get_db()
    state = db.twin_states.find_one(
        {"asset_id": asset_id},
        {"_id": 0, "asset_id": 1, "sla": 1, "breach_count": 1,
         "time_in_band_pct": 1, "compliance_score": 1, "state": 1}
    )

    if not state:
        return json.dumps({"message": f"No SLA metrics found for {asset_id}"})

    return json.dumps(state, default=str)


def find_breaches(asset_id: str = None, hours: int = 24, limit: int = 20) -> str:
    """Find temperature breach events.

    Args:
        asset_id: Optional — filter by specific asset. If None, returns all breaches.
        hours: How many hours to look back (default 24)
        limit: Maximum results (default 20)

    Returns:
        JSON string with breach events.
    """
    db = get_db()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = {"timestamp": {"$gte": since}, "event_type": {"$regex": "breach|BREACH|alert|ALERT", "$options": "i"}}
    if asset_id:
        query["asset_id"] = asset_id

    cursor = db.alerts.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit)

    results = []
    for doc in cursor:
        if "timestamp" in doc and isinstance(doc["timestamp"], datetime):
            doc["timestamp"] = doc["timestamp"].isoformat()
        results.append(doc)

    if not results:
        # Fallback: check telemetry for temperature values outside bounds
        temp_query = {"timestamp": {"$gte": since}}
        if asset_id:
            temp_query["asset_id"] = asset_id
        temp_query["$or"] = [
            {"temperature": {"$gt": -2}},  # Above upper threshold
            {"temperature": {"$lt": -25}}  # Below lower threshold
        ]
        cursor = db.telemetry.find(temp_query, {"_id": 0}).sort("timestamp", -1).limit(limit)
        results = []
        for doc in cursor:
            if "timestamp" in doc and isinstance(doc["timestamp"], datetime):
                doc["timestamp"] = doc["timestamp"].isoformat()
            results.append(doc)

    if not results:
        scope = f"for {asset_id}" if asset_id else "across all assets"
        return json.dumps({"message": f"No breaches found {scope} in last {hours}h"})

    return json.dumps(results, default=str)


def compare_assets(asset_ids: list[str] = None) -> str:
    """Compare digital twin states across multiple assets side-by-side.

    Args:
        asset_ids: Optional list of asset IDs. If None, returns all assets.

    Returns:
        JSON string with comparison data.
    """
    db = get_db()

    query = {}
    if asset_ids:
        query["asset_id"] = {"$in": asset_ids}

    cursor = db.twin_states.find(query, {"_id": 0}).sort("asset_id", 1)

    results = []
    for doc in cursor:
        if "last_updated" in doc and isinstance(doc["last_updated"], datetime):
            doc["last_updated"] = doc["last_updated"].isoformat()
        results.append(doc)

    if not results:
        return json.dumps({"message": "No twin states found"})

    return json.dumps(results, default=str)


def list_all_assets() -> str:
    """List all known assets in the digital twin system.

    Returns:
        JSON string with list of asset IDs and their current states.
    """
    db = get_db()
    cursor = db.twin_states.find({}, {"_id": 0, "asset_id": 1, "state": 1, "asset_type": 1}).sort("asset_id", 1)

    results = list(cursor)
    if not results:
        return json.dumps({"message": "No assets found in the system"})

    return json.dumps(results, default=str)
