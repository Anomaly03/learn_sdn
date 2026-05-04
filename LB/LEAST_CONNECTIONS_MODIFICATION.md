# Least Connections Load Balancing - Modification Summary

## Overview
Modified `rr_lb.py` from **Round-Robin (RR)** algorithm to **Least Connections (LC)** algorithm.

**Original Algorithm:** Counter-based Round-Robin
- Sequentially selects servers: Server1 → Server2 → Server3 → Server1 → ...
- Ignores actual server load/connections

**New Algorithm:** Least Connections
- Selects server with **minimum active connections**
- Dynamically adjusts based on current load
- More intelligent load distribution

---

## Changes Made

### 1. **Initialization Changes** (Lines 35-54)

**Removed:**
```python
self.counter = 0  # Old round-robin counter
```

**Added:**
```python
self.server_connections = {}  # Track active connections per server
self.flow_to_server = {}      # Map cookie → server_ip for cleanup
```

**Initialization Loop:**
```python
for server in self.serverlist:
    self.server_connections[server['ip']] = 0
```

---

### 2. **Flow Removal Handler** (Lines 93-109)

**New Event Handler:**
```python
@set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
def flow_removed_handler(self, ev):
    # Triggered when flow times out (idle_timeout = 7 seconds)
    # Decrements connection counter for that server
    # Cleans up flow_to_server tracking dictionary
```

**Purpose:**
- When OpenFlow flow expires after 7 seconds, connection is considered complete
- Decrements the server's active connection count
- Allows new connections to be directed to that server again

---

### 3. **Server Selection Logic** (Lines 254-268)

**Removed (Old Round-Robin):**
```python
count = self.counter % 3
server_ip_selected = self.serverlist[count]['ip']
self.counter = self.counter + 1
```

**Added (New Least Connections):**
```python
# Select server with MINIMUM active connections
server_ip_selected = min(self.server_connections, 
                         key=self.server_connections.get)

# Increment connection counter for selected server
self.server_connections[server_ip_selected] += 1

print("[LEAST-CONNECTIONS] Selected: {}".format(server_ip_selected))
print("[LOAD-STATUS] Server loads: {}".format(self.server_connections))
```

**How it works:**
1. `min()` finds server with lowest connection count
2. Increment counter when flow is created
3. Connection count is decremented when flow times out

---

### 4. **Flow Tracking** (Lines 275-277)

**Added:**
```python
# Track cookie → server_ip for connection counting on flow removal
self.flow_to_server[cookie] = server_ip_selected
```

**Purpose:**
- Associates OpenFlow flow cookie with the selected server
- When flow is removed (via FlowRemoved event), we know which server to decrement

---

## Algorithm Flow

```
CLIENT REQUEST
    ↓
┌─────────────────────────────────────────┐
│ SELECT SERVER (Least Connections)       │
├─────────────────────────────────────────┤
│ Current loads:                          │
│ Server1: 3 connections                  │
│ Server2: 1 connection ← SELECT THIS     │
│ Server3: 2 connections                  │
└─────────────────────────────────────────┘
    ↓
INSTALL FORWARD + REVERSE FLOWS
    ↓
INCREMENT: server_connections['10.0.0.3'] = 2
    ↓
SAVE: flow_to_server[0x1234abcd] = '10.0.0.3'
    ↓
PACKET ROUTING & RESPONSE
    ↓
[After 7 seconds - FlowRemoved event]
    ↓
DECREMENT: server_connections['10.0.0.3'] = 1
DELETE: flow_to_server[0x1234abcd]
```

---

## Testing with Mininet

### Setup
```bash
# Terminal 1 - Start Controller
docker exec -it learn_sdn bash
cd LB
osken-manager rr_lb.py

# Terminal 2 - Start Topology
docker exec -it learn_sdn bash
cd LB
sudo python3 topo_lb.py
```

### Testing Commands (in Mininet CLI)
```mininet
# Basic test
mininet> h1 curl -s 10.0.0.100 | head -2

# Multiple requests - watch server distribution
mininet> for i in {1..10}; do h1 curl -s 10.0.0.100 >/dev/null; done

# Check flows
mininet> dpctl dump-flows -O OpenFlow13
```

### Expected Output
**Controller Log Example:**
```
[LEAST-CONNECTIONS] Selected server: 10.0.0.2 with 1 active connections
[LOAD-STATUS] Server loads: {'10.0.0.2': 1, '10.0.0.3': 0, '10.0.0.4': 0}

[LEAST-CONNECTIONS] Selected server: 10.0.0.3 with 1 active connections
[LOAD-STATUS] Server loads: {'10.0.0.2': 1, '10.0.0.3': 1, '10.0.0.4': 0}

[LEAST-CONNECTIONS] Selected server: 10.0.0.4 with 1 active connections
[LOAD-STATUS] Server loads: {'10.0.0.2': 1, '10.0.0.3': 1, '10.0.0.4': 1}

[LEAST-CONNECTIONS] Selected server: 10.0.0.2 with 1 active connections
[LOAD-STATUS] Server loads: {'10.0.0.2': 2, '10.0.0.3': 1, '10.0.0.4': 1}

[After 7 seconds flow timeouts...]
[FLOW-REMOVED] Flow expired for server 10.0.0.2, updated loads: {'10.0.0.2': 1, '10.0.0.3': 1, '10.0.0.4': 1}
```

---

## Comparison: Round-Robin vs Least Connections

### Round-Robin (Old)
```
Request 1 → Server 0 (counter=0)
Request 2 → Server 1 (counter=1)
Request 3 → Server 2 (counter=2)
Request 4 → Server 0 (counter=0 again)

Problem: Doesn't care if Server 0 is still handling Request 1!
```

### Least Connections (New)
```
Connection Count: {S1: 0, S2: 0, S3: 0}
Request 1 → Select S1 (load=0) → Count: {S1: 1, S2: 0, S3: 0}
Request 2 → Select S2 (load=0) → Count: {S1: 1, S2: 1, S3: 0}
Request 3 → Select S3 (load=0) → Count: {S1: 1, S2: 1, S3: 1}
Request 4 → Select S1 (load=1) → Count: {S1: 2, S2: 1, S3: 1}

Benefit: Always picks the least busy server!
```

---

## Files Modified
- `LB/rr_lb.py` - Main control plane application

## Dependencies
- No new dependencies added
- Uses existing OS-KEN events: `EventOFPFlowRemoved`

## Performance Impact
- **Memory:** Minimal - additional dictionaries (max 100s of entries)
- **CPU:** Negligible - `min()` operation is O(n) where n=3 servers
- **Latency:** No noticeable increase

---

## Future Enhancements
1. **Weighted Least Connections** - Servers have different weights
2. **Connection Timeout Detection** - More accurate tracking via TCP state
3. **Server Health Checks** - Exclude unhealthy servers from load balancing
4. **Metrics Export** - Prometheus metrics for monitoring

