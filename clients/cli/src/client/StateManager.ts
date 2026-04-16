/**
 * StateManager - Global application state management
 * Manages UI state, pending approvals, and operational state
 */

import { getEventBus } from "./EventBus";
import { UIState, DashboardMode, EventFilter } from "../types/ui";
import { ApprovalRequest } from "../types/approval";

export interface AppState {
  ui: {
    mode: DashboardMode;
    selectedTab: string;
    focusedElement?: string;
    scrollPosition: number;
    isPaused: boolean;
    filters: EventFilter;
    loading: boolean;
  };
  session: {
    sessionId: string;
    username: string;
    startedAt: number;
    isPaused: boolean;
    status: "connected" | "disconnected" | "paused" | "error";
  };
  operation: {
    currentStage?: string;
    targetInfo?: Record<string, any>;
    startedAt?: number;
    completedAt?: number;
    error?: string;
  };
  metrics: {
    eventsReceived: number;
    eventsProcessed: number;
    commandsExecuted: number;
    approvalsgranted: number;
    approvalsRejected: number;
  };
  notifications: Array<{
    id: string;
    type: string;
    message: string;
    timestamp: number;
  }>;
}

export class StateManager {
  private state: AppState;
  private eventBus = getEventBus();
  private listeners: Map<string, Set<(state: Partial<AppState>) => void>> =
    new Map();

  constructor(sessionId: string, username: string) {
    this.state = {
      ui: {
        mode: DashboardMode.OVERVIEW,
        selectedTab: "events",
        scrollPosition: 0,
        isPaused: false,
        filters: {},
        loading: false,
      },
      session: {
        sessionId,
        username,
        startedAt: Date.now(),
        isPaused: false,
        status: "disconnected",
      },
      operation: {},
      metrics: {
        eventsReceived: 0,
        eventsProcessed: 0,
        commandsExecuted: 0,
        approvalsgranted: 0,
        approvalsRejected: 0,
      },
      notifications: [],
    };
  }

  /**
   * Get full state
   */
  getState(): Readonly<AppState> {
    return { ...this.state };
  }

  /**
   * Get partial state
   */
  getUIState(): UIState {
    return {
      mode: this.state.ui.mode,
      selectedTab: this.state.ui.selectedTab,
      focusedElement: this.state.ui.focusedElement,
      scrollPosition: this.state.ui.scrollPosition,
      isPaused: this.state.ui.isPaused,
      filters: this.state.ui.filters,
    };
  }

  /**
   * Update UI state
   */
  updateUIState(updates: Partial<AppState["ui"]>): void {
    this.state.ui = { ...this.state.ui, ...updates };
    this._notifyListeners("ui", { ui: this.state.ui });
  }

  /**
   * Update session state
   */
  updateSessionState(updates: Partial<AppState["session"]>): void {
    this.state.session = { ...this.state.session, ...updates };
    this._notifyListeners("session", { session: this.state.session });
  }

  /**
   * Update operation state
   */
  updateOperationState(updates: Partial<AppState["operation"]>): void {
    this.state.operation = { ...this.state.operation, ...updates };
    this._notifyListeners("operation", { operation: this.state.operation });
  }

  /**
   * Update metrics
   */
  incrementMetric(
    key: keyof AppState["metrics"],
    amount: number = 1
  ): void {
    (this.state.metrics[key] as number) += amount;
    this._notifyListeners("metrics", { metrics: this.state.metrics });
  }

  /**
   * Add notification
   */
  addNotification(type: string, message: string): string {
    const id = `notif_${Date.now()}_${Math.random()}`;
    this.state.notifications.push({
      id,
      type,
      message,
      timestamp: Date.now(),
    });

    this._notifyListeners("notifications", {
      notifications: this.state.notifications,
    });

    // Auto-remove after 5 seconds
    setTimeout(() => this.removeNotification(id), 5000);

    return id;
  }

  /**
   * Remove notification
   */
  removeNotification(id: string): void {
    this.state.notifications = this.state.notifications.filter(
      (n) => n.id !== id
    );
    this._notifyListeners("notifications", {
      notifications: this.state.notifications,
    });
  }

  /**
   * Change dashboard mode
   */
  setDashboardMode(mode: DashboardMode): void {
    this.updateUIState({ mode });
    this.eventBus.emitUI("dashboard_mode_changed", mode);
  }

  /**
   * Set selected tab
   */
  setSelectedTab(tab: string): void {
    this.updateUIState({ selectedTab: tab });
  }

  /**
   * Pause operation
   */
  pauseOperation(): void {
    this.updateSessionState({
      isPaused: true,
      status: "paused",
    });
    this.updateUIState({ isPaused: true });
    this.eventBus.emitUI("operation_paused");
  }

  /**
   * Resume operation
   */
  resumeOperation(): void {
    this.updateSessionState({
      isPaused: false,
      status: "connected",
    });
    this.updateUIState({ isPaused: false });
    this.eventBus.emitUI("operation_resumed");
  }

  /**
   * Connect to orchestrator
   */
  setConnected(): void {
    this.updateSessionState({
      status: "connected",
    });
    this.eventBus.emitUI("connected");
  }

  /**
   * Disconnect from orchestrator
   */
  setDisconnected(): void {
    this.updateSessionState({
      status: "disconnected",
    });
    this.eventBus.emitUI("disconnected");
  }

  /**
   * Set error state
   */
  setError(error: string): void {
    this.updateSessionState({ status: "error" });
    this.updateOperationState({ error });
    this.addNotification("error", error);
  }

  /**
   * Clear error
   */
  clearError(): void {
    this.updateOperationState({ error: undefined });
  }

  /**
   * Record approval granted
   */
  recordApprovalGranted(): void {
    this.incrementMetric("approvalsgranted");
    this.addNotification("success", "Action approved");
  }

  /**
   * Record approval rejected
   */
  recordApprovalRejected(): void {
    this.incrementMetric("approvalsRejected");
    this.addNotification("warning", "Action rejected");
  }

  /**
   * Subscribe to state changes
   */
  subscribe(
    key: keyof AppState,
    listener: (state: Partial<AppState>) => void
  ): () => void {
    if (!this.listeners.has(key)) {
      this.listeners.set(key, new Set());
    }

    this.listeners.get(key)!.add(listener);

    // Return unsubscribe function
    return () => {
      this.listeners.get(key)?.delete(listener);
    };
  }

  /**
   * Subscribe to all changes
   */
  subscribeAll(listener: (state: Partial<AppState>) => void): () => void {
    const unsubs: Array<() => void> = [];

    (Object.keys(this.state) as Array<keyof AppState>).forEach((key) => {
      unsubs.push(this.subscribe(key, listener));
    });

    return () => {
      unsubs.forEach((unsub) => unsub());
    };
  }

  /**
   * Notify listeners
   */
  private _notifyListeners(key: string, state: Partial<AppState>): void {
    const listeners = this.listeners.get(key as keyof AppState);
    if (listeners) {
      listeners.forEach((listener) => {
        try {
          listener(state);
        } catch (err) {
          console.error("[StateManager] Listener error:", err);
        }
      });
    }
  }

  /**
   * Save state snapshot for recovery
   */
  getSnapshot(): AppState {
    return JSON.parse(JSON.stringify(this.state));
  }

  /**
   * Restore from snapshot
   */
  restoreFromSnapshot(snapshot: AppState): void {
    this.state = JSON.parse(JSON.stringify(snapshot));
    this._notifyListeners("ui", { ui: this.state.ui });
    this._notifyListeners("session", { session: this.state.session });
    this._notifyListeners("operation", { operation: this.state.operation });
    this._notifyListeners("metrics", { metrics: this.state.metrics });
  }

  /**
   * Export state as JSON
   */
  exportState(): string {
    return JSON.stringify(this.state, null, 2);
  }

  /**
   * Clear all state
   */
  reset(): void {
    this.state.notifications = [];
    this.state.ui.scrollPosition = 0;
    this.state.metrics = {
      eventsReceived: 0,
      eventsProcessed: 0,
      commandsExecuted: 0,
      approvalsgranted: 0,
      approvalsRejected: 0,
    };
  }
}
