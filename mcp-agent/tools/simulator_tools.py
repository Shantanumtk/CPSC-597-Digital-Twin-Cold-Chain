"""
Simulator Controller Tools — Manipulate docker-compose sensor environment
via natural language. Runs on the same EC2 as the sensor simulator.
"""

import os
import json
import subprocess
import time

# Path to the sensor simulator docker-compose directory on MQTT EC2
SIMULATOR_DIR = os.getenv("SIMULATOR_DIR", "/home/ec2-user/cold-chain-simulator")


def _run_cmd(cmd: str, cwd: str = None) -> dict:
    """Run a shell command and return result."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=30, cwd=cwd or SIMULATOR_DIR
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_simulator_status() -> str:
    """Get the current status of the sensor simulator containers.

    Returns:
        JSON string with container status information.
    """
    result = _run_cmd("docker-compose ps --format json 2>/dev/null || docker compose ps --format json")

    if not result["success"]:
        # Fallback to plain format
        result = _run_cmd("docker-compose ps 2>/dev/null || docker compose ps")

    return json.dumps(result)


def get_simulator_env() -> str:
    """Get current environment variables of the sensor simulator.

    Returns:
        JSON showing current simulator configuration (NUM_TRUCKS, NUM_ROOMS, etc.)
    """
    result = _run_cmd("docker-compose exec -T sensor-simulator env 2>/dev/null || docker compose exec -T sensor-simulator env")

    if result["success"]:
        # Parse relevant env vars
        env_vars = {}
        for line in result["stdout"].split("\n"):
            if any(k in line for k in ["NUM_", "PUBLISH_", "MQTT_", "BREACH_", "DOOR_", "COMPRESSOR_"]):
                key, _, value = line.partition("=")
                env_vars[key] = value
        return json.dumps({"simulator_config": env_vars})

    return json.dumps(result)


def restart_simulator(env_overrides: dict = None) -> str:
    """Restart the sensor simulator with optional environment variable overrides.

    Args:
        env_overrides: Dict of environment variables to override.
                       Example: {"NUM_TRUCKS": "20", "PUBLISH_INTERVAL": "0.5"}

    Returns:
        JSON string with restart result.
    """
    if env_overrides:
        # Build env string for docker-compose
        env_str = " ".join(f"{k}={v}" for k, v in env_overrides.items())
        cmd = f"{env_str} docker-compose up -d --force-recreate sensor-simulator 2>/dev/null || {env_str} docker compose up -d --force-recreate sensor-simulator"
    else:
        cmd = "docker-compose restart sensor-simulator 2>/dev/null || docker compose restart sensor-simulator"

    result = _run_cmd(cmd)
    return json.dumps({"action": "restart_simulator", "env_overrides": env_overrides, **result})


def trigger_door_event(asset_id: str, duration_seconds: int = 60) -> str:
    """Simulate a door-open event on a specific asset by publishing an MQTT command.

    Args:
        asset_id: The truck or room to trigger door open on (e.g. 'truck-02')
        duration_seconds: How long the door stays open in seconds (default 60)

    Returns:
        JSON string confirming the door event was triggered.
    """
    topic = f"commands/{asset_id}/door"
    payload = json.dumps({"action": "open", "duration_seconds": duration_seconds})

    cmd = f'mosquitto_pub -h localhost -t "{topic}" -m \'{payload}\''
    result = _run_cmd(cmd, cwd="/tmp")

    return json.dumps({
        "action": "door_open",
        "asset_id": asset_id,
        "duration_seconds": duration_seconds,
        "topic": topic,
        **result
    })


def trigger_compressor_failure(asset_id: str, duration_seconds: int = 300) -> str:
    """Simulate a compressor failure on a specific asset.

    Args:
        asset_id: The asset to fail compressor on (e.g. 'truck-05')
        duration_seconds: How long the compressor stays off (default 300 = 5 min)

    Returns:
        JSON string confirming the compressor failure was triggered.
    """
    topic = f"commands/{asset_id}/compressor"
    payload = json.dumps({"action": "fail", "duration_seconds": duration_seconds})

    cmd = f'mosquitto_pub -h localhost -t "{topic}" -m \'{payload}\''
    result = _run_cmd(cmd, cwd="/tmp")

    return json.dumps({
        "action": "compressor_failure",
        "asset_id": asset_id,
        "duration_seconds": duration_seconds,
        **result
    })


def trigger_power_outage(site_id: str = "site-1", duration_seconds: int = 600) -> str:
    """Simulate a power outage at a warehouse site.

    Args:
        site_id: The site to simulate power outage (default 'site-1')
        duration_seconds: Duration of outage in seconds (default 600 = 10 min)

    Returns:
        JSON string confirming the power outage simulation.
    """
    topic = f"commands/{site_id}/power"
    payload = json.dumps({"action": "outage", "duration_seconds": duration_seconds})

    cmd = f'mosquitto_pub -h localhost -t "{topic}" -m \'{payload}\''
    result = _run_cmd(cmd, cwd="/tmp")

    return json.dumps({
        "action": "power_outage",
        "site_id": site_id,
        "duration_seconds": duration_seconds,
        **result
    })


def scale_fleet(num_trucks: int = None, num_cold_rooms: int = None) -> str:
    """Scale the simulated fleet size by restarting with new counts.

    Args:
        num_trucks: New number of trucks (optional)
        num_cold_rooms: New number of cold rooms (optional)

    Returns:
        JSON string with scaling result.
    """
    env = {}
    if num_trucks is not None:
        env["NUM_TRUCKS"] = str(num_trucks)
    if num_cold_rooms is not None:
        env["NUM_COLD_ROOMS"] = str(num_cold_rooms)

    if not env:
        return json.dumps({"error": "Specify num_trucks and/or num_cold_rooms"})

    return restart_simulator(env_overrides=env)
