/**
 * Central exports for all Ink.js components
 */

// Base components
export {
  BorderedBox,
  StyledText,
  StatusIndicator,
  Badge,
  ProgressBar,
  LoadingSpinner,
  Divider,
  Tabs,
  Alert,
  KeyBindingsHelp,
  Table,
  Menu,
} from "./Base";

// Approval panel
export { ApprovalPanel, ApprovalQueue } from "./ApprovalPanel";

// Event stream
export { EventStreamPanel, EventSummary, EventDetails } from "./EventStreamPanel";

// Attack graph
export {
  AttackGraphVisualizer,
  VulnerabilityDetails,
  AttackPathsVisualizer,
} from "./AttackGraphVisualizer";

// Metrics
export {
  MetricsDashboard,
  MetricsChart,
  HealthStatus,
} from "./MetricsDashboard";

// Command output
export {
  CommandOutputPanel,
  CommandHistory,
  LiveLog,
  CommandProgress,
} from "./CommandOutputPanel";
