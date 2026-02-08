#!/bin/bash
set -e

MONGO_DB_NAME="${mongo_db_name}"

echo "=========================================="
echo "MongoDB Setup - Ubuntu 24"
echo "=========================================="

apt-get update -y
apt-get install -y gnupg curl

curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor

echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/8.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-8.0.list

apt-get update -y
apt-get install -y mongodb-org

cat > /etc/mongod.conf << 'MONGOCONFIG'
storage:
  dbPath: /var/lib/mongodb

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

net:
  port: 27017
  bindIp: 0.0.0.0

processManagement:
  timeZoneInfo: /usr/share/zoneinfo
MONGOCONFIG

systemctl daemon-reload
systemctl enable mongod
systemctl start mongod

sleep 10

mongosh $MONGO_DB_NAME << MONGOSCRIPT
db.telemetry.createIndex({ "created_at": 1 }, { expireAfterSeconds: 604800 })
db.telemetry.createIndex({ "sensor_id": 1, "timestamp": -1 })
db.telemetry.createIndex({ "truck_id": 1, "timestamp": -1 })
db.telemetry.createIndex({ "asset_type": 1 })
db.assets.createIndex({ "type": 1 })
db.assets.createIndex({ "last_updated": 1 })
db.alerts.createIndex({ "asset_id": 1, "detected_at": -1 })
db.alerts.createIndex({ "acknowledged": 1 })
db.alerts.createIndex({ "created_at": 1 })
print("Indexes created!")
MONGOSCRIPT

echo "=========================================="
echo "MongoDB Setup Complete!"
echo "=========================================="