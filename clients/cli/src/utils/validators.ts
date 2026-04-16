/**
 * Validation utilities for user input and data integrity
 */

import {
  ApprovalRequest,
  ActionRiskLevel,
  AuthorizationMethod,
} from "../types/approval";

export class Validators {
  /**
   * Validate risk level
   */
  static isValidRiskLevel(level: any): level is ActionRiskLevel {
    return ["low", "medium", "high", "critical"].includes(level);
  }

  /**
   * Validate authorization method
   */
  static isValidAuthMethod(method: any): method is AuthorizationMethod {
    return [
      "interactive",
      "password",
      "totp",
      "biometric",
      "none",
    ].includes(method);
  }

  /**
   * Validate approval request
   */
  static validateApprovalRequest(request: any): {
    valid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];

    if (!request.id) errors.push("Missing approval ID");
    if (!request.sessionId) errors.push("Missing session ID");
    if (!request.action) errors.push("Missing action");
    if (!request.action.id) errors.push("Missing action ID");
    if (!request.action.name) errors.push("Missing action name");
    if (!this.isValidRiskLevel(request.action.riskLevel)) {
      errors.push("Invalid risk level");
    }
    if (request.timeout && request.timeout < 0) {
      errors.push("Invalid timeout");
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }

  /**
   * Validate session ID format
   */
  static isValidSessionId(sessionId: string): boolean {
    // UUID v4 format
    const uuidRegex =
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    return uuidRegex.test(sessionId);
  }

  /**
   * Validate URL
   */
  static isValidUrl(url: string): boolean {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Validate username
   */
  static isValidUsername(username: string): boolean {
    // Alphanumeric, underscore, hyphen, 3-32 chars
    return /^[a-zA-Z0-9_-]{3,32}$/.test(username);
  }

  /**
   * Validate command
   */
  static isValidCommand(command: string): {
    valid: boolean;
    warnings: string[];
  } {
    const warnings: string[] = [];

    if (!command || command.trim().length === 0) {
      return { valid: false, warnings: ["Command is empty"] };
    }

    // Check for dangerous patterns
    if (
      command.includes("rm -rf") &&
      !command.includes("--dry-run") &&
      !command.includes("--help")
    ) {
      warnings.push("Destructive command detected (rm -rf)");
    }

    if (command.includes("DROP TABLE")) {
      warnings.push("Database destructive command detected");
    }

    if (command.includes("`) || command.includes("$("))) {
      warnings.push("Command injection pattern detected");
    }

    return {
      valid: true,
      warnings,
    };
  }

  /**
   * Validate JSON
   */
  static isValidJSON(text: string): boolean {
    try {
      JSON.parse(text);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Validate CVSS score
   */
  static isValidCVSSScore(score: number): boolean {
    return score >= 0 && score <= 10;
  }

  /**
   * Validate CWE ID
   */
  static isValidCWE(cweid: string): boolean {
    return /^CWE-\d+$/.test(cweid);
  }

  /**
   * Validate port number
   */
  static isValidPort(port: number): boolean {
    return port > 0 && port <= 65535 && Number.isInteger(port);
  }

  /**
   * Validate IP address
   */
  static isValidIPAddress(ip: string): boolean {
    const ipv4Regex =
      /^(\d{1,3}\.){3}\d{1,3}$/;
    const ipv6Regex = /^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$/;

    if (ipv4Regex.test(ip)) {
      const parts = ip.split(".");
      return parts.every((part) => {
        const num = parseInt(part);
        return num >= 0 && num <= 255;
      });
    }

    return ipv6Regex.test(ip);
  }

  /**
   * Sanitize input
   */
  static sanitizeInput(input: string): string {
    return input
      .replace(/[<>]/g, "")
      .replace(/[\r\n]/g, " ")
      .trim();
  }

  /**
   * Validate email
   */
  static isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  /**
   * Check if string is safe (no shell injection)
   */
  static isSafeString(str: string): boolean {
    const dangerousPatterns = [
      /[;&|`$()]/,
      /\$\{.*\}/,
      /\$\(.*\)/,
      /`.*`/,
    ];

    return !dangerousPatterns.some((pattern) => pattern.test(str));
  }

  /**
   * Validate object structure
   */
  static validateObject(obj: any, schema: Record<string, string>): {
    valid: boolean;
    errors: string[];
  } {
    const errors: string[] = [];

    for (const [key, type] of Object.entries(schema)) {
      if (!(key in obj)) {
        errors.push(`Missing required field: ${key}`);
      } else if (typeof obj[key] !== type) {
        errors.push(`Field ${key} must be ${type}, got ${typeof obj[key]}`);
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  }
}
