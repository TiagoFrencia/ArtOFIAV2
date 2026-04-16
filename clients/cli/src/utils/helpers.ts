/**
 * Helper utilities for common TUI operations
 */

import { AnyEvent, EventType } from "../types/events";
import { ApprovalStatus, ActionRiskLevel, RiskAction } from "../types/approval";
import { UIState, DashboardMode } from "../types/ui";

/**
 * Event helper utilities
 */
export class EventHelpers {
  /**
   * Group events by agent
   */
  static groupByAgent(events: AnyEvent[]): Map<string, AnyEvent[]> {
    const map = new Map<string, AnyEvent[]>();

    for (const event of events) {
      const agentId = (event as any).agentId || "unknown";
      if (!map.has(agentId)) {
        map.set(agentId, []);
      }
      map.get(agentId)!.push(event);
    }

    return map;
  }

  /**
   * Group events by type
   */
  static groupByType(events: AnyEvent[]): Map<EventType, AnyEvent[]> {
    const map = new Map<EventType, AnyEvent[]>();

    for (const event of events) {
      if (!map.has(event.type)) {
        map.set(event.type, []);
      }
      map.get(event.type)!.push(event);
    }

    return map;
  }

  /**
   * Get events within time range
   */
  static getEventsInRange(
    events: AnyEvent[],
    startTime: Date,
    endTime: Date
  ): AnyEvent[] {
    return events.filter((e) => {
      const time = e.timestamp.getTime();
      return time >= startTime.getTime() && time <= endTime.getTime();
    });
  }

  /**
   * Get latest N events
   */
  static getLatestN(events: AnyEvent[], n: number): AnyEvent[] {
    return events.slice(Math.max(0, events.length - n));
  }

  /**
   * Count events by type
   */
  static countByType(events: AnyEvent[]): Record<EventType, number> {
    const counts: Record<EventType, number> = {} as any;

    for (const event of events) {
      counts[event.type] = (counts[event.type] || 0) + 1;
    }

    return counts;
  }

  /**
   * Filter events with custom predicate
   */
  static filter(events: AnyEvent[], predicate: (e: AnyEvent) => boolean) {
    return events.filter(predicate);
  }

  /**
   * Get events for specific agent in time range
   */
  static getAgentEventsInRange(
    events: AnyEvent[],
    agentId: string,
    startTime: Date,
    endTime: Date
  ): AnyEvent[] {
    return events.filter((e) => {
      const isAgent = (e as any).agentId === agentId;
      const inRange =
        e.timestamp.getTime() >= startTime.getTime() &&
        e.timestamp.getTime() <= endTime.getTime();
      return isAgent && inRange;
    });
  }
}

/**
 * State helper utilities
 */
export class StateHelpers {
  /**
   * Check if UI is in approval mode
   */
  static isInApprovalMode(uiState: UIState): boolean {
    return uiState.mode === "approval";
  }

  /**
   * Check if operation is paused
   */
  static isOperationPaused(sessionState: any): boolean {
    return sessionState?.isPaused === true;
  }

  /**
   * Check if connected
   */
  static isConnected(sessionState: any): boolean {
    return sessionState?.status === "connected";
  }

  /**
   * Get total notifications
   */
  static getNotificationCount(notifications: any[]): number {
    return notifications?.length || 0;
  }

  /**
   * Get error notifications
   */
  static getErrorNotifications(notifications: any[]): any[] {
    return notifications?.filter((n) => n.type === "error") || [];
  }

  /**
   * Duration since operation started
   */
  static getOperationDuration(startedAt: Date | null): number {
    if (!startedAt) return 0;
    return Date.now() - startedAt.getTime();
  }
}

/**
 * Risk assessment helpers
 */
export class RiskHelpers {
  /**
   * Determine risk level from severity
   */
  static getSeverityToRisk(severity: string): ActionRiskLevel {
    switch (severity?.toLowerCase()) {
      case "critical":
      case "very_high":
        return "critical";
      case "high":
        return "high";
      case "medium":
      case "moderate":
        return "medium";
      default:
        return "low";
    }
  }

  /**
   * Get color for risk level
   */
  static getRiskColor(level: ActionRiskLevel): string {
    switch (level) {
      case "critical":
        return "\x1b[41m\x1b[37m"; // Red bg, white text
      case "high":
        return "\x1b[91m"; // Bright red
      case "medium":
        return "\x1b[93m"; // Bright yellow
      case "low":
        return "\x1b[92m"; // Bright green
      default:
        return "\x1b[0m"; // Reset
    }
  }

  /**
   * Check if action needs approval
   */
  static needsApproval(action: RiskAction): boolean {
    return ["medium", "high", "critical"].includes(action.riskLevel);
  }

  /**
   * Suggest approval method
   */
  static suggestApprovalMethod(riskLevel: ActionRiskLevel): string {
    switch (riskLevel) {
      case "critical":
        return "biometric";
      case "high":
        return "totp";
      case "medium":
        return "password";
      case "low":
        return "interactive";
      default:
        return "interactive";
    }
  }

  /**
   * Estimate action impact
   */
  static estimateImpact(action: RiskAction): string {
    if (action.category?.includes("privilege_escalation")) {
      return "High: Privilege escalation detected";
    }
    if (action.category?.includes("data_modification")) {
      return "Critical: Data modification";
    }
    if (action.category?.includes("infrastructure_creation")) {
      return "Medium: New resources created";
    }
    return "Low: Reconnaissance only";
  }
}

/**
 * Data transformation helpers
 */
export class DataHelpers {
  /**
   * Convert bytes to readable format
   */
  static bytesToReadable(bytes: number): string {
    const units = ["B", "KB", "MB", "GB", "TB"];
    let size = bytes;
    let unitIndex = 0;

    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }

    return `${size.toFixed(2)} ${units[unitIndex]}`;
  }

  /**
   * Convert milliseconds to readable duration
   */
  static msToReadable(ms: number): string {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    }
    if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
  }

  /**
   * Paginate array
   */
  static paginate<T>(array: T[], page: number, pageSize: number): T[] {
    const start = page * pageSize;
    return array.slice(start, start + pageSize);
  }

  /**
   * Deep clone object
   */
  static deepClone<T>(obj: T): T {
    if (obj === null || typeof obj !== "object") {
      return obj;
    }

    if (obj instanceof Date) {
      return new Date(obj.getTime()) as any;
    }

    if (obj instanceof Array) {
      return obj.map((item) => this.deepClone(item)) as any;
    }

    if (obj instanceof Object) {
      const cloned = {} as T;
      for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
          cloned[key] = this.deepClone(obj[key]);
        }
      }
      return cloned;
    }

    return obj;
  }

  /**
   * Flatten nested object
   */
  static flatten(obj: any, prefix = ""): Record<string, any> {
    const flattened: Record<string, any> = {};

    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        const value = obj[key];
        const newKey = prefix ? `${prefix}.${key}` : key;

        if (value !== null && typeof value === "object" && !Array.isArray(value)) {
          Object.assign(flattened, this.flatten(value, newKey));
        } else {
          flattened[newKey] = value;
        }
      }
    }

    return flattened;
  }
}

/**
 * Keyboard input helpers
 */
export class InputHelpers {
  /**
   * Key name to action
   */
  static keyToAction(key: string): string | null {
    const keyMap: Record<string, string> = {
      y: "approve",
      n: "reject",
      p: "pause",
      r: "resume",
      q: "quit",
      h: "help",
      k: "scroll_up",
      j: "scroll_down",
      f: "find",
      c: "clear",
    };
    return keyMap[key?.toLowerCase()] || null;
  }

  /**
   * Is valid yes/no input
   */
  static isYesNo(input: string): boolean {
    return ["y", "yes", "n", "no"].includes(input.toLowerCase());
  }

  /**
   * Parse yes/no input
   */
  static parseYesNo(input: string): boolean {
    return ["y", "yes"].includes(input.toLowerCase());
  }

  /**
   * Escape shell input
   */
  static escapeShell(str: string): string {
    return `'${str.replace(/'/g, "'\\''")}'`;
  }

  /**
   * Highlight search term in text
   */
  static highlight(text: string, term: string, color = "\x1b[33m"): string {
    const regex = new RegExp(`(${term})`, "gi");
    return text.replace(regex, `${color}$1\x1b[0m`);
  }
}

/**
 * Format/Style helpers
 */
export class StyleHelpers {
  /**
   * Create colored text
   */
  static colorize(text: string, color: "red" | "green" | "yellow" | "blue" | "magenta" | "cyan"): string {
    const colors: Record<string, string> = {
      red: "\x1b[91m",
      green: "\x1b[92m",
      yellow: "\x1b[93m",
      blue: "\x1b[94m",
      magenta: "\x1b[95m",
      cyan: "\x1b[96m",
    };
    return `${colors[color]}${text}\x1b[0m`;
  }

  /**
   * Bold text
   */
  static bold(text: string): string {
    return `\x1b[1m${text}\x1b[22m`;
  }

  /**
   * Dim text
   */
  static dim(text: string): string {
    return `\x1b[2m${text}\x1b[22m`;
  }

  /**
   * Italic text
   */
  static italic(text: string): string {
    return `\x1b[3m${text}\x1b[23m`;
  }

  /**
   * Create border box
   */
  static box(text: string, padding = 1): string {
    const lines = text.split("\n");
    const maxWidth = Math.max(...lines.map((l) => l.length));
    const padStr = " ".repeat(padding);
    const borderLine = "─".repeat(maxWidth + padding * 2 + 2);

    const result: string[] = [];
    result.push("┌" + borderLine + "┐");

    for (let i = 0; i < padding; i++) {
      result.push("│" + " ".repeat(maxWidth + padding * 2 + 2) + "│");
    }

    for (const line of lines) {
      result.push("│" + padStr + line.padEnd(maxWidth) + padStr + "│");
    }

    for (let i = 0; i < padding; i++) {
      result.push("│" + " ".repeat(maxWidth + padding * 2 + 2) + "│");
    }

    result.push("└" + borderLine + "┘");

    return result.join("\n");
  }

  /**
   * Create horizontal line
   */
  static line(width: number, char = "─"): string {
    return char.repeat(width);
  }
}

/**
 * Export all helpers
 */
export const Helpers = {
  Event: EventHelpers,
  State: StateHelpers,
  Risk: RiskHelpers,
  Data: DataHelpers,
  Input: InputHelpers,
  Style: StyleHelpers,
};
