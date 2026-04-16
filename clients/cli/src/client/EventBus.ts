/**
 * EventBus - Internal event management for CLI components
 * Used to communicate between Ink.js components without prop drilling
 */

import EventEmitter from "events";
import { AnyEvent, EventType } from "../types/index";

export class EventBus extends EventEmitter {
  private eventHistory: AnyEvent[] = [];
  private maxHistorySize: number = 10000;
  private eventStats = {
    total: 0,
    byType: {} as Record<EventType, number>,
  };

  /**
   * Record event and emit to subscribers
   */
  emit(event: AnyEvent | string, ...args: any[]): boolean {
    if (typeof event === "object" && "type" in event) {
      // It's an AnyEvent
      const typedEvent = event as AnyEvent;
      this._recordEvent(typedEvent);
      super.emit("event", typedEvent);
      super.emit(`event:${typedEvent.type}`, typedEvent);
      return true;
    }

    // Regular event emission
    return super.emit(event, ...args);
  }

  /**
   * Record event in history
   */
  private _recordEvent(event: AnyEvent): void {
    this.eventHistory.push(event);
    this.eventStats.total++;

    const type = event.type as EventType;
    this.eventStats.byType[type] = (this.eventStats.byType[type] || 0) + 1;

    // Maintain max history size
    if (this.eventHistory.length > this.maxHistorySize) {
      this.eventHistory.shift();
    }
  }

  /**
   * Get event history
   */
  getHistory(): AnyEvent[] {
    return [...this.eventHistory];
  }

  /**
   * Get events filtered by type
   */
  getEventsByType(type: EventType): AnyEvent[] {
    return this.eventHistory.filter((e) => e.type === type);
  }

  /**
   * Get events in time range
   */
  getEventsByTimeRange(start: number, end: number): AnyEvent[] {
    return this.eventHistory.filter((e) => e.timestamp >= start && e.timestamp <= end);
  }

  /**
   * Get events by agent
   */
  getEventsByAgent(agentId: string): AnyEvent[] {
    return this.eventHistory.filter((e) => e.agentId === agentId);
  }

  /**
   * Get recent events
   */
  getRecentEvents(count: number = 100): AnyEvent[] {
    return this.eventHistory.slice(-count);
  }

  /**
   * Get event statistics
   */
  getStats() {
    return {
      total: this.eventStats.total,
      byType: { ...this.eventStats.byType },
      oldestEvent: this.eventHistory[0]?.timestamp,
      newestEvent: this.eventHistory[this.eventHistory.length - 1]?.timestamp,
    };
  }

  /**
   * Clear history
   */
  clearHistory(): void {
    this.eventHistory = [];
    this.eventStats = {
      total: 0,
      byType: {},
    };
  }

  /**
   * Subscribe to specific event type
   */
  onType(type: EventType, listener: (event: AnyEvent) => void): void {
    this.on(`event:${type}`, listener);
  }

  /**
   * Subscribe to any event
   */
  onAnyEvent(listener: (event: AnyEvent) => void): void {
    this.on("event", listener);
  }

  /**
   * One-time listener
   */
  onceType(type: EventType, listener: (event: AnyEvent) => void): void {
    this.once(`event:${type}`, listener);
  }

  /**
   * Emit UI event (non-orchestrator events)
   */
  emitUI(eventName: string, data?: any): void {
    super.emit(`ui:${eventName}`, data);
  }

  /**
   * Listen to UI event
   */
  onUI(eventName: string, listener: (data: any) => void): void {
    this.on(`ui:${eventName}`, listener);
  }

  /**
   * Emit state change
   */
  emitStateChange(stateName: string, newState: any): void {
    super.emit(`state:${stateName}`, newState);
  }

  /**
   * Subscribe to state change
   */
  onStateChange(stateName: string, listener: (state: any) => void): void {
    this.on(`state:${stateName}`, listener);
  }
}

// Singleton instance
let busInstance: EventBus | null = null;

/**
 * Get or create global EventBus instance
 */
export function getEventBus(): EventBus {
  if (!busInstance) {
    busInstance = new EventBus();
  }
  return busInstance;
}

/**
 * Reset event bus (for testing)
 */
export function resetEventBus(): void {
  if (busInstance) {
    busInstance.removeAllListeners();
    busInstance.clearHistory();
  }
  busInstance = null;
}
