#!/bin/bash
set -e
AWS_REGION="${aws_region}"
SECRET_ARN="${secret_arn}"
MQTT_PORT="${mqtt_port}"
MQTT_TLS_PORT="${mqtt_tls_port}"
WEBSOCKET_PORT="${websocket_port}"
LOG_GROUP_NAME="${log_group_name}"

echo "=========================================="
echo "Cold Chain MQTT Broker Setup - Ubuntu 24"
echo "=========================================="

# Install packages
apt-get update -y
apt-get install -y mosquitto mosquitto-clients jq docker.io docker-compose-v2 git
snap install aws-cli --classic

# Enable Docker
systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu

# Setup Mosquitto certs
mkdir -p /etc/mosquitto/certs
chmod 700 /etc/mosquitto/certs
SECRET_JSON=$(aws secretsmanager get-secret-value --secret-id "$SECRET_ARN" --region "$AWS_REGION" --query SecretString --output text)
echo "$SECRET_JSON" | jq -r '.ca_cert' > /etc/mosquitto/certs/ca.crt
echo "$SECRET_JSON" | jq -r '.server_cert' > /etc/mosquitto/certs/server.crt
echo "$SECRET_JSON" | jq -r '.server_key' > /etc/mosquitto/certs/server.key
chmod 644 /etc/mosquitto/certs/ca.crt
chmod 644 /etc/mosquitto/certs/server.crt
chmod 600 /etc/mosquitto/certs/server.key
chown -R mosquitto:mosquitto /etc/mosquitto/certs

# Configure Mosquitto
cat > /etc/mosquitto/conf.d/coldchain.conf << MQTTCONFIG
listener $MQTT_PORT 0.0.0.0
allow_anonymous true
listener $WEBSOCKET_PORT 0.0.0.0
protocol websockets
allow_anonymous true
MQTTCONFIG

mkdir -p /var/log/mosquitto
chown mosquitto:mosquitto /var/log/mosquitto
systemctl enable mosquitto
systemctl restart mosquitto

echo "=========================================="
echo "Deploying Sensor Simulator from GitHub"
echo "=========================================="

# Clone the repository
cd /home/ubuntu
git clone https://github.com/Shantanumtk/CPSC-597-Digital-Twin-Cold-Chain.git
cd CPSC-597-Digital-Twin-Cold-Chain

# Update docker-compose to use localhost for MQTT
#sed -i 's/MQTT_BROKER=host.docker.internal/MQTT_BROKER=localhost/' docker-compose.yml

# Build the sensor simulator image
docker build -t coldchain-sensor-simulator ./sensors

# Run with docker compose using host network
docker compose up -d --build

# Set ownership for ubuntu user
chown -R ubuntu:ubuntu /home/ubuntu/CPSC-597-Digital-Twin-Cold-Chain

echo "=========================================="
echo "MQTT Broker + Simulator Setup Complete!"
echo "=========================================="