# ArtOfIA CLI - Architecture Documentation

## Overview

The ArtOfIA CLI is a professional Terminal User Interface (TUI) built with React (Ink.js) that provides real-time monitoring and state-managed approval for autonomous red team operations.

## Design Principles

1. **Type Safety First** - All data typed, no `any`
2. **Separation of Concerns** - Clear boundaries between layers
3. **Reactive Architecture** - Event-driven updates
4. **Human-in-the-Loop** - Operator control and awareness
5. **Performance** - Real-time with minimal overhead

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Terminal UI Layer                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Ink.js Components                   │   │
│  │  ┌─────────────────────────────────────────────┐ │   │
│  │  │ App Component (Orchestrator)                │ │   │
│  │  │  - Dashboard mode routing                   │ │   │
│  │  │  - Keyboard handling                        │ │   │
│  │  │  - Notification queue                       │ │   │
│  │  └─────────────────────────────────────────────┘ │   │
│  │  ┌─────────────────────────────────────────────┐ │   │
│  │  │ Modal Components (Approval, Commands)       │ │   │
│  │  │  - Interactive dialogs                      │ │   │
│  │  │  - Event-driven display                     │ │   │
│  │  └─────────────────────────────────────────────┘ │   │
│  │  ┌─────────────────────────────────────────────┐ │   │
│  │  │ Panel Components (Events, Metrics, Graphs)  │ │   │
│  │  │  - Real-time updates                        │ │   │
│  │  │  - Scrollable views                         │ │   │
│  │  └─────────────────────────────────────────────┘ │   │
│  │  ┌─────────────────────────────────────────────┐ │   │
│  │  │ Base Components (Boxes, Badges, Tables)    │ │   │
│  │  │  - Reusable primitives                      │ │   │
│  │  │  - Styled elements                          │ │   │
│  │  └─────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
             ↑                        ↓
        useInput()              Component props
             ↑                        ↓
┌─────────────────────────────────────────────────────────┐
│                  State Management Layer                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │           StateManager (Global State)            │   │
│  │  ┌─────────────────────────────────────────────┐ │   │
│  │  │ AppState                                    │ │   │
│  │  │ - UI state (mode, tabs, scroll)             │ │   │
│  │  │ - Session state (connected, paused)         │ │   │
│  │  │ - Metrics (events, approvals, commands)     │ │   │
│  │  │ - Notifications queue                       │ │   │
│  │  └─────────────────────────────────────────────┘ │   │
│  │  Partial subscriptions: Only notify listeners    │   │
│  │  for specific keys they care about              │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │        EventBus (Pub/Sub System)                │   │
│  │  - Global event stream                          │   │
│  │  - Event history buffer (10K max)               │   │
│  │  - Per-type subscriptions                       │   │
│  │  - Statistics tracking                          │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
             ↑                        ↓
        subscribe()          emit/on listeners
             ↑                        ↓
┌─────────────────────────────────────────────────────────┐
│                Communication Layer                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │     OrchestratorClient (WebSocket)              │   │
│  │  ┌─────────────────────────────────────────────┐ │   │
│  │  │ Connection Management                       │ │   │
│  │  │ - WebSocket connect/disconnect              │ │   │
│  │  │ - Auto-reconnect with backoff               │ │   │
│  │  │ - Heartbeat monitoring                      │ │   │
│  │  └─────────────────────────────────────────────┘ │   │
│  │  ┌─────────────────────────────────────────────┐ │   │
│  │  │ Message Routing                             │ │   │
│  │  │ - Event → EventBus                          │ │   │
│  │  │ - ApprovalRequest → Pending queue           │ │   │
│  │  │ - Response → Send back to server            │ │   │
│  │  └─────────────────────────────────────────────┘ │   │
│  │  ┌─────────────────────────────────────────────┐ │   │
│  │  │ Command Execution                           │ │   │
│  │  │ - Promise-based with timeout                │ │   │
│  │  │ - Custom command support                    │ │   │
│  │  └─────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
             ↑                        ↓
        send(message)         receive/parse
             ↑                        ↓
┌─────────────────────────────────────────────────────────┐
│              Network (Orchestrator Server)              │
└─────────────────────────────────────────────────────────┘
```

## Layer Descriptions

### 1. Terminal UI Layer (Ink.js Components)

**Purpose**: Visual rendering and user interaction

**Components**:
- **App**: Main orchestrator, routes between modes
- **Modal Components**: ApprovalPanel, CommandOutputPanel
- **Panel Components**: EventStreamPanel, MetricsDashboard, AttackGraphVisualizer
- **Base Components**: BorderedBox, Badge, ProgressBar, Table, Menu

**Data Flow**:
```
User Input (keyboard)
    ↓
useInput() hook
    ↓
Event handler (dispatch to StateManager)
    ↓
StateManager updates
    ↓
Subscribed component updates
    ↓
Ink.js re-renders
    ↓
Terminal output
```

### 2. State Management Layer

**Purpose**: Single source of truth for application state

**Components**:

#### StateManager
- Maintains complete AppState
- Partial subscriptions (only notify on key changes)
- Automatic notification expiry
- Snapshot/restore for recovery
- Metrics accumulation

```typescript
AppState = {
  ui: {mode, tab, scroll, filters, loading},
  session: {id, user, connected, paused},
  operation: {stage, target, started, completed, error},
  metrics: {events, commands, approvals},
  notifications: [{id, type, message, timestamp}]
}
```

#### EventBus
- Global pub/sub for events from orchestrator
- Event history buffer (max 10K)
- Per-type subscriptions
- Statistics tracking
- Singleton pattern

**Subscription Pattern**:
```
StateManager.subscribe('ui', (newUI) => setUI(newUI))
  Only triggered when ui key changes
  
EventBus.onType(EVENT_TYPE.APPROVAL_REQUESTED, (event) => {})
  Only triggered for specific event types
```

### 3. Communication Layer (OrchestratorClient)

**Purpose**: WebSocket management and message routing

**Responsibilities**:
- Establish/maintain connection to orchestrator
- Auto-reconnect with exponential backoff
- Buffer events during disconnection
- Route messages to appropriate handlers
- Handle approval requests specially
- Execute commands with timeout

**Architecture**:
```
Connection Lifecycle:
  connect() 
    → send handshake {sessionId, username}
    → listen for messages
    → heartbeat every 30s
    → auto-reconnect on failure (1s, 2s, 4s, 8s, 16s max)

Message Routing:
  {type: 'event', data: AnyEvent}
    → _recordEvent()
    → emit('event') + emit(`event:${type}`)
    
  {type: 'approval_request', data: ApprovalRequest}
    → storeInPendingQueue()
    → emit('approval_requested')
    
  {type: 'heartbeat'}
    → updateLastHeartbeat()
    → respond with heartbeat
```

## Data Flow Examples

### Example 1: Real-Time Event Display

```
1. orchestrator sends: {type: 'event', data: AgentStartedEvent}
2. OrchestratorClient receives WebSocket message
3. Calls handleMessage() → handleEvent(event)
4. Records to buffer: messages.push(event)
5. Emits: eventEmitter.emit('event', event)
           eventEmitter.emit('event:AGENT_STARTED', event)
6. EventBus receives and broadcasts
7. EventStreamPanel subscribed via useEventBus()
8. Component state updates: setEvents(prev => [...prev, event])
9. Ink.js re-renders with new event
10. Terminal output updates
```

### Example 2: Approval Interruption

```
1. Agent attempts high-risk action
2. orchestrator freezes agent state
3. ortchestrator sends: {type: 'approval_request', data: ApprovalRequest}
4. OrchestratorClient receives
5. Calls handleApprovalRequest(request)
6. Stores: pendingApprovals.set(request.id, request)
7. Emits: EventBus broadcasts ApprovalRequestedEvent
8. App component receives event via useApprovalHandling()
9. Sets state: setApprovals([request])
10. App re-renders with ApprovalPanel overlay
11. User sees action details and decides
12. Presses [Y] → presses approveAction(id)
13. OrchestratorClient sends: {decision: 'approve', id, reasoning}
14. orchestrator resumes agent with approval
15. Agent continues
16. Operation completes
17. orchestrator sends CompletedEvent
18. Full cycle logged and visible in CLI
```

### Example 3: Dashboard Mode Switch

```
1. User presses [2] key
2. useInput() intercepts: setDashboardMode('detailed')
3. StateManager.setDashboardMode('detailed')
4. Updates AppState.ui.mode = 'detailed'
5. Notifies subscribers to 'ui' key
6. App component receives update via useAppState()
7. App re-renders with different layout
8. User sees new dashboard
9. Tabs component appears with [←→] navigation
10. User can switch between Events/Commands/Vulnerabilities
11. Each tab loads different subset of data from state
```

## Type System Architecture

```
src/types/
├── events.ts
│   ├── EventType (enum)
│   │   ├── AGENT_STARTED, AGENT_COMPLETED, AGENT_ERROR
│   │   ├── TOOL_INVOKED, TOOL_COMPLETED, TOOL_ERROR
│   │   ├── SERVICE_DISCOVERED, VULNERABILITY_FOUND
│   │   ├── APPROVAL_REQUESTED, APPROVAL_GRANTED, APPROVAL_REJECTED
│   │   └── [15 total event types]
│   │
│   ├── BaseEvent (interface)
│   │   ├── type: EventType
│   │   ├── timestamp: Date
│   │   └── data?: unknown
│   │
│   ├── Specific Events
│   │   ├── AgentStartedEvent extends BaseEvent
│   │   ├── VulnerabilityFoundEvent extends BaseEvent
│   │   ├── ApprovalRequestedEvent extends BaseEvent
│   │   └── [10 more specific types]
│   │
│   └── AnyEvent (union type)
│       Discriminated union for type-safe event handling
│
├── approval.ts
│   ├── ApprovalStatus (enum)
│   │   ├── pending, approved, rejected, expired
│   │
│   ├── ActionRiskLevel (enum)
│   │   ├── low, medium, high, critical
│   │
│   ├── RiskAction (interface)
│   │   ├── id, name, description, category, riskLevel
│   │   ├── command, target, impact
│   │   └── context: {target, timeEstimate, retryable}
│   │
│   ├── ApprovalRequest (interface)
│   │   ├── id, sessionId, action
│   │   ├── requestedAt, timeout, requiredMethod
│   │   └── requiresReasoning
│   │
│   ├── ApprovalResponse (interface)
│   │   ├── decision: "approve" | "reject"
│   │   ├── operator, timestamp, reasoning
│   │
│   ├── InterruptionState (interface)
│   │   ├── savedState: {agentState, memory, context}
│   │   ├── savedAt, expiresAt
│   │
│   └── [RiskPolicy, AuthorizedUser, etc.]
│
└── ui.ts
    ├── DashboardMode (enum)
    │   ├── overview, detailed, graph_view, metrics, approval
    │
    ├── UIState (interface)
    │   ├── mode, selectedTab, focusedElement
    │   ├── scrollPosition, isPaused
    │   ├── filters: EventFilter
    │   └── loading: LoadingState
    │
    ├── Visualization Types
    │   ├── Vulnerability:
    │   │   ├── id, name, severity, cwe, cvss
    │   │   ├── discovered, exploitable, exploitPath
    │   │
    │   ├── Service:
    │   │   ├── name, port, protocol, version
    │   │   ├── technology, vulnerabilities[]
    │   │
    │   ├── AttackPath:
    │   │   ├── id, name, stages[], success_rate
    │   │
    │   └── AttackSurface:
    │       ├── id, services[], vulnerabilities[]
    │       └── attackPaths[]
    │
    └── [ChartData, KeyBindings, Colors, etc.]
```

## Performance Considerations

### Memory Management
- Event buffer capped at 10K
- Visible events limited to 15-25
- Auto-cleanup of expired notifications (5s default)
- Snapshot/restore for state recovery

### Rendering Optimization
- Partial subscriptions (only re-render on relevant changes)
- Debounced keyboard input (100ms)
- Lazy component rendering (only render visible tabs)
- Virtualized lists for large datasets (future)

### Network Efficiency
- WebSocket reuse (single persistent connection)
- Heartbeat every 30 seconds
- Event buffering during disconnection
- Automatic reconnection with backoff

### CPU Usage
- Real-time updates: ~100ms debounce
- Event processing: O(1) insertion into buffer
- State updates: O(subscribers to key) notification
- Rendering: Only changed components

**Typical Resource Usage**:
- Memory: 50-100 MB
- CPU: <5% idle, <20% during operations
- Network: <1 KB/s at rest, 10-50 KB/s during activity

## Extensibility Points

### 1. Custom Commands
```typescript
// Add new command type
client.executeCommand('custom_cmd', ['arg1', 'arg2'])
  .then(result => /* handle result */)
```

### 2. Custom Hooks
```typescript
// Create domain-specific hook
export function useVulnerabilityTracking() {
  const bus = getEventBus();
  const [vulns, setVulns] = useState([]);
  
  useEffect(() => {
    bus.onType('VULNERABILITY_FOUND', (event) => {
      setVulns(prev => [...prev, event.data.vulnerability])
    });
  }, []);
  
  return vulns;
}
```

### 3. Custom Components
```typescript
// Create custom panel
function MyCustomPanel() {
  const events = useEventBus();
  return <BorderedBox title="Custom">{/* render events */}</BorderedBox>
}
```

### 4. Remote Sessions
```typescript
// Connect to different orchestrator
const { client } = useOrchestratorConnection({
  orchestratorUrl: 'ws://remote-server:9000',
  sessionId: 'remote-session',
  username: 'remote-user'
})
```

## Testing Strategy

### Unit Tests
- Validators (input/output)
- Helpers (transformation logic)
- Hooks (state management)
- Formatters (output consistency)

### Component Tests
- Base components (rendering)
- Panels (event subscription)
- Modal components (interaction)
- App component (orchestration)

### Integration Tests
- Client ↔ EventBus
- EventBus ↔ StateManager
- Components ↔ State subscriptions
- App ↔ All layers

### E2E Tests
- With mock orchestrator
- Real approval flow
- Mode switching
- Keyboard interaction

## Future Enhancements

1. **Multi-Pane Layout**
   - Side-by-side panels
   - Resizable windows
   - Custom layouts

2. **Advanced Visualization**
   - Colored graphs (ink-chart)
   - 3D ASCII art
   - Mathematical plots

3. **Session Management**
   - Save/restore sessions
   - Session playback
   - Multi-user collaboration

4. **Plugin System**
   - Custom command modules
   - Custom visualization plugins
   - Custom formatter plugins

5. **Performance**
   - Virtualized lists (1000+ items)
   - Worker threads for heavy lifting
   - Incremental rendering

## Deployment

### Development
```bash
npm run start:dev
```

### Production Build
```bash
npm run build
npm install -g .
artofIA --orchestrator ws://prod-server:9000
```

### Docker
```dockerfile
FROM node:18
WORKDIR /app
COPY . .
RUN npm install && npm run build
CMD ["npm", "start"]
```

## References

- **Ink.js**: https://github.com/vadimdemedes/ink
- **React Hooks**: https://react.dev/reference/react/hooks
- **TypeScript**: https://www.typescriptlang.org/
- **WebSocket**: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
