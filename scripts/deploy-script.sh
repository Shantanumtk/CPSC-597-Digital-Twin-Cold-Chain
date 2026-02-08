#!/bin/bash
# =============================================================================
# Cold Chain Digital Twin - Full Deployment Script
# Deploys: Terraform → ECR Images → EKS Apps
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
AWS_REGION="us-west-2"
AWS_ACCOUNT_ID="443071119316"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}"
echo "=============================================="
echo "Cold Chain Digital Twin - Full Deployment"
echo "=============================================="
echo -e "${NC}"

# -----------------------------------------------------------------------------
# Step 1: Terraform Apply
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[1/11] Deploying Infrastructure with Terraform...${NC}"

cd "$PROJECT_DIR/terraform"
terraform init
terraform apply -auto-approve

# Get outputs
MQTT_IP=$(terraform output -raw mqtt_broker_public_ip)
MONGODB_IP=$(terraform output -raw mongodb_private_ip)
ECR_BRIDGE_URL=$(terraform output -raw ecr_repository_url)
ECR_INGESTION_URL=$(terraform output -raw ecr_ingestion_url)
ECR_STATE_ENGINE_URL=$(terraform output -raw ecr_state_engine_url)
EKS_CLUSTER_NAME=$(terraform output -raw eks_cluster_name)

echo -e "${GREEN}✓ Terraform complete${NC}"
echo "  MQTT IP: $MQTT_IP"
echo "  MongoDB IP: $MONGODB_IP"
echo "  EKS Cluster: $EKS_CLUSTER_NAME"

# -----------------------------------------------------------------------------
# Step 2: Wait for EC2 instances to initialize
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[2/11] Waiting for EC2 instances to initialize...${NC}"

sleep 90

echo -e "${GREEN}✓ EC2 initialization complete${NC}"

# -----------------------------------------------------------------------------
# Step 3: Build and Push Bridge Image to ECR
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[3/11] Building and pushing Bridge image to ECR...${NC}"

cd "$PROJECT_DIR/bridge"

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

docker build --platform linux/amd64 -t coldchain-bridge .
docker tag coldchain-bridge:latest "$ECR_BRIDGE_URL:latest"
docker push "$ECR_BRIDGE_URL:latest"

echo -e "${GREEN}✓ Bridge image pushed to ECR${NC}"

# -----------------------------------------------------------------------------
# Step 4: Build and Push Ingestion Image to ECR
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[4/11] Building and pushing Ingestion image to ECR...${NC}"

cd "$PROJECT_DIR/ingestion"

docker build --platform linux/amd64 -t coldchain-ingestion .
docker tag coldchain-ingestion:latest "$ECR_INGESTION_URL:latest"
docker push "$ECR_INGESTION_URL:latest"

echo -e "${GREEN}✓ Ingestion image pushed to ECR${NC}"

# -----------------------------------------------------------------------------
# Step 5: Build and Push Kafka Image to ECR
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[5/11] Building and pushing Kafka image to ECR...${NC}"

aws ecr create-repository --repository-name coldchain-kafka --region $AWS_REGION 2>/dev/null || true

docker pull --platform linux/amd64 apache/kafka:3.9.0
docker tag apache/kafka:3.9.0 "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/coldchain-kafka:3.9.0"
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/coldchain-kafka:3.9.0"

echo -e "${GREEN}✓ Kafka image pushed to ECR${NC}"

# -----------------------------------------------------------------------------
# Step 6: Build and Push Redis Image to ECR
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[6/11] Building and pushing Redis image to ECR...${NC}"

aws ecr create-repository --repository-name coldchain-redis --region $AWS_REGION 2>/dev/null || true

docker pull --platform linux/amd64 redis:7-alpine
docker tag redis:7-alpine "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/coldchain-redis:7-alpine"
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/coldchain-redis:7-alpine"

echo -e "${GREEN}✓ Redis image pushed to ECR${NC}"

# -----------------------------------------------------------------------------
# Step 7: Build and Push State Engine Image to ECR
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[7/11] Building and pushing State Engine image to ECR...${NC}"

cd "$PROJECT_DIR/state-engine"

docker build --platform linux/amd64 -t coldchain-state-engine .
docker tag coldchain-state-engine:latest "$ECR_STATE_ENGINE_URL:latest"
docker push "$ECR_STATE_ENGINE_URL:latest"

echo -e "${GREEN}✓ State Engine image pushed to ECR${NC}"

# -----------------------------------------------------------------------------
# Step 8: Configure kubectl
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[8/11] Configuring kubectl for EKS...${NC}"

aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER_NAME

kubectl get nodes

echo -e "${GREEN}✓ kubectl configured${NC}"

# -----------------------------------------------------------------------------
# Step 9: Deploy Core Kubernetes Resources
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[9/11] Deploying core Kubernetes resources...${NC}"

cd "$PROJECT_DIR"

# Update configmaps with actual IPs
sed -i.bak "s/MQTT_BROKER_IP_PLACEHOLDER/$MQTT_IP/" k8s/bridge/bridge-configmap.yaml
sed -i.bak "s|MONGO_URI_PLACEHOLDER|mongodb://$MONGODB_IP:27017|" k8s/ingestion/ingestion-configmap.yaml
sed -i.bak "s|MONGO_URI_PLACEHOLDER|mongodb://$MONGODB_IP:27017|" k8s/state-engine/state-engine-configmap.yaml

# Apply namespace
kubectl apply -f k8s/namespace.yaml

# Apply Kafka
kubectl apply -f k8s/kafka/
echo "  Waiting for Kafka to be ready..."
kubectl wait --for=condition=ready pod -l app=kafka -n coldchain --timeout=180s

# Apply Bridge
kubectl apply -f k8s/bridge/
echo "  Waiting for Bridge to be ready..."
kubectl wait --for=condition=ready pod -l app=mqtt-kafka-bridge -n coldchain --timeout=120s

# Apply Ingestion
kubectl apply -f k8s/ingestion/
echo "  Waiting for Ingestion to be ready..."
kubectl wait --for=condition=ready pod -l app=kafka-consumer -n coldchain --timeout=120s

# Apply Redis
kubectl apply -f k8s/redis/
echo "  Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n coldchain --timeout=60s

# Apply State Engine
kubectl apply -f k8s/state-engine/
echo "  Waiting for State Engine to be ready..."
kubectl wait --for=condition=ready pod -l app=state-engine -n coldchain --timeout=120s

# Restore original configmaps
mv k8s/bridge/bridge-configmap.yaml.bak k8s/bridge/bridge-configmap.yaml
mv k8s/ingestion/ingestion-configmap.yaml.bak k8s/ingestion/ingestion-configmap.yaml
mv k8s/state-engine/state-engine-configmap.yaml.bak k8s/state-engine/state-engine-configmap.yaml

echo -e "${GREEN}✓ Core Kubernetes resources deployed${NC}"

# -----------------------------------------------------------------------------
# Step 10: Build and Push Dashboard Image to ECR
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[10/11] Building and pushing Dashboard image to ECR...${NC}"

# Wait for State Engine LoadBalancer
echo "  Waiting for State Engine LoadBalancer..."
sleep 30

API_URL=""
for i in {1..12}; do
  API_URL=$(kubectl get svc -n coldchain state-engine -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
  if [ -n "$API_URL" ]; then
    break
  fi
  echo "  Waiting for LoadBalancer... ($i/12)"
  sleep 10
done

if [ -z "$API_URL" ]; then
  echo -e "${RED}Failed to get State Engine API URL${NC}"
  exit 1
fi

echo "  State Engine API: http://$API_URL"

cd "$PROJECT_DIR/dashboard"

docker build \
  --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_API_URL=http://$API_URL \
  -t coldchain-dashboard .

docker tag coldchain-dashboard:latest "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/coldchain-digital-twin-dashboard:latest"
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/coldchain-digital-twin-dashboard:latest"

echo -e "${GREEN}✓ Dashboard image pushed to ECR${NC}"

# -----------------------------------------------------------------------------
# Step 11: Deploy Dashboard
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[11/11] Deploying Dashboard...${NC}"

cd "$PROJECT_DIR"

kubectl apply -f k8s/dashboard/
echo "  Waiting for Dashboard to be ready..."
kubectl wait --for=condition=ready pod -l app=dashboard -n coldchain --timeout=120s

echo -e "${GREEN}✓ Dashboard deployed${NC}"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo -e "${GREEN}"
echo "=============================================="
echo "Deployment Complete!"
echo "=============================================="
echo -e "${NC}"

echo -e "${BLUE}MQTT Broker:${NC}"
echo "  IP: $MQTT_IP"
echo "  Test: mosquitto_sub -h $MQTT_IP -p 1883 -t '#' -v"

echo ""
echo -e "${BLUE}MongoDB:${NC}"
echo "  Private IP: $MONGODB_IP"
echo "  Connection: mongodb://$MONGODB_IP:27017/coldchain"

echo ""
echo -e "${BLUE}EKS Cluster:${NC}"
echo "  Name: $EKS_CLUSTER_NAME"
echo "  Pods: kubectl get pods -n coldchain"

echo ""
echo -e "${BLUE}State Engine API:${NC}"
echo "  URL: http://$API_URL"
echo "  Health: curl http://$API_URL/health"
echo "  Docs: http://$API_URL/docs"

echo ""
echo -e "${BLUE}Dashboard:${NC}"
DASHBOARD_URL=$(kubectl get svc -n coldchain dashboard -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
echo "  URL: http://$DASHBOARD_URL"

echo ""
echo -e "${BLUE}Verify Data Flow:${NC}"
echo "  Bridge logs: kubectl logs -n coldchain -l app=mqtt-kafka-bridge --tail=20"
echo "  Consumer logs: kubectl logs -n coldchain -l app=kafka-consumer --tail=20"
echo "  State Engine logs: kubectl logs -n coldchain -l app=state-engine --tail=20"

echo ""
echo -e "${GREEN}All systems running!${NC}"