FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy simulator code
COPY simulator.py .

# Environment variables with defaults
ENV MQTT_BROKER=mosquitto
ENV MQTT_PORT=1883
ENV MQTT_QOS=1
ENV PUBLISH_INTERVAL=5.0
ENV NUM_COLD_ROOMS=10
ENV NUM_TRUCKS=12

# Run simulator
CMD ["python", "-u", "simulator.py"]
