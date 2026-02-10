#!/bin/bash
set -e

NAMESPACE=${1:-staging}
PREFIX="/mlops-model-platform/${NAMESPACE}"

echo "Syncing secrets from ${PREFIX} to namespace ${NAMESPACE}..."

DB_PASSWORD=$(aws ssm get-parameter \
  --name "${PREFIX}/db-password" \
  --with-decryption \
  --query "Parameter.Value" \
  --output text 2>/dev/null || echo "")

API_KEY=$(aws ssm get-parameter \
  --name "${PREFIX}/api-key" \
  --with-decryption \
  --query "Parameter.Value" \
  --output text 2>/dev/null || echo "")

kubectl create secret generic app-secrets \
  --from-literal=DB_PASSWORD="${DB_PASSWORD}" \
  --from-literal=API_KEY="${API_KEY}" \
  --namespace "${NAMESPACE}" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Secrets synced to ${NAMESPACE}/app-secrets"
