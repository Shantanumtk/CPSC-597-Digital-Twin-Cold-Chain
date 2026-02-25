"""
Kafka MCP Tools — Read streaming events and alerts from Kafka topics.
Connects to Kafka running on EKS.
"""

import os
import json
import asyncio
from aiokafka import AIOKafkaConsumer

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

TOPICS = {
    "trucks": "coldchain.telemetry.trucks",
    "rooms": "coldchain.telemetry.rooms",
    "alerts": "coldchain.alerts",
}


async def _consume_recent(topic: str, max_messages: int = 10, timeout_ms: int = 5000) -> list:
    """Internal helper: consume recent messages from a Kafka topic."""
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_SERVERS,
        auto_offset_reset="latest",
        enable_auto_commit=False,
        consumer_timeout_ms=timeout_ms,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    messages = []
    try:
        await consumer.start()
        # Seek to end minus N messages
        partitions = consumer.assignment()
        for tp in partitions:
            end_offset = await consumer.end_offsets([tp])
            offset = max(0, end_offset[tp] - max_messages)
            consumer.seek(tp, offset)

        async for msg in consumer:
            messages.append({
                "topic": msg.topic,
                "partition": msg.partition,
                "offset": msg.offset,
                "timestamp": msg.timestamp,
                "value": msg.value,
            })
            if len(messages) >= max_messages:
                break
    except Exception as e:
        messages.append({"error": str(e)})
    finally:
        await consumer.stop()

    return messages


def read_recent_events(topic_key: str = "alerts", count: int = 10) -> str:
    """Read the most recent events from a Kafka topic.

    Args:
        topic_key: One of 'trucks', 'rooms', or 'alerts' (default 'alerts')
        count: Number of recent messages to read (default 10)

    Returns:
        JSON string with recent Kafka messages.
    """
    topic = TOPICS.get(topic_key, topic_key)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If called from async context
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                messages = pool.submit(
                    lambda: asyncio.run(_consume_recent(topic, count))
                ).result(timeout=10)
        else:
            messages = asyncio.run(_consume_recent(topic, count))
    except Exception as e:
        return json.dumps({"error": f"Failed to read from Kafka topic {topic}: {str(e)}"})

    if not messages:
        return json.dumps({"message": f"No recent messages on topic {topic}"})

    return json.dumps(messages, default=str)


def list_topics() -> str:
    """List available Kafka topics for the cold chain system.

    Returns:
        JSON string with available topic names and their keys.
    """
    return json.dumps({
        "available_topics": TOPICS,
        "usage": "Use topic_key (e.g. 'alerts') with read_recent_events"
    })
