/**
 * UI & Dashboard Types for Ink.js Components
 */

export enum DashboardMode {
  OVERVIEW = "overview",
  DETAILED = "detailed",
  GRAPH_VIEW = "graph_view",
  METRICS = "metrics",
  APPROVAL = "approval",
  COMMAND_OUTPUT = "command_output",
}

export interface UIState {
  mode: DashboardMode;
  selectedTab: string;
  focusedElement?: string;
  scrollPosition: number;
  isPaused: boolean;
  filters: EventFilter;
}

export interface EventFilter {
  agentId?: string;
  riskLevel?: string;
  eventType?: string;
  timeRange?: {
    start: number;
    end: number;
  };
}

/**
 * Vulnerability for visualization
 */
export interface Vulnerability {
  id: string;
  name: string;
  severity: "low" | "medium" | "high" | "critical";
  cwe?: string;
  cvss?: number;
  discovered: number;
  exploitable: boolean;
  exploitPath?: string[];
}

/**
 * Attack surface visualization
 */
export interface AttackSurface {
  id: string;
  services: Service[];
  vulnerabilities: Vulnerability[];
  attackPaths: AttackPath[];
}

export interface Service {
  id: string;
  name: string;
  port: number;
  protocol: string;
  version?: string;
  technology: string;
  vulnerabilities: string[]; // IDs
}

export interface AttackPath {
  id: string;
  name: string;
  stages: [
    {
      step: number;
      technique: string;
      service: string;
      likelihood: number;
    }
  ];
  success_rate: number;
}

/**
 * Chart data for visualization
 */
export interface ChartData {
  title: string;
  data: ChartPoint[];
  legend?: string[];
  min?: number;
  max?: number;
}

export interface ChartPoint {
  label: string;
  value: number;
  color?: "red" | "green" | "yellow" | "blue" | "cyan" | "magenta";
}

/**
 * Terminal dimensions
 */
export interface TerminalDimensions {
  width: number;
  height: number;
  rows: number;
  cols: number;
}

/**
 * Panel configuration
 */
export interface PanelConfig {
  title: string;
  width: number;
  height: number;
  scrollable?: boolean;
  bordered?: boolean;
  color?: "red" | "green" | "yellow" | "blue" | "cyan" | "magenta" | "white";
}

/**
 * Color scheme
 */
export const ColorScheme = {
  // Status colors
  success: "#00FF00",
  error: "#FF0000",
  warning: "#FFFF00",
  info: "#00FFFF",

  // Risk colors
  lowRisk: "#00FF00",
  mediumRisk: "#FFFF00",
  highRisk: "#FF8800",
  criticalRisk: "#FF0000",

  // UI colors
  header: "#00CCFF",
  border: "#00FFFF",
  text: "#FFFFFF",
  dimText: "#888888",
};

/**
 * Keyboard input configuration
 */
export enum KeyboardAction {
  APPROVE = "y",
  REJECT = "n",
  PAUSE = "p",
  RESUME = "r",
  QUIT = "q",
  HELP = "h",
  SCROLL_UP = "k",
  SCROLL_DOWN = "j",
  FILTER = "f",
  CLEAR_SCREEN = "c",
}

export interface KeyBindings {
  approve: string;
  reject: string;
  pause: string;
  resume: string;
  quit: string;
  help: string;
  scrollUp: string;
  scrollDown: string;
  filter: string;
  clearScreen: string;
}

/**
 * Message for inter-component communication
 */
export interface UIMessage {
  id: string;
  type: "info" | "success" | "warning" | "error" | "approval";
  content: string;
  details?: string;
  action?: {
    label: string;
    callback: () => void;
  };
  createdAt: number;
  expiresAt?: number;
  cta?: string; // Call-to-action button
}

/**
 * Loading state
 */
export interface LoadingState {
  isLoading: boolean;
  progress?: number;
  message?: string;
}

/**
 * Notification queue
 */
export interface NotificationQueue {
  messages: UIMessage[];
  add(message: UIMessage): void;
  remove(id: string): void;
  clear(): void;
  getVisible(): UIMessage[];
}
