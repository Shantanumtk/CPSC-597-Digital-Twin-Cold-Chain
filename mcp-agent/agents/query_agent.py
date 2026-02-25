"""
Query Agent — Answers natural language questions about cold chain data.
Uses Claude API with tool calling to query MongoDB, Redis, Kafka, and MQTT.
"""

import os
import json
import anthropic
from tools import mongo_tools, redis_tools, kafka_tools, mqtt_tools

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """You are a Cold Chain Digital Twin AI assistant. You help logistics operators 
monitor and analyze their refrigerated fleet (trucks and cold storage rooms).

You have access to real-time and historical data through these tools:
- MongoDB: Historical telemetry, digital twin states, SLA metrics, breach events
- Redis: Real-time live state of all assets
- Kafka: Recent streaming events and alerts
- MQTT: Live sensor readings directly from devices

When answering questions:
1. First check real-time data (Redis/MQTT) for current status
2. Then check recent events (Kafka) for context
3. Then query history (MongoDB) for trends and root cause analysis
4. Correlate findings across sources to give a comprehensive answer

Always provide specific data points (temperatures, timestamps, SLA percentages).
If you detect anomalies, explain the likely cause based on correlated events.
Be concise but thorough. Use the data — don't speculate without evidence."""

# Tool definitions for Claude API
TOOLS = [
    {
        "name": "get_live_state",
        "description": "Get real-time state of an asset from Redis (temperature, door status, compressor, etc.)",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "Asset ID like 'truck-01' or 'cold-room-site-1-room-1'"}
            },
            "required": ["asset_id"]
        }
    },
    {
        "name": "get_all_live_states",
        "description": "Get real-time state for ALL assets from Redis",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_live_reading",
        "description": "Get the latest MQTT sensor reading directly from the device",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "Asset ID"}
            },
            "required": ["asset_id"]
        }
    },
    {
        "name": "list_active_sensors",
        "description": "List all sensors currently publishing MQTT data",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "query_telemetry",
        "description": "Query historical telemetry readings from MongoDB",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "Asset ID"},
                "hours": {"type": "integer", "description": "Hours of history (default 2)", "default": 2},
                "limit": {"type": "integer", "description": "Max results (default 50)", "default": 50}
            },
            "required": ["asset_id"]
        }
    },
    {
        "name": "get_twin_state",
        "description": "Get the digital twin state including SLA metrics from MongoDB",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "Asset ID"}
            },
            "required": ["asset_id"]
        }
    },
    {
        "name": "get_sla_metrics",
        "description": "Get SLA compliance metrics — time-in-band %, breach count, compliance score",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "Asset ID"}
            },
            "required": ["asset_id"]
        }
    },
    {
        "name": "find_breaches",
        "description": "Find temperature breach events from MongoDB",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "Optional asset ID filter"},
                "hours": {"type": "integer", "description": "Hours to look back (default 24)", "default": 24},
                "limit": {"type": "integer", "description": "Max results (default 20)", "default": 20}
            }
        }
    },
    {
        "name": "compare_assets",
        "description": "Compare digital twin states across multiple assets",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of asset IDs to compare. If empty, compares all."
                }
            }
        }
    },
    {
        "name": "list_all_assets",
        "description": "List all known assets in the digital twin system",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "read_recent_events",
        "description": "Read recent events from Kafka topics",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic_key": {
                    "type": "string",
                    "description": "One of: 'trucks', 'rooms', 'alerts'",
                    "enum": ["trucks", "rooms", "alerts"]
                },
                "count": {"type": "integer", "description": "Number of messages (default 10)", "default": 10}
            },
            "required": ["topic_key"]
        }
    },
    {
        "name": "get_alerts_from_redis",
        "description": "Get recent alerts from Redis for an asset or all assets",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "Optional asset ID filter"}
            }
        }
    },
]

# Map tool names to functions
TOOL_HANDLERS = {
    "get_live_state": lambda args: redis_tools.get_live_state(**args),
    "get_all_live_states": lambda args: redis_tools.get_all_live_states(),
    "get_live_reading": lambda args: mqtt_tools.get_live_reading(**args),
    "list_active_sensors": lambda args: mqtt_tools.list_active_sensors(),
    "query_telemetry": lambda args: mongo_tools.query_telemetry(**args),
    "get_twin_state": lambda args: mongo_tools.get_twin_state(**args),
    "get_sla_metrics": lambda args: mongo_tools.get_sla_metrics(**args),
    "find_breaches": lambda args: mongo_tools.find_breaches(**args),
    "compare_assets": lambda args: mongo_tools.compare_assets(**args),
    "list_all_assets": lambda args: mongo_tools.list_all_assets(),
    "read_recent_events": lambda args: kafka_tools.read_recent_events(**args),
    "get_alerts_from_redis": lambda args: redis_tools.get_alerts_from_redis(**args),
}


def process_query(user_message: str, conversation_history: list = None) -> str:
    """Process a natural language query using Claude with tool calling.

    Args:
        user_message: The user's question
        conversation_history: Optional list of previous messages

    Returns:
        The assistant's final text response.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    messages = conversation_history or []
    messages.append({"role": "user", "content": user_message})

    # Agentic loop: keep calling tools until Claude gives a text response
    max_iterations = 10
    for _ in range(max_iterations):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Check if Claude wants to use tools
        if response.stop_reason == "tool_use":
            # Add assistant message with tool use blocks
            messages.append({"role": "assistant", "content": response.content})

            # Process each tool call
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    handler = TOOL_HANDLERS.get(tool_name)
                    if handler:
                        try:
                            result = handler(tool_input)
                        except Exception as e:
                            result = json.dumps({"error": f"Tool {tool_name} failed: {str(e)}"})
                    else:
                        result = json.dumps({"error": f"Unknown tool: {tool_name}"})

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})

        else:
            # Claude gave a final text response
            text_parts = [block.text for block in response.content if hasattr(block, "text")]
            return "\n".join(text_parts)

    return "I wasn't able to fully answer your question within the allowed number of tool calls. Please try a more specific question."
