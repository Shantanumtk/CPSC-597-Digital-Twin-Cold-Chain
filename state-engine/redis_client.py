"""
Redis Client - Manages asset state cache
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict

import redis

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Key prefixes
ASSET_STATE_PREFIX = "asset:state:"
ALERT_ACTIVE_PREFIX = "alert:active:"
STATS_KEY = "stats:dashboard"


class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
        logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
    
    def ping(self) -> bool:
        """Check Redis connection"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    # -------------------------------------------------------------------------
    # Asset State Operations
    # -------------------------------------------------------------------------
    
    def set_asset_state(self, asset_id: str, state_data: dict) -> bool:
        """Store current state for an asset"""
        try:
            key = f"{ASSET_STATE_PREFIX}{asset_id}"
            state_data["updated_at"] = datetime.utcnow().isoformat()
            self.client.set(key, json.dumps(state_data))
            
            # Add to asset index
            self.client.sadd("assets:index", asset_id)
            
            # Update state counters
            self._update_state_counter(state_data.get("state", "UNKNOWN"))
            
            return True
        except Exception as e:
            logger.error(f"Failed to set asset state: {e}")
            return False
    
    def get_asset_state(self, asset_id: str) -> Optional[dict]:
        """Get current state for an asset"""
        try:
            key = f"{ASSET_STATE_PREFIX}{asset_id}"
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get asset state: {e}")
            return None
    
    def get_all_assets(self) -> List[dict]:
        """Get all asset states"""
        try:
            asset_ids = self.client.smembers("assets:index")
            assets = []
            for asset_id in asset_ids:
                state = self.get_asset_state(asset_id)
                if state:
                    state["asset_id"] = asset_id
                    assets.append(state)
            return assets
        except Exception as e:
            logger.error(f"Failed to get all assets: {e}")
            return []
    
    def get_assets_by_state(self, state: str) -> List[dict]:
        """Get all assets with a specific state"""
        assets = self.get_all_assets()
        return [a for a in assets if a.get("state") == state]
    
    # -------------------------------------------------------------------------
    # Alert Operations
    # -------------------------------------------------------------------------
    
    def set_active_alert(self, asset_id: str, alert_data: dict, ttl: int = 3600) -> bool:
        """Store active alert with TTL"""
        try:
            key = f"{ALERT_ACTIVE_PREFIX}{asset_id}"
            alert_data["created_at"] = datetime.utcnow().isoformat()
            self.client.setex(key, ttl, json.dumps(alert_data))
            self.client.sadd("alerts:active:index", asset_id)
            return True
        except Exception as e:
            logger.error(f"Failed to set alert: {e}")
            return False
    
    def clear_alert(self, asset_id: str) -> bool:
        """Clear active alert for asset"""
        try:
            key = f"{ALERT_ACTIVE_PREFIX}{asset_id}"
            self.client.delete(key)
            self.client.srem("alerts:active:index", asset_id)
            return True
        except Exception as e:
            logger.error(f"Failed to clear alert: {e}")
            return False
    
    def get_active_alerts(self) -> List[dict]:
        """Get all active alerts"""
        try:
            alert_ids = self.client.smembers("alerts:active:index")
            alerts = []
            for asset_id in alert_ids:
                key = f"{ALERT_ACTIVE_PREFIX}{asset_id}"
                data = self.client.get(key)
                if data:
                    alert = json.loads(data)
                    alert["asset_id"] = asset_id
                    alerts.append(alert)
                else:
                    # Alert expired, remove from index
                    self.client.srem("alerts:active:index", asset_id)
            return alerts
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []
    
    # -------------------------------------------------------------------------
    # Statistics Operations
    # -------------------------------------------------------------------------
    
    def _update_state_counter(self, state: str):
        """Update state counter for statistics"""
        try:
            self.client.hincrby("stats:state_counts", state, 1)
        except Exception:
            pass
    
    def get_stats(self) -> dict:
        """Get dashboard statistics"""
        try:
            assets = self.get_all_assets()
            active_alerts = self.get_active_alerts()
            
            state_counts = {"NORMAL": 0, "WARNING": 0, "CRITICAL": 0}
            asset_types = {"refrigerated_truck": 0, "cold_room": 0}
            
            for asset in assets:
                state = asset.get("state", "UNKNOWN")
                if state in state_counts:
                    state_counts[state] += 1
                
                asset_type = asset.get("asset_type", "unknown")
                if asset_type in asset_types:
                    asset_types[asset_type] += 1
            
            return {
                "total_assets": len(assets),
                "state_counts": state_counts,
                "asset_types": asset_types,
                "active_alerts": len(active_alerts),
                "updated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}