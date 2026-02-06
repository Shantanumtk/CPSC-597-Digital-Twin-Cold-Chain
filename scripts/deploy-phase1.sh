#!/bin/bash
# =============================================================================
# Cold Chain Digital Twin - Phase 1 Deployment Script
# Deploys: VPC + MQTT Broker (EC2) with TLS
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "=============================================="
echo "Cold Chain Digital Twin - Phase 1 Deployment"
echo "=============================================="
echo -e "${NC}"

# -----------------------------------------------------------------------------
# Prerequisites Check
# -----------------------------------------------------------------------------

echo -e "${YELLOW}[1/4] Checking prerequisites...${NC}"

check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 is not installed${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ $1 found${NC}"
    fi
}

check_command "terraform"
check_command "aws"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    echo "Run: aws configure"
    exit 1
else
    echo -e "${GREEN}✓ AWS credentials configured${NC}"
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=$(aws configure get region)
    echo "  Account: $AWS_ACCOUNT"
    echo "  Region: $AWS_REGION"
fi

# -----------------------------------------------------------------------------
# Terraform Initialization
# -----------------------------------------------------------------------------

echo ""
echo -e "${YELLOW}[2/4] Initializing Terraform...${NC}"

cd terraform

if [ ! -f "terraform.tfvars" ]; then
    echo -e "${YELLOW}Creating terraform.tfvars from example...${NC}"
    cp terraform.tfvars.example terraform.tfvars
    echo -e "${YELLOW}⚠️  Please review terraform.tfvars and customize as needed${NC}"
fi

terraform init

# -----------------------------------------------------------------------------
# Terraform Plan
# -----------------------------------------------------------------------------

echo ""
echo -e "${YELLOW}[3/4] Planning infrastructure...${NC}"

terraform plan -out=phase1.tfplan

echo ""
echo -e "${YELLOW}Review the plan above.${NC}"
read -p "Do you want to apply this plan? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${RED}Deployment cancelled${NC}"
    exit 1
fi

# -----------------------------------------------------------------------------
# Terraform Apply
# -----------------------------------------------------------------------------

echo ""
echo -e "${YELLOW}[4/4] Deploying infrastructure...${NC}"

terraform apply phase1.tfplan

# Clean up plan file
rm -f phase1.tfplan

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

echo ""
echo -e "${GREEN}"
echo "=============================================="
echo "Phase 1 Deployment Complete!"
echo "=============================================="
echo -e "${NC}"

MQTT_IP=$(terraform output -raw mqtt_broker_public_ip)

echo ""
echo -e "${BLUE}MQTT Broker:${NC}"
echo "  Public IP: $MQTT_IP"
echo "  MQTT Port: 1883"
echo "  TLS Port:  8883"
echo "  WebSocket: 9001"

echo ""
echo -e "${BLUE}Test MQTT Connection:${NC}"
echo "  Subscribe: mosquitto_sub -h $MQTT_IP -p 1883 -t '#' -v"
echo "  Publish:   mosquitto_pub -h $MQTT_IP -p 1883 -t 'test' -m 'hello'"

echo ""
echo -e "${BLUE}Connect Sensor Simulator:${NC}"
echo "  export MQTT_BROKER=$MQTT_IP"
echo "  docker-compose up -d"

echo ""
echo -e "${BLUE}SSH to MQTT Broker:${NC}"
echo "  aws ssm start-session --target $(terraform output -raw mqtt_broker_instance_id)"

echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Test MQTT connection with mosquitto_sub"
echo "  2. Run sensor simulator pointing to $MQTT_IP"
echo "  3. Proceed to Phase 2: MQTT → Kafka Bridge"
echo ""