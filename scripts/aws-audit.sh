#!/bin/bash
set -e

# AWS security and cost audit using Prowler
# Checks S3, IAM, and billing configuration
# Usage: ./scripts/aws-audit.sh

echo "=== AWS Security & Cost Audit ==="
echo ""

# check prowler is installed
if ! command -v prowler &> /dev/null; then
    echo "prowler not found. install with: pip install prowler"
    exit 1
fi

# run prowler against S3 and IAM
echo "[Prowler] Running S3 and IAM checks..."
echo ""
prowler aws --services s3 iam --output-formats csv --status FAIL

echo ""

# cost check (separate from prowler)
echo "[Cost] Last 30 days spending by service..."
START_DATE=$(python3 -c "from datetime import date, timedelta; print((date.today() - timedelta(30)).isoformat())")
END_DATE=$(python3 -c "from datetime import date; print(date.today().isoformat())")

aws ce get-cost-and-usage \
    --time-period "Start=$START_DATE,End=$END_DATE" \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=DIMENSION,Key=SERVICE \
    --query 'ResultsByTime[].Groups[?Metrics.BlendedCost.Amount!=`0`].[Keys[0],Metrics.BlendedCost.Amount]' \
    --output table 2>/dev/null || echo "  Cost Explorer not enabled — enable it in the AWS billing console"

echo ""

# billing alarm check
echo "[Billing] Checking for billing alarm..."
ALARMS=$(aws cloudwatch describe-alarms \
    --alarm-name-prefix "billing" \
    --query 'MetricAlarms[].AlarmName' \
    --output text 2>/dev/null || echo "")

if [ -z "$ALARMS" ]; then
    echo "  No billing alarm found. Create one with:"
    echo ""
    echo "  aws cloudwatch put-metric-alarm \\"
    echo "    --alarm-name billing-alarm-5usd \\"
    echo "    --metric-name EstimatedCharges \\"
    echo "    --namespace AWS/Billing \\"
    echo "    --statistic Maximum \\"
    echo "    --period 21600 \\"
    echo "    --threshold 5 \\"
    echo "    --comparison-operator GreaterThanThreshold \\"
    echo "    --evaluation-periods 1 \\"
    echo "    --dimensions Name=Currency,Value=USD"
else
    echo "  Billing alarms: $ALARMS"
fi

echo ""
echo "=== Audit complete ==="
