# ArtOfIA CLI - Terminal User Interface

Professional Terminal User Interface (TUI) for ArtOfIA V2 - Real-time autonomous red team operation monitoring with state-managed human-in-the-loop approval system.

## Features

### 🎯 Core Capabilities

1. **Real-Time Operation Monitoring**
   - Live event stream from orchestrator
   - No browser context switching required
   - Full terminal-based visualization
   - Auto-scrolling event feed with filtering

2. **State-Managed Approval Interruption**
   - High-risk actions trigger automatic pause
   - Operator sees full context (command, target, impact)
   - Interactive Y/N decision interface
   - Auto-reject after timeout (5 minutes default)
   - Complete audit trail of all decisions

3. **Attack Surface Visualization**
   - Terminal-native graph rendering
   - Service discovery mapping
   - Vulnerability identification
   - Attack path visualization
   - Exploitability indicators

4. **Operational Metrics**
   - Event processing statistics
   - Approval acceptance rates
   - Command execution tracking
   - System health indicators
   - Real-time performance metrics

5. **Command Execution Tracking**
   - View command history
   - STDOUT/STDERR capture
   - Exit code tracking
   - Execution duration
   - Command output detail inspection

## Installation

```bash
npm install @artofIA/cli
```

Or clone and build:

```bash
git clone https://github.com/artofIA/artofIA-v2.git
cd clients/cli
npm install
npm run build
```

## Usage

### Basic Start

```bash
npx artofIA --orchestrator ws://localhost:9000 --username operator
```

### With Options

```bash
npx artofIA \
  --orchestrator ws://your-server:9000 \
  --session my-session-id \
  --username my-username
```

### Development Mode

```bash
npm run start:dev
```

## Architecture

### Component Hierarchy

```
App (main orchestrator)
├── Header (status, connection)
├── Dashboard (mode-based)
│   ├── OverviewMode
│   │   └── EventStreamPanel
│   ├── DetailedMode
│   │   ├── Tabs
│   │   ├── EventStreamPanel
│   │   ├── CommandOutputPanel
│   │   └── AttackGraphVisualizer
│   ├── GraphViewMode
│   │   ├── AttackGraphVisualizer
│   │   ├── VulnerabilityDetails
│   │   └── AttackPathsVisualizer
│   ├── MetricsMode
│   │   ├── MetricsDashboard
│   │   ├── MetricsChart
│   │   └── HealthStatus
│   └── ApprovalMode
│       └── ApprovalPanel (full-screen)
├── ApprovalOverlay (when approvals pending)
├── Notifications
└── Footer (shortcuts)
```

### Data Flow

```
OrchestratorClient (WebSocket)
        ↓ (receives events)
    EventBus (pub/sub)
        ↓ (broadcasts to components)
   Ink.js Components
        ↓ (user interactions)
    StateManager (global state)
        ↓ (notifies subscribers)
    Component Updates
        ↓ (sends decisions back)
    OrchestratorClient
        ↓ (to server)
```

### Type System

**Events** (`src/types/events.ts`)
- 15+ event types covering full operation lifecycle
- Type-safe discrimination with `AnyEvent` union

**Approvals** (`src/types/approval.ts`)
- Risk levels: low/medium/high/critical
- Authorization methods: interactive/password/TOTP/biometric
- Interruption state with context preservation

**UI State** (`src/types/ui.ts`)
- Dashboard modes: overview/detailed/graph/metrics/approval
- Vulnerability & attack surface structures
- Keyboard bindings configuration

## Keyboard Shortcuts

### Navigation

| Key | Action |
|-----|--------|
| `1-4` | Switch dashboard mode |
| `←/→` | Navigate tabs |
| `↑/↓` | Scroll lists |
| `Enter` | Select/expand |

### Approval Handling

| Key | Action |
|-----|--------|
| `Y` | Approve action |
| `N` | Reject action |
| `?` | Show context help |

### Operations

| Key | Action |
|-----|--------|
| `P` | Pause operation |
| `R` | Resume operation |
| `H` | Show help |
| `Q` | Quit application |

## Dashboard Modes

### 1. Overview Mode (`[1]`)
- Quick status at a glance
- Last 20 events
- Connection status
- Operational summary

### 2. Detailed Mode (`[2]`)
- Tabbed interface
- Full event stream (25 events)
- Command history
- Vulnerability details

### 3. Graph View Mode (`[3]`)
- Attack surface visualization
- Service discovery mapping
- Vulnerability locations
- Attack paths
- Expandable details

### 4. Metrics Mode (`[4]`)
- Event processing statistics
- Approval acceptance rates
- System resource usage
- Agent status indicators
- Performance charts

## Approval System

### How It Works

1. **Agent Decision**: Agent decides to perform high-risk action
2. **Orchestrator Pause**: Server freezes agent state and context
3. **CLI Interruption**: Event triggers approval panel
4. **Operator Input**: User sees action details and presses Y/N
5. **Decision Sent**: Response transmitted to orchestrator
6. **Agent Resume**: Agent continues with operator's directive

### Example Flow

```
[APPROVAL_REQUESTED event]
    ↓
    └─→ EventBus broadcasts
            ↓
            └─→ App detects pending approval
                    ↓
                    └─→ Shows ApprovalPanel overlay
                            ↓
                            └─→ Waits for Y/N
                                ↓
                                ├─→ [Y] Calls client.approveAction()
                                │       ↓
                                │       └─→ Sends ApprovalResponse
                                │
                                └─→ [N] Calls client.rejectAction()
                                        ↓
                                        └─→ Sends rejection reason
```

## Components

### Base Components (`src/components/Base.tsx`)
- `BorderedBox` - Container with borders
- `StyledText` - Colored/styled text
- `StatusIndicator` - Connection status
- `Badge` - Small labels
- `ProgressBar` - Progress visualization
- `LoadingSpinner` - Activity indicator
- `Alert` - Alert messages
- `Table` - Data table display
- `Menu` - Selectable menu

### Panels

**ApprovalPanel** (`src/components/ApprovalPanel.tsx`)
- Displays action details
- Risk level visualization
- Impact assessment
- Countdown timer
- Interactive Y/N interface

**EventStreamPanel** (`src/components/EventStreamPanel.tsx`)
- Real-time event feed
- Event filtering
- Auto-scroll
- Event statistics
- Detailed event inspection

**AttackGraphVisualizer** (`src/components/AttackGraphVisualizer.tsx`)
- Terminal graph rendering
- Service mapping
- Vulnerability details
- Attack paths visualization
- Expandable nodes

**MetricsDashboard** (`src/components/MetricsDashboard.tsx`)
- Real-time statistics
- Progress charts
- System health
- Agent status
- Performance metrics

**CommandOutputPanel** (`src/components/CommandOutputPanel.tsx`)
- Command history
- STDOUT/STDERR display
- Execution progress
- Live log streaming

## Utilities

### Hooks (`src/utils/hooks.ts`)
- `useOrchestratorConnection()` - WebSocket management
- `useEventStream()` - Real-time events
- `useEventBus()` - Pub/sub subscription
- `useAppState()` - Global state
- `useApprovalHandling()` - Approval flow
- `useKeyboardInput()` - Keyboard handling

### Helpers (`src/utils/helpers.ts`)
- `EventHelpers` - Event manipulation
- `StateHelpers` - State queries
- `RiskHelpers` - Risk assessment
- `DataHelpers` - Data transformation
- `InputHelpers` - Input processing
- `StyleHelpers` - Text styling

### Validators (`src/utils/validators.ts`)
- Input validation
- Risk assessment validation
- JSON/Email/IP validation
- Shell safety checks
- Schema validation

### Formatters (`src/utils/formatters.ts`)
- Terminal-aware formatting
- Time/duration formatting
- Event-specific formatting
- Syntax highlighting

## Configuration

Environment variables:

```bash
# Orchestrator connection
ARTOFCIA_ORCHESTRATOR=ws://localhost:9000
ARTOFCIA_SESSION_ID=my-session
ARTOFCIA_USERNAME=operator

# Terminal settings
ARTOFCIA_THEME=default
ARTOFCIA_AUTO_SCROLL=true

# Approval settings
ARTOFCIA_APPROVAL_TIMEOUT=300
ARTOFCIA_REQUIRE_REASONING=false
```

## Development

### Build

```bash
npm run build
```

### Watch Mode

```bash
npm run dev
```

### Lint

```bash
npm run lint
```

### Format

```bash
npm run format
```

### Test

```bash
npm test
```

## Performance

- **Event Buffer**: 10,000 max events
- **Visible Events**: 15-25 per screen (configurable)
- **Refresh Rate**: Real-time + 100ms debounce
- **Memory**: ~50-100MB typical
- **CPU**: <5% idle, <20% during operations

## Troubleshooting

### Connection Issues

```bash
# Verify orchestrator is running
curl ws://localhost:9000/health

# Check session ID format (UUID v4)
artofIA --session invalid-id --username test
```

### Terminal Compatibility

Requires:
- Terminal width ≥ 80 columns
- Terminal height ≥ 24 rows
- ANSI color support
- UTF-8 encoding

### Performance

If slow:
1. Reduce max visible events: `--max-events 10`
2. Disable auto-scroll: `--auto-scroll false`
3. Check system resources

## Architecture Decisions

### Why Ink.js?
- React-based → familiar patterns
- Real-time rendering → responsive UI
- Terminal-native → no browser overhead
- Composable components → maintainable

### Why WebSockets?
- Bi-directional communication
- Low latency for real-time events
- Persistent connection for approvals
- Standard protocol → compatible

### Why Event-Based?
- Decoupled components (no prop drilling)
- Scalable to many subscribers
- Natural for async operations
- Easy to test and debug

## Future Enhancements

- [ ] Graph visualization with `ink-chart`
- [ ] Multi-pane layout manager
- [ ] Plugin system for custom commands
- [ ] Dark/light theme support
- [ ] Session recording & playback
- [ ] Integration with systemd/supervisord
- [ ] Remote session connections
- [ ] Multi-user collaboration mode

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md)

## License

MIT - See [LICENSE](../../LICENSE)

## Support

- 📧 Email: support@artofIA.dev
- 💬 Discord: https://discord.gg/artofIA
- 🐛 Issues: https://github.com/artofIA/artofIA-v2/issues
