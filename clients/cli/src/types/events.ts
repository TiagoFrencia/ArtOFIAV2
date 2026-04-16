/**
 * Event Types & Contracts
 * Define all event structures that flow between Orchestrator and CLI
 */

export enum EventType {
  // Agent Lifecycle
  AGENT_STARTED = "agent:started",
  AGENT_COMPLETED = "agent:completed",
  AGENT_ERROR = "agent:error",

  // Tool Invocation
  TOOL_INVOKED = "tool:invoked",
  TOOL_COMPLETED = "tool:completed",
  TOOL_ERROR = "tool:error",

  // Recon Events
  SERVICE_DISCOVERED = "recon:service_discovered",
  VULNERABILITY_FOUND = "recon:vulnerability_found",
  TECHNOLOGY_IDENTIFIED = "recon:technology_identified",

  // Execution Events
  COMMAND_EXECUTED = "exec:command_executed",
  COMMAND_OUTPUT = "exec:command_output",
  COMMAND_ERROR = "exec:command_error",

  // Approval Events
  APPROVAL_REQUESTED = "approval:requested",
  APPROVAL_GRANTED = "approval:granted",
  APPROVAL_REJECTED = "approval:rejected",

  // System Events
  CONNECTION_ESTABLISHED = "system:connection_established",
  CONNECTION_LOST = "system:connection_lost",
  OPERATION_STARTED = "system:operation_started",
  OPERATION_COMPLETED = "system:operation_completed",

  // Learning Events
  LEARNING_RECORDED = "learning:recorded",
  TECHNIQUE_OPTIMIZED = "learning:technique_optimized",

  // Status Updates
  STATUS_UPDATE = "status:update",
  METRICS_UPDATE = "metrics:update",
}

export interface BaseEvent {
  id: string;
  type: EventType;
  timestamp: number;
  agentId?: string;
  sessionId: string;
}

// Agent Events
export interface AgentStartedEvent extends BaseEvent {
  type: EventType.AGENT_STARTED;
  agentName: string;
  stage: "reconnaissance" | "analysis" | "exploitation" | "learning";
  target?: string;
}

export interface AgentCompletedEvent extends BaseEvent {
  type: EventType.AGENT_COMPLETED;
  agentName: string;
  duration: number; // ms
  success: boolean;
  output?: Record<string, any>;
}

export interface AgentErrorEvent extends BaseEvent {
  type: EventType.AGENT_ERROR;
  agentName: string;
  error: string;
  stack?: string;
}

// Tool Events
export interface ToolInvokedEvent extends BaseEvent {
  type: EventType.TOOL_INVOKED;
  toolName: string;
  toolType: "sandbox" | "llm" | "network" | "infrastructure";
  parameters: Record<string, any>;
  riskLevel: "low" | "medium" | "high" | "critical";
}

export interface ToolCompletedEvent extends BaseEvent {
  type: EventType.TOOL_COMPLETED;
  toolName: string;
  output: Record<string, any>;
  duration: number;
}

export interface ToolErrorEvent extends BaseEvent {
  type: EventType.TOOL_ERROR;
  toolName: string;
  error: string;
}

// Recon Events
export interface ServiceDiscoveredEvent extends BaseEvent {
  type: EventType.SERVICE_DISCOVERED;
  service: {
    name: string;
    port: number;
    protocol: string;
    version?: string;
  };
}

export interface VulnerabilityFoundEvent extends BaseEvent {
  type: EventType.VULNERABILITY_FOUND;
  vulnerability: {
    id: string;
    name: string;
    severity: "low" | "medium" | "high" | "critical";
    cwe?: string;
    score?: number;
  };
}

export interface TechnologyIdentifiedEvent extends BaseEvent {
  type: EventType.TECHNOLOGY_IDENTIFIED;
  technology: {
    name: string;
    category: string;
    version?: string;
    confidence: number; // 0-100
  };
}

// Execution Events
export interface CommandExecutedEvent extends BaseEvent {
  type: EventType.COMMAND_EXECUTED;
  command: string;
  environment: "sandbox" | "host" | "remote";
  exitCode: number;
}

export interface CommandOutputEvent extends BaseEvent {
  type: EventType.COMMAND_OUTPUT;
  command: string;
  output: string;
  stream: "stdout" | "stderr";
}

// Approval Events
export interface ApprovalRequestedEvent extends BaseEvent {
  type: EventType.APPROVAL_REQUESTED;
  action: {
    id: string;
    description: string;
    riskLevel: "low" | "medium" | "high" | "critical";
    command?: string;
    impact?: string;
    context?: string;
  };
  timeout?: number; // seconds
  autoApproveIfTimeout?: boolean;
}

export interface ApprovalGrantedEvent extends BaseEvent {
  type: EventType.APPROVAL_GRANTED;
  approvalId: string;
  operator: string;
  reasoning?: string;
}

export interface ApprovalRejectedEvent extends BaseEvent {
  type: EventType.APPROVAL_REJECTED;
  approvalId: string;
  operator: string;
  reason: string;
}

// Status Events
export interface StatusUpdateEvent extends BaseEvent {
  type: EventType.STATUS_UPDATE;
  status: {
    sandbox: "ready" | "busy" | "error";
    llm: "ready" | "busy" | "error";
    learning: "ready" | "busy" | "error";
    agents: Record<string, "idle" | "running" | "paused" | "error">;
  };
}

export interface MetricsUpdateEvent extends BaseEvent {
  type: EventType.METRICS_UPDATE;
  metrics: {
    operationsCompleted: number;
    successRate: number;
    avgExecutionTime: number;
    techniquesLearned: number;
    lastUpdateTime: number;
  };
}

// Union type for all events
export type AnyEvent =
  | AgentStartedEvent
  | AgentCompletedEvent
  | AgentErrorEvent
  | ToolInvokedEvent
  | ToolCompletedEvent
  | ToolErrorEvent
  | ServiceDiscoveredEvent
  | VulnerabilityFoundEvent
  | TechnologyIdentifiedEvent
  | CommandExecutedEvent
  | CommandOutputEvent
  | ApprovalRequestedEvent
  | ApprovalGrantedEvent
  | ApprovalRejectedEvent
  | StatusUpdateEvent
  | MetricsUpdateEvent;

export interface EventStreamOptions {
  timeout?: number;
  autoReconnect?: boolean;
  maxRetries?: number;
}

export interface EventFilter {
  types?: EventType[];
  agentId?: string;
  riskLevel?: "low" | "medium" | "high" | "critical";
  timeRange?: {
    start: number;
    end: number;
  };
}
