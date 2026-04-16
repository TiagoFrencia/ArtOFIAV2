/**
 * Approval & Authorization Types
 * State-managed interruption contracts
 */

export enum ApprovalStatus {
  PENDING = "pending",
  APPROVED = "approved",
  REJECTED = "rejected",
  EXPIRED = "expired",
}

export enum ActionRiskLevel {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  CRITICAL = "critical",
}

export enum AuthorizationMethod {
  INTERACTIVE = "interactive", // User presses Y/N
  PASSWORD = "password", // Require password
  TOTP = "totp", // Time-based OTP
  BIOMETRIC = "biometric", // Fingerprint/facial
  NONE = "none", // Auto-approved
}

/**
 * Action classification for risk-based authorization
 */
export interface RiskAction {
  id: string;
  name: string;
  description: string;
  category:
    | "exploit_execution"
    | "data_modification"
    | "privilege_escalation"
    | "infrastructure_creation"
    | "network_access"
    | "authentication_bypass";
  riskLevel: ActionRiskLevel;
  command?: string;
  target?: string;
  impact?: string;
  context?: {
    target?: string;
    timeEstimate?: number;
    retryable?: boolean;
  };
}

/**
 * Approval request from orchestrator to CLI
 */
export interface ApprovalRequest {
  id: string; // Unique ID for this approval
  sessionId: string;
  action: RiskAction;
  requestedAt: number; // Timestamp
  timeout?: number; // Seconds until auto-expiry
  requiredMethod: AuthorizationMethod;
  requiresReasoning?: boolean; // User must provide reason for rejection
}

/**
 * User's response to approval request
 */
export interface ApprovalResponse {
  approvalId: string;
  decision: "approve" | "reject";
  operator: string; // Current terminal user
  timestamp: number;
  reasoning?: string; // Why they approved/rejected
  authMethod?: AuthorizationMethod;
}

/**
 * State saved when awaiting approval
 */
export interface InterruptionState {
  id: string;
  approvalRequest: ApprovalRequest;
  savedState: {
    agentState: Record<string, any>;
    agentMemory: Record<string, any>;
    context: Record<string, any>;
  };
  savedAt: number;
  expiresAt: number;
}

/**
 * History of approvals/rejections
 */
export interface ApprovalLog {
  approvalId: string;
  action: RiskAction;
  operator: string;
  decision: "approve" | "reject";
  reasoning?: string;
  timestamp: number;
  executedAt?: number; // When action was actually executed
  result?: "success" | "failure" | "error";
  errorMessage?: string;
}

/**
 * Risk policy configuration
 */
export interface RiskPolicy {
  riskLevel: ActionRiskLevel;
  requiresApproval: boolean;
  authMethod: AuthorizationMethod;
  timeout?: number;
  autoApproveIfTimeout?: boolean;
  categories?: string[];
}

/**
 * User profile for authorization
 */
export interface AuthorizedUser {
  id: string;
  username: string;
  role: "operator" | "lead" | "admin";
  permissions: {
    autoApproveLow: boolean;
    autoApproveMedium: boolean;
    autoApproveHigh: boolean;
    canRejectCritical: boolean;
  };
  auditLog: ApprovalLog[];
}
