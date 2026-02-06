#!/bin/bash
# =============================================================================
# Cold Chain Digital Twin - Phase 1 Destroy Script
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}"
echo "=============================================="
echo "WARNING: This will destroy all Phase 1 resources!"
echo "=============================================="
echo -e "${NC}"

echo ""
echo "This will destroy:"
echo "  - VPC and all networking components"
echo "  - MQTT Broker EC2 instance"
echo "  - TLS certificates in Secrets Manager"
echo "  - All associated IAM roles and policies"
echo ""

read -p "Are you sure you want to destroy all resources? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${GREEN}Destruction cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}Destroying Terraform infrastructure...${NC}"

cd terraform
terraform destroy -auto-approve

echo ""
echo -e "${GREEN}"
echo "=============================================="
echo "Phase 1 resources destroyed successfully"
echo "=============================================="
echo -e "${NC}"