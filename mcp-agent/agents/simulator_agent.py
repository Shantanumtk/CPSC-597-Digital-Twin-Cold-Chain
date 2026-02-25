"""
Simulator Controller Agent — Controls docker-compose sensor environment
through natural language commands using Claude API with tool calling.
"""

import os
import json
import anthropic
from tools import simulator_tools

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """You are a Cold Chain Simulation Controller. You can manipulate the sensor
simulator environment to create test scenarios for the cold chain monitoring system.

You control a docker-compose environment running on an EC2 instance that simulates:
- Refrigerated trucks with temperature sensors, door sensors, and compressors
- Cold storage rooms in warehouses with temperature and humidity sensors

You can:
- Open/close truck doors to simulate loading events
- Trigger compressor failures to simulate equipment breakdowns
- Simulate power outages at warehouse sites
- Scale the fleet (add/remove trucks and cold rooms)
- Restart the simulator with different configurations

When the user describes a scenario, figure out which tools to call and execute them.
Confirm what you did and explain what the user should expect to see in the monitoring system.

Be specific about timings, asset IDs, and expected effects."""

TOOLS = [
    {
        "name": "get_simulator_status",
        "description": "Get current status of the sensor simulator containers",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_simulator_env",
        "description": "Get current simulator configuration (number of trucks, rooms, etc.)",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "trigger_door_event",
        "description": "Open a truck or room door for a specified duration",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "Asset ID (e.g. 'truck-02')"},
                "duration_seconds": {"type": "integer", "description": "How long door stays open (default 60)", "default": 60}
            },
            "required": ["asset_id"]
        }
    },
    {
        "name": "trigger_compressor_failure",
        "description": "Simulate compressor failure on an asset",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "Asset ID (e.g. 'truck-05')"},
                "duration_seconds": {"type": "integer", "description": "Duration of failure (default 300)", "default": 300}
            },
            "required": ["asset_id"]
        }
    },
    {
        "name": "trigger_power_outage",
        "description": "Simulate power outage at a warehouse site",
        "input_schema": {
            "type": "object",
            "properties": {
                "site_id": {"type": "string", "description": "Site ID (default 'site-1')", "default": "site-1"},
                "duration_seconds": {"type": "integer", "description": "Duration of outage (default 600)", "default": 600}
            }
        }
    },
    {
        "name": "scale_fleet",
        "description": "Change the number of simulated trucks and/or cold rooms",
        "input_schema": {
            "type": "object",
            "properties": {
                "num_trucks": {"type": "integer", "description": "New number of trucks"},
                "num_cold_rooms": {"type": "integer", "description": "New number of cold rooms"}
            }
        }
    },
    {
        "name": "restart_simulator",
        "description": "Restart the sensor simulator with optional config changes",
        "input_schema": {
            "type": "object",
            "properties": {
                "env_overrides": {
                    "type": "object",
                    "description": "Environment variable overrides (e.g. {'PUBLISH_INTERVAL': '0.5'})"
                }
            }
        }
    },
]

TOOL_HANDLERS = {
    "get_simulator_status": lambda args: simulator_tools.get_simulator_status(),
    "get_simulator_env": lambda args: simulator_tools.get_simulator_env(),
    "trigger_door_event": lambda args: simulator_tools.trigger_door_event(**args),
    "trigger_compressor_failure": lambda args: simulator_tools.trigger_compressor_failure(**args),
    "trigger_power_outage": lambda args: simulator_tools.trigger_power_outage(**args),
    "scale_fleet": lambda args: simulator_tools.scale_fleet(**args),
    "restart_simulator": lambda args: simulator_tools.restart_simulator(**args),
}


def process_command(user_message: str, conversation_history: list = None) -> str:
    """Process a simulation command using Claude with tool calling.

    Args:
        user_message: The user's simulation command
        conversation_history: Optional list of previous messages

    Returns:
        The assistant's response confirming actions taken.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    messages = conversation_history or []
    messages.append({"role": "user", "content": user_message})

    max_iterations = 10
    for _ in range(max_iterations):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    handler = TOOL_HANDLERS.get(block.name)
                    if handler:
                        try:
                            result = handler(block.input)
                        except Exception as e:
                            result = json.dumps({"error": f"Tool {block.name} failed: {str(e)}"})
                    else:
                        result = json.dumps({"error": f"Unknown tool: {block.name}"})

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})
        else:
            text_parts = [block.text for block in response.content if hasattr(block, "text")]
            return "\n".join(text_parts)

    return "Simulation command processing exceeded maximum iterations."
