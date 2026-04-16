# ArtOfIA CLI - Orchestrator Integration Guide

## Overview

The CLI connects to the orchestrator via WebSocket to:
1. **Receive** events from autonomous agents
2. **Display** operations in real-time
3. **Intercept** approval requests
4. **Send** operator decisions back to orchestrator
5. **Resume** agents with operator's directive

## WebSocket Protocol

### Connection

**Client → Server (Handshake)**
```json
{
  "type": "handshake",
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "username": "operator",
  "clientVersion": "2.0.0"
}
```

**Server → Client (Connection Acknowledged)**
```json
{
  "type": "connection_acknowledged",
  "sessionId": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-15T10:30:00Z",
  "operatorId": "op-12345"
}
```

### Event Stream

**Server → Client (Events)**
```json
{
  "type": "event",
  "data": {
    "type": "AGENT_STARTED",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {
      "agentId": "recon_agent_1",
      "stage": "reconnaissance",
      "target": "target.example.com"
    }
  }
}
```

**Event Types**:
- `AGENT_STARTED` - Agent begins operation
- `AGENT_COMPLETED` - Agent finishes operation
- `AGENT_ERROR` - Agent encountered error
- `TOOL_INVOKED` - Tool/skill executed
- `TOOL_COMPLETED` - Tool completed
- `TOOL_ERROR` - Tool failed
- `SERVICE_DISCOVERED` - Found service
- `VULNERABILITY_FOUND` - Identified vulnerability
- `TECHNOLOGY_IDENTIFIED` - Recognized technology
- `COMMAND_EXECUTED` - Command run
- `COMMAND_OUTPUT` - Command produced output
- `COMMAND_ERROR` - Command failed
- `LEARNING_RECORDED` - Knowledge saved
- `TECHNIQUE_OPTIMIZED` - Technique improved
- `STATUS_UPDATE` - Status changed
- `METRICS_UPDATE` - Metrics updated

### Approval Requests

**Server → Client (Approval Interruption)**
```json
{
  "type": "approval_request",
  "data": {
    "id": "approval-uuid-1",
    "sessionId": "550e8400-e29b-41d4-a716-446655440000",
    "action": {
      "id": "action-uuid-1",
      "name": "Execute Privilege Escalation",
      "description": "Attempt to escalate privileges using CVE-2024-1234",
      "category": "privilege_escalation",
      "riskLevel": "critical",
      "command": "exploit --target vulnerable_service --method kerberoasting",
      "target": "domain_controller.internal",
      "impact": "Will attempt to extract Kerberos tickets, may trigger IDS alerts",
      "context": {
        "discoveredAt": "2024-01-15T10:25:00Z",
        "exploitConfidence": 0.95,
        "estimatedTimeSeconds": 30,
        "retryable": true
      }
    },
    "requestedAt": "2024-01-15T10:30:05Z",
    "timeout": 300,
    "requiredMethod": "interactive",
    "requiresReasoning": true
  }
}
```

**Client → Server (Operator Decision)**

Approve:
```json
{
  "type": "approval_response",
  "data": {
    "approvalId": "approval-uuid-1",
    "sessionId": "550e8400-e29b-41d4-a716-446655440000",
    "decision": "approve",
    "operator": "operator",
    "timestamp": "2024-01-15T10:30:10Z",
    "reasoning": "Risk is acceptable. Target is in test environment."
  }
}
```

Reject:
```json
{
  "type": "approval_response",
  "data": {
    "approvalId": "approval-uuid-1",
    "sessionId": "550e8400-e29b-41d4-a716-446655440000",
    "decision": "reject",
    "operator": "operator",
    "timestamp": "2024-01-15T10:30:08Z",
    "reason": "Not authorized. Requires manager approval."
  }
}
```

### Heartbeat

**Bidirectional (every 30 seconds)**

Client → Server:
```json
{
  "type": "heartbeat",
  "sessionId": "550e8400-e29b-41d4-a716-446655440000"
}
```

Server → Client:
```json
{
  "type": "heartbeat",
  "timestamp": "2024-01-15T10:30:30Z"
}
```

### Command Execution

**Client → Server**
```json
{
  "type": "command",
  "data": {
    "command": "pause",
    "args": [],
    "timeout": 5000
  }
}
```

Supported commands:
- `pause` - Pause all operations
- `resume` - Resume operations
- `status` - Get current status
- `export_events` - Export event log
- `metrics` - Get metrics

**Server → Client**
```json
{
  "type": "command_response",
  "data": {
    "success": true,
    "result": { "paused": true },
    "timestamp": "2024-01-15T10:30:35Z"
  }
}
```

### Error Handling

**Server → Client (Server Error)**
```json
{
  "type": "error",
  "data": {
    "code": "AUTH_FAILED",
    "message": "Invalid session ID",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**Client → Server (Error Acknowledgment)**
```json
{
  "type": "error_ack",
  "data": {
    "errorCode": "AUTH_FAILED",
    "sessionId": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

## State Preservation During Interruption

When approval is requested, orchestrator saves complete state:

```json
{
  "type": "approval_request",
  "data": {
    "id": "approval-uuid-1",
    "action": { /* action details */ },
    "context": {
      "agentState": {
        "currentStage": "exploitation",
        "discoveredServices": 12,
        "vulnerabilitiesFound": 8,
        "exploitsAttempted": 3,
        "successCount": 2
      },
      "memory": {
        "techniques_used": ["nmap", "metasploit"],
        "attack_path": ["scan", "enumerate", "exploit"],
        "learned_vulnerabilities": ["CVE-2024-1234"]
      },
      "lastEventId": "event-uuid-123",
      "frozenAt": "2024-01-15T10:30:05Z"
    }
  }
}
```

When approved, agent resumes with:
```python
# In orchestrator
agent.context = frozen_context  # Restore complete state
agent.resume()  # Continue from where it stopped
```

## CLI Integration Checklist

### Connection Setup
- [ ] Parse `--orchestrator` URL
- [ ] Generate or use `--session` ID (UUID v4)
- [ ] Get `--username` (default: $USER)
- [ ] Initialize `OrchestratorClient`
- [ ] Call `client.connect()`

### Event Handling
- [ ] Subscribe to `event` events
- [ ] Buffer events (max 10K)
- [ ] Update `EventBus`
- [ ] Notify components
- [ ] Render in real-time

### Approval Handling
- [ ] Listen for `approval_requested` events
- [ ] Store in pending queue
- [ ] Show `ApprovalPanel`
- [ ] Wait for operator Y/N
- [ ] Call `client.approveAction()` or `client.rejectAction()`
- [ ] Send response with decision
- [ ] Update metrics

### State Synchronization
- [ ] Track connection status
- [ ] Handle reconnection
- [ ] Preserve pending approvals
- [ ] Maintain event history
- [ ] Save metrics

## Example Integration

### 1. Start CLI
```bash
artofIA --orchestrator ws://localhost:9000 --username alice
```

### 2. CLI Connects
```
[11:30:00] ✓ Connecting to ws://localhost:9000...
[11:30:01] ✓ Connected as alice (session: 550e8400-e29b-41d4-a716-446655440000)
[11:30:02] Waiting for events...
```

### 3. Agent Starts Operation
```
Orchestrator sends: AGENT_STARTED(recon_agent_1)
CLI displays: ▶ AGENT_STARTED at 11:30:05
Metrics updated: 1 event received
```

### 4. Services Discovered
```
Orchestrator sends: SERVICE_DISCOVERED(http:80, ssh:22)
CLI displays: ◆ SERVICE_DISCOVERED [2 services]
CLI updates: 2 events received
```

### 5. Vulnerability Found
```
Orchestrator sends: VULNERABILITY_FOUND(CVE-2024-1234, CRITICAL)
CLI displays: ⚠ VULNERABILITY_FOUND at 11:30:15
CLI updates graph: Shows vulnerability on service
Metrics updated: 3 events received
```

### 6. High-Risk Action
```
Orchestrator sends: APPROVAL_REQUESTED
  action: "Execute Privilege Escalation"
  riskLevel: "critical"
  
CLI displays full-screen approval panel:
  ⚠ APPROVAL REQUIRED
  Action: Execute Privilege Escalation
  Risk: ⚠ CRITICAL
  Command: exploit --target vulnerable_service...
  Target: domain_controller.internal
  Impact: Will attempt to extract Kerberos tickets...
  
  [Y] APPROVE    [N] REJECT
  Time: 5 minutes remaining
```

### 7. Operator Decides
```
User presses: [Y]
CLI sends: APPROVAL_RESPONSE(decision: "approve")
Orchestrator receives: Resumes agent with saved state
CLI displays: ✓ Action approved - Resuming operation
Metrics updated: approvalsGranted++
```

### 8. Agent Continues
```
Orchestrator sends: TOOL_INVOKED(kerberoasting)
Orchestrator sends: COMMAND_OUTPUT(kerberoast results)
Orchestrator sends: LEARNING_RECORDED(password_hash)
Orchestrator sends: AGENT_COMPLETED(success)

CLI updates:
  - Shows tool execution
  - Displays command output
  - Records learning
  - Shows agent completion
  - Updates metrics (6 events received)
```

### 9. Summary
```
Session ended
Total events: 6
Approvals: 1 granted, 0 rejected
Commands: 0 errors
Duration: 00:00:25
Vulnerabilities: 1 identified, 1 exploitable
```

## Security Considerations

### Authentication
- Session ID must be UUID v4 format
- Username identifies operator
- Server should validate both

### Authorization
- Only operator can approve/reject
- Server validates operator permissions
- Rejected actions should be logged

### Encryption
- Use `wss://` (WebSocket Secure) in production
- TLS 1.2+ required
- Certificate validation

### Audit Trail
- All events logged with timestamp
- All approval decisions recorded
- Operator identity logged
- Duration and outcome recorded

### Rate Limiting
- Heartbeat: every 30s
- Events: no limit (server enforces)
- Commands: 1 per second max
- Max event buffer: 10K

## Troubleshooting

### Connection Issues

**Problem**: "Failed to connect"
```
Solution:
1. Check orchestrator is running: ps aux | grep orchestrator
2. Verify URL: ws://localhost:9000
3. Check firewall rules
4. Verify network connectivity
```

**Problem**: "Connection dropped"
```
Solution:
1. Auto-reconnect with backoff (1s → 16s)
2. Check server logs for errors
3. Verify stable network
4. Check heartbeat (30s interval)
```

### Event Issues

**Problem**: "No events received"
```
Solution:
1. Verify agent is running
2. Check if events are being generated
3. Verify session ID matches
4. Check event buffer isn't full (10K max)
```

**Problem**: "Missing events"
```
Solution:
1. Events may have been older than buffer
2. Check event history export
3. Verify timestamp filters
4. Check connection stability
```

### Approval Issues

**Problem**: "Approval panel not showing"
```
Solution:
1. Check if approval request was received
2. Verify EventBus is broadcasting
3. Check component subscription
4. Verify message format
```

**Problem**: "Timeout auto-rejected"
```
Solution:
1. Default timeout is 5 minutes
2. Increase timeout: server config
3. Check clock synchronization
4. Verify operator response time
```

## Performance Tuning

### Reduce Memory Usage
```bash
# Limit event buffer
OrchestratorClient.MAX_EVENTS = 1000  # default 10000

# Reduce visible events
--max-visible 10  # default 20
```

### Improve Responsiveness
```bash
# Reduce debounce delay
OrchestratorClient.DEBOUNCE_MS = 50  # default 100

# Disable auto-scroll
--auto-scroll false
```

### Network Optimization
```bash
# Adjust heartbeat interval
OrchestratorClient.HEARTBEAT_INTERVAL = 60000  # default 30000

# Batch events
--batch-events true  # send multiple at once
```

## References

- CLI README: [../README.md](../README.md)
- Architecture Guide: [../ARCHITECTURE.md](../ARCHITECTURE.md)
- Type Definitions: [../src/types/](../src/types/)
- Client Implementation: [../src/client/](../src/client/)
