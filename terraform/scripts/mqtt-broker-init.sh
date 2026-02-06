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
apt-get update -y
apt-get install -y mosquitto mosquitto-clients jq docker.io docker-compose-v2
snap install aws-cli --classic

# Enable Docker
systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu

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
echo "MQTT Broker Setup Complete!"