/**
 * OrchestratorClient - Manages connection to ArtOfIA V2 Orchestrator
 * Handles bidirectional communication with state-managed interruption
 */

import EventEmitter from "events";
import { AnyEvent, EventType, EventStreamOptions } from "../types/index";
import {
  ApprovalRequest,
  ApprovalResponse,
  ApprovalStatus,
} from "../types/approval";

export interface ClientConfig {
  orchestratorUrl: string; // e.g., "http://localhost:8000"
  sessionId: string;
  username: string;
  retryAttempts?: number;
  retryDelay?: number;
  connectionTimeout?: number;
}

export interface ConnectionStatus {
  connected: boolean;
  lastHeartbeat?: number;
  eventCount: number;
  errors: number;
}

export class OrchestratorClient extends EventEmitter {
  private config: ClientConfig;
  private ws?: WebSocket;
  private status: ConnectionStatus = {
    connected: false,
    eventCount: 0,
    errors: 0,
  };
  private retryCount = 0;
  private pendingApprovals: Map<string, ApprovalRequest> = new Map();
  private eventBuffer: AnyEvent[] = [];

  constructor(config: ClientConfig) {
    super();
    this.config = {
      retryAttempts: 5,
      retryDelay: 1000,
      connectionTimeout: 10000,
      ...config,
    };
  }

  /**
   * Connect to orchestrator via WebSocket
   */
  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = this.config.orchestratorUrl
          .replace("http://", "ws://")
          .replace("https://", "wss://");

        this.ws = new WebSocket(`${wsUrl}/api/v1/cli-stream`);

        this.ws.onopen = () => {
          console.log("[Client] Connected to orchestrator");
          this.status.connected = true;
          this.retryCount = 0;

          // Send initial handshake
          this.send({
            type: "handshake",
            sessionId: this.config.sessionId,
            username: this.config.username,
          });

          this.emit("connected");
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (err) {
            console.error("[Client] Failed to parse message:", err);
            this.status.errors++;
          }
        };

        this.ws.onerror = (event) => {
          console.error("[Client] WebSocket error:", event);
          this.status.errors++;
          this.emit("error", event);
        };

        this.ws.onclose = () => {
          console.log("[Client] Disconnected from orchestrator");
          this.status.connected = false;
          this.emit("disconnected");

          // Attempt reconnect
          if (this.config.retryAttempts && this.retryCount < this.config.retryAttempts!) {
            this.retryCount++;
            setTimeout(() => this.connect(), this.config.retryDelay);
          } else {
            reject(new Error("Failed to connect after retries"));
          }
        };

        // Connection timeout
        setTimeout(() => {
          if (!this.status.connected) {
            reject(new Error("Connection timeout"));
          }
        }, this.config.connectionTimeout);
      } catch (err) {
        reject(err);
      }
    });
  }

  /**
   * Handle incoming messages from orchestrator
   */
  private handleMessage(message: any): void {
    const { type, data } = message;

    switch (type) {
      case "event":
        this.handleEvent(data);
        break;

      case "approval_request":
        this.handleApprovalRequest(data);
        break;

      case "heartbeat":
        this.handleHeartbeat();
        break;

      case "error":
        this.emit("server_error", data);
        break;

      default:
        console.warn("[Client] Unknown message type:", type);
    }
  }

  /**
   * Handle event from orchestrator
   */
  private handleEvent(event: AnyEvent): void {
    this.status.eventCount++;
    this.eventBuffer.push(event);

    // Emit based on event type
    this.emit("event", event);
    this.emit(`event:${event.type}`, event);

    // Keep buffer size manageable
    if (this.eventBuffer.length > 10000) {
      this.eventBuffer = this.eventBuffer.slice(-5000);
    }
  }

  /**
   * Handle approval request from orchestrator
   */
  private handleApprovalRequest(request: ApprovalRequest): void {
    this.pendingApprovals.set(request.id, request);
    this.emit("approval_requested", request);
  }

  /**
   * Handle heartbeat from orchestrator
   */
  private handleHeartbeat(): void {
    this.status.lastHeartbeat = Date.now();

    // Send heartbeat response
    this.send({
      type: "heartbeat_response",
      sessionId: this.config.sessionId,
    });
  }

  /**
   * Send approval response to orchestrator
   */
  async approveAction(
    approvalId: string,
    reasoning?: string
  ): Promise<void> {
    const approval = this.pendingApprovals.get(approvalId);
    if (!approval) {
      throw new Error(`Approval request not found: ${approvalId}`);
    }

    const response: ApprovalResponse = {
      approvalId,
      decision: "approve",
      operator: this.config.username,
      timestamp: Date.now(),
      reasoning,
    };

    this.send({
      type: "approval_response",
      data: response,
    });

    this.pendingApprovals.delete(approvalId);
    this.emit("action_approved", approval);
  }

  /**
   * Reject action
   */
  async rejectAction(approvalId: string, reason: string): Promise<void> {
    const approval = this.pendingApprovals.get(approvalId);
    if (!approval) {
      throw new Error(`Approval request not found: ${approvalId}`);
    }

    const response: ApprovalResponse = {
      approvalId,
      decision: "reject",
      operator: this.config.username,
      timestamp: Date.now(),
      reasoning: reason,
    };

    this.send({
      type: "approval_response",
      data: response,
    });

    this.pendingApprovals.delete(approvalId);
    this.emit("action_rejected", approval);
  }

  /**
   * Send custom command to orchestrator
   */
  async executeCommand(command: string, args?: Record<string, any>): Promise<any> {
    return new Promise((resolve, reject) => {
      const requestId = `cmd_${Date.now()}_${Math.random()}`;

      const timeout = setTimeout(() => {
        this.removeListener(`command_response:${requestId}`, resolve);
        reject(new Error("Command timeout"));
      }, 30000);

      this.once(`command_response:${requestId}`, (response) => {
        clearTimeout(timeout);
        if (response.error) {
          reject(new Error(response.error));
        } else {
          resolve(response.data);
        }
      });

      this.send({
        type: "command",
        requestId,
        command,
        args,
      });
    });
  }

  /**
   * Stream events from orchestrator
   */
  async streamEvents(options?: EventStreamOptions): Promise<AsyncIterable<AnyEvent>> {
    const timeout = options?.timeout || 3600000; // 1 hour default
    const startTime = Date.now();

    const generator = async function* (this: OrchestratorClient) {
      while (Date.now() - startTime < timeout) {
        if (this.eventBuffer.length > 0) {
          yield this.eventBuffer.shift()!;
        } else {
          await new Promise((resolve) => setTimeout(resolve, 100));
        }

        if (!this.status.connected) {
          throw new Error("Connection lost");
        }
      }
    };

    return generator.call(this);
  }

  /**
   * Get pending approvals
   */
  getPendingApprovals(): ApprovalRequest[] {
    return Array.from(this.pendingApprovals.values());
  }

  /**
   * Get approval request by ID
   */
  getApproval(approvalId: string): ApprovalRequest | undefined {
    return this.pendingApprovals.get(approvalId);
  }

  /**
   * Get connection status
   */
  getStatus(): ConnectionStatus {
    return { ...this.status };
  }

  /**
   * Send message to orchestrator
   */
  private send(message: any): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket not connected");
    }

    this.ws.send(JSON.stringify(message));
  }

  /**
   * Pause operation (freeze agent state)
   */
  async pause(): Promise<void> {
    this.send({
      type: "pause",
      sessionId: this.config.sessionId,
    });
  }

  /**
   * Resume operation
   */
  async resume(): Promise<void> {
    this.send({
      type: "resume",
      sessionId: this.config.sessionId,
    });
  }

  /**
   * Stop operation and save state
   */
  async stop(): Promise<void> {
    this.send({
      type: "stop",
      sessionId: this.config.sessionId,
    });
  }

  /**
   * Graceful disconnect
   */
  async disconnect(): Promise<void> {
    if (this.ws) {
      this.ws.close(1000, "Client closed");
    }
  }

  /**
   * Get event history
   */
  getEventHistory(): AnyEvent[] {
    return [...this.eventBuffer];
  }

  /**
   * Filter events by type
   */
  getEventsByType(type: EventType): AnyEvent[] {
    return this.eventBuffer.filter((e) => e.type === type);
  }
}
