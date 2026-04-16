/**
 * Formatting utilities for terminal output
 */

import { AnyEvent, EventType } from "../types/index";
import { ColorScheme } from "../types/ui";

export class Formatters {
  /**
   * Format timestamp to human-readable format
   */
  static formatTime(timestamp: number): string {
    const date = new Date(timestamp);
    const now = new Date();

    // Same day: HH:MM:SS
    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString();
    }

    // Different day: MM-DD HH:MM
    return date.toLocaleString();
  }

  /**
   * Format duration in milliseconds
   */
  static formatDuration(ms: number): string {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`;
    return `${(ms / 3600000).toFixed(1)}h`;
  }

  /**
   * Format file size
   */
  static formatSize(bytes: number): string {
    const sizes = ["B", "KB", "MB", "GB"];
    if (bytes === 0) return "0 B";

    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + " " + sizes[i];
  }

  /**
   * Format risk level with color
   */
  static formatRiskLevel(
    level: "low" | "medium" | "high" | "critical"
  ): string {
    const colors = {
      low: "\x1b[32m", // Green
      medium: "\x1b[33m", // Yellow
      high: "\x1b[38;5;208m", // Orange
      critical: "\x1b[31m", // Red
    };
    const reset = "\x1b[0m";

    return `${colors[level]}${level.toUpperCase()}${reset}`;
  }

  /**
   * Format event as string
   */
  static formatEvent(event: AnyEvent): string {
    const time = this.formatTime(event.timestamp);
    const type = event.type;

    let message = `[${time}] ${type}`;

    // Add context based on event type
    switch (event.type) {
      case EventType.AGENT_STARTED:
        message += ` - Agent: ${(event as any).agentName}, Stage: ${(event as any).stage}`;
        break;

      case EventType.AGENT_COMPLETED:
        const duration = this.formatDuration((event as any).duration);
        const result = (event as any).success ? "✓" : "✗";
        message += ` - ${result} (${duration})`;
        break;

      case EventType.VULNERABILITY_FOUND:
        const severity = this.formatRiskLevel((event as any).vulnerability.severity);
        message += ` - ${(event as any).vulnerability.name} [${severity}]`;
        break;

      case EventType.SERVICE_DISCOVERED:
        message += ` - ${(event as any).service.name}:${(event as any).service.port}`;
        break;

      case EventType.TOOL_INVOKED:
        const riskLevel = this.formatRiskLevel((event as any).riskLevel);
        message += ` - Tool: ${(event as any).toolName} [${riskLevel}]`;
        break;

      case EventType.APPROVAL_REQUESTED:
        message += ` - Action: ${(event as any).action.description}`;
        break;

      case EventType.COMMAND_OUTPUT:
        const output = (event as any).output.substring(0, 80);
        message += ` - ${output}`;
        break;
    }

    return message;
  }

  /**
   * Format JSON with indentation
   */
  static formatJSON(obj: any, indent: number = 2): string {
    return JSON.stringify(obj, null, indent);
  }

  /**
   * Format command for display
   */
  static formatCommand(command: string, maxLength: number = 100): string {
    if (command.length <= maxLength) {
      return command;
    }
    return command.substring(0, maxLength - 3) + "...";
  }

  /**
   * Format percentage
   */
  static formatPercentage(value: number, decimals: number = 1): string {
    return (value * 100).toFixed(decimals) + "%";
  }

  /**
   * Format number with separators
   */
  static formatNumber(num: number): string {
    return num.toLocaleString();
  }

  /**
   * Create a simple progress bar
   */
  static createProgressBar(
    current: number,
    total: number,
    width: number = 20
  ): string {
    const percentage = current / total;
    const filled = Math.round(width * percentage);
    const empty = width - filled;

    return `[${"█".repeat(filled)}${"░".repeat(empty)}] ${this.formatPercentage(percentage)}`;
  }

  /**
   * Create a horizontal line
   */
  static createLine(width: number, char: string = "─"): string {
    return char.repeat(width);
  }

  /**
   * Truncate text with ellipsis
   */
  static truncate(text: string, maxLength: number): string {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength - 3) + "...";
  }

  /**
   * Center text in width
   */
  static center(text: string, width: number): string {
    const padding = Math.max(0, width - text.length);
    const leftPad = Math.floor(padding / 2);
    const rightPad = padding - leftPad;

    return " ".repeat(leftPad) + text + " ".repeat(rightPad);
  }

  /**
   * Pad text to width
   */
  static pad(text: string, width: number, char: string = " "): string {
    if (text.length >= width) return text;
    return text + char.repeat(width - text.length);
  }
}
