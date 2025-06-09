#!/bin/bash
# Run overnight maintenance with logging

cd /workspace/years-of-lead
source venv/bin/activate

echo "Starting overnight maintenance at $(date)"
echo "Parameters: --hours 2.0 --budget 75"

python scripts/overnight_maintenance.py --hours 2.0 --budget 75 2>&1 | tee overnight_maintenance_output.log

echo "Overnight maintenance completed at $(date)"