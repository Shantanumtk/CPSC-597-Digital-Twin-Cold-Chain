"""
MQTT MCP Tools — Subscribe to live sensor data and publish commands.
Connects to Mosquitto broker running on the same EC2 instance (localhost).
"""

import os
import json
import time
import threading
import paho.mqtt.client as mqtt

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

# In-memory buffer for recent messages
_message_buffer = {}
_buffer_lock = threading.Lock()
_subscriber_thread = None
_client = None


def _on_message(client, userdata, msg):
    """Callback: store latest message per topic."""
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = {"raw": msg.payload.decode("utf-8", errors="replace")}

    with _buffer_lock:
        _message_buffer[msg.topic] = {
            "topic": msg.topic,
            "payload": payload,
            "received_at": time.time(),
        }


def _ensure_subscriber():
    """Start background MQTT subscriber if not running."""
    global _subscriber_thread, _client

    if _client is not None:
        return

    _client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    _client.on_message = _on_message

    try:
        _client.connect(MQTT_BROKER, MQTT_PORT, 60)
        # Subscribe to all cold chain topics
        _client.subscribe("fleet/+/telemetry")
        _client.subscribe("warehouse/+/room/+/telemetry")
        _client.subscribe("alerts/#")

        _subscriber_thread = threading.Thread(target=_client.loop_forever, daemon=True)
        _subscriber_thread.start()
    except Exception as e:
        _client = None
        raise RuntimeError(f"Failed to connect to MQTT broker: {e}")


def get_live_reading(asset_id: str) -> str:
    """Get the most recent MQTT reading for an asset.

    Args:
        asset_id: The asset identifier (e.g. 'truck-01', 'cold-room-site-1-room-1')

    Returns:
        JSON string with the latest MQTT message for the asset.
    """
    try:
        _ensure_subscriber()
    except RuntimeError as e:
        return json.dumps({"error": str(e)})

    # Give a moment for messages to arrive if just started
    time.sleep(0.5)

    with _buffer_lock:
        # Search for matching topic
        for topic, data in _message_buffer.items():
            if asset_id in topic or asset_id.replace("-", "_") in topic:
                age = time.time() - data["received_at"]
                return json.dumps({
                    "asset_id": asset_id,
                    "source": "mqtt_live",
                    "age_seconds": round(age, 1),
                    **data["payload"]
                }, default=str)

    return json.dumps({"message": f"No recent MQTT data for {asset_id}. Sensor may not be publishing."})


def list_active_sensors() -> str:
    """List all sensors that are currently publishing MQTT data.

    Returns:
        JSON string with active sensor topics and their last update time.
    """
    try:
        _ensure_subscriber()
    except RuntimeError as e:
        return json.dumps({"error": str(e)})

    time.sleep(1)  # Wait for messages

    with _buffer_lock:
        sensors = []
        now = time.time()
        for topic, data in sorted(_message_buffer.items()):
            age = now - data["received_at"]
            sensors.append({
                "topic": topic,
                "age_seconds": round(age, 1),
                "active": age < 30,  # Consider active if updated in last 30s
            })

    if not sensors:
        return json.dumps({"message": "No active MQTT sensors detected yet. Wait a few seconds."})

    return json.dumps({"active_sensors": sensors, "total": len(sensors)})
