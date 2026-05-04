#!/bin/bash

# Test Script untuk Least Connections Load Balancer
# Melakukan automated test dengan multiple curl requests

set -e

echo "=========================================="
echo "Least Connections Load Balancer Test"
echo "=========================================="

# Cleanup sebelumnya
echo "[*] Cleaning up previous mininet instances..."
docker exec learn_sdn bash -c "pkill -f 'osken\|topo' || true; sleep 2; mn -c 2>/dev/null || true"

echo "[*] Starting OS-KEN controller with Least Connections..."
docker exec learn_sdn bash -c "cd LB && osken-manager rr_lb.py > /tmp/controller.log 2>&1" &
CONTROLLER_PID=$!
sleep 5

echo "[*] Starting Mininet topology..."
docker exec learn_sdn bash -c "cd LB && (
  sleep 2
  # Send 9 curl requests
  echo 'Testing with 9 sequential curl requests...'
  for i in {1..9}; do
    echo \"h1 curl -s 10.0.0.100 2>/dev/null | head -c 50\"
  done
  
  sleep 2
  echo 'exit'
) | timeout 40 python3 topo_lb.py > /tmp/topo.log 2>&1" &

sleep 8

echo ""
echo "=========================================="
echo "Controller Output (Load Balancing Decisions)"
echo "=========================================="
grep -E "\[LEAST-CONNECTIONS\]|\[LOAD-STATUS\]|\[FLOW-REMOVED\]" /tmp/controller.log || echo "No LC events yet"

echo ""
echo "=========================================="
echo "Analysis Summary"
echo "=========================================="

# Count selections
echo "Server Selection Distribution:"
grep "\[LEAST-CONNECTIONS\] Selected" /tmp/controller.log | grep -o "10.0.0.[0-9]" | sort | uniq -c | awk '{print "  Server " $2 ": " $1 " selections"}'

echo ""
echo "Final Server Loads:"
tail -n 1 /tmp/controller.log | grep -o "\[LOAD-STATUS\].*" || echo "  (Check controller logs for full details)"

echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="

# Cleanup
echo "[*] Cleaning up..."
docker exec learn_sdn bash -c "pkill -f 'osken\|topo' || true"

# Show full controller log for detail
echo ""
echo "Full Controller Log:"
tail -50 /tmp/controller.log
