#!/bin/bash
# =============================================================================
# Cold Chain Digital Twin - Destroy All Resources
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${RED}"
echo "=============================================="
echo "WARNING: This will destroy ALL resources!"
echo "=============================================="
echo -e "${NC}"

read -p "Are you sure? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

# Delete Kubernetes resources
echo -e "${YELLOW}[1/3] Deleting Kubernetes resources...${NC}"
kubectl delete namespace coldchain --ignore-not-found=true

# Delete ECR images
echo -e "${YELLOW}[2/3] Deleting ECR images...${NC}"
aws ecr batch-delete-image --repository-name coldchain-digital-twin-bridge --image-ids imageTag=latest --region us-west-2 2>/dev/null || true
aws ecr batch-delete-image --repository-name coldchain-kafka --image-ids imageTag=3.9.0 --region us-west-2 2>/dev/null || true

# Terraform destroy
echo -e "${YELLOW}[3/3] Destroying Terraform infrastructure...${NC}"
cd "$PROJECT_DIR/terraform"
terraform destroy -auto-approve

echo -e "${GREEN}"
echo "=============================================="
echo "All resources destroyed!"
echo "=============================================="
echo -e "${NC}"