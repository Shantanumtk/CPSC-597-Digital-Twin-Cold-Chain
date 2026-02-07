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
echo -e "${YELLOW}[1/5] Deploying Infrastructure with Terraform...${NC}"

cd "$PROJECT_DIR/terraform"
terraform init
terraform apply -auto-approve

# Get outputs
MQTT_IP=$(terraform output -raw mqtt_broker_public_ip)
ECR_BRIDGE_URL=$(terraform output -raw ecr_repository_url)
EKS_CLUSTER_NAME=$(terraform output -raw eks_cluster_name)

echo -e "${GREEN}✓ Terraform complete${NC}"
echo "  MQTT IP: $MQTT_IP"
echo "  ECR URL: $ECR_BRIDGE_URL"
echo "  EKS Cluster: $EKS_CLUSTER_NAME"

# -----------------------------------------------------------------------------
# Step 2: Wait for EC2 Simulator to be ready
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[2/5] Waiting for EC2 and Simulator to initialize...${NC}"

sleep 60  # Wait for user-data script to complete

echo -e "${GREEN}✓ EC2 initialization complete${NC}"

# -----------------------------------------------------------------------------
# Step 3: Build and Push Bridge Image to ECR
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[3/5] Building and pushing Bridge image to ECR...${NC}"

cd "$PROJECT_DIR/bridge"

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "$ECR_BRIDGE_URL"

# Build for linux/amd64
docker build --platform linux/amd64 -t coldchain-bridge .

# Tag and push
docker tag coldchain-bridge:latest "$ECR_BRIDGE_URL:latest"
docker push "$ECR_BRIDGE_URL:latest"

echo -e "${GREEN}✓ Bridge image pushed to ECR${NC}"

# -----------------------------------------------------------------------------
# Step 4: Configure kubectl
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[4/5] Configuring kubectl for EKS...${NC}"

aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER_NAME

# Verify connection
kubectl get nodes

echo -e "${GREEN}✓ kubectl configured${NC}"

# -----------------------------------------------------------------------------
# Step 5: Deploy Kubernetes Resources
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[5/5] Deploying Kubernetes resources...${NC}"

cd "$PROJECT_DIR"

# Update bridge configmap with actual MQTT IP
sed -i.bak "s/MQTT_BROKER_IP_PLACEHOLDER/$MQTT_IP/" k8s/bridge/bridge-configmap.yaml

# Apply namespace
kubectl apply -f k8s/namespace.yaml

# Apply Kafka
kubectl apply -f k8s/kafka/

# Wait for Kafka to be ready
echo "  Waiting for Kafka to be ready..."
kubectl wait --for=condition=ready pod -l app=kafka -n coldchain --timeout=180s

# Apply Bridge
kubectl apply -f k8s/bridge/

# Wait for Bridge to be ready
echo "  Waiting for Bridge to be ready..."
kubectl wait --for=condition=ready pod -l app=mqtt-kafka-bridge -n coldchain --timeout=120s

# Restore original configmap for git
mv k8s/bridge/bridge-configmap.yaml.bak k8s/bridge/bridge-configmap.yaml

echo -e "${GREEN}✓ Kubernetes resources deployed${NC}"

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
echo -e "${BLUE}EKS Cluster:${NC}"
echo "  Name: $EKS_CLUSTER_NAME"
echo "  Pods: kubectl get pods -n coldchain"

echo ""
echo -e "${BLUE}Verify Data Flow:${NC}"
echo "  Bridge logs: kubectl logs -n coldchain -l app=mqtt-kafka-bridge --tail=20"
echo "  Kafka topics: kubectl exec -it -n coldchain \$(kubectl get pods -n coldchain -l app=kafka -o jsonpath='{.items[0].metadata.name}') -- /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092"

echo ""
echo -e "${GREEN}All systems running!${NC}"