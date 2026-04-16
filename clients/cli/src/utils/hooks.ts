/**
 * React hooks for TUI component state management and orchestration
 */

import { useEffect, useState, useRef, useCallback } from "react";
import { OrchestratorClient } from "../client/OrchestratorClient";
import { EventBus, getEventBus } from "../client/EventBus";
import { StateManager } from "../client/StateManager";
import {
  AnyEvent,
  EventType,
  ApprovalRequestedEvent,
} from "../types/events";
import { ApprovalRequest, ApprovalResponse } from "../types/approval";
import { DashboardMode } from "../types/ui";

/**
 * Hook to manage orchestrator client connection
 */
export function useOrchestratorConnection(
  config: ConstructorParameters<typeof OrchestratorClient>[0]
) {
  const clientRef = useRef<OrchestratorClient | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const client = new OrchestratorClient(config);
    clientRef.current = client;

    client.connect().then(
      () => {
        setConnected(true);
        setError(null);
      },
      (err) => {
        setError(err.message);
        setConnected(false);
      }
    );

    return () => {
      client.disconnect();
    };
  }, [config]);

  return {
    client: clientRef.current,
    connected,
    error,
  };
}

/**
 * Hook to stream real-time events from orchestrator
 */
export function useEventStream(
  client: OrchestratorClient | null,
  options?: { maxEvents?: number }
) {
  const [events, setEvents] = useState<AnyEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!client) return;

    setLoading(true);
    const subscription = client.on("event", (event: AnyEvent) => {
      setEvents((prev) => {
        const updated = [...prev, event];
        if (options?.maxEvents && updated.length > options.maxEvents) {
          return updated.slice(-options.maxEvents);
        }
        return updated;
      });
      setLoading(false);
    });

    client.on("error", (err) => {
      setError(err.message);
      setLoading(false);
    });

    return () => {
      if (subscription && typeof subscription.unsubscribe === "function") {
        subscription.unsubscribe();
      }
    };
  }, [client, options?.maxEvents]);

  return { events, loading, error };
}

/**
 * Hook to subscribe to EventBus
 */
export function useEventBus(
  eventType?: EventType | EventType[]
) {
  const [events, setEvents] = useState<AnyEvent[]>([]);
  const busRef = useRef<EventBus>(getEventBus());

  useEffect(() => {
    const bus = busRef.current;

    if (!eventType) {
      // Subscribe to all events
      const listener = (event: AnyEvent) => {
        setEvents((prev) => [...prev, event]);
      };
      bus.onAnyEvent(listener);
      return () => {
        // Cleanup not directly available, would need to add remove listener
      };
    }

    if (Array.isArray(eventType)) {
      // Subscribe to multiple types
      const listeners = eventType.map((type) => {
        const listener = (event: AnyEvent) => {
          if (event.type === type) {
            setEvents((prev) => [...prev, event]);
          }
        };
        bus.onType(type, listener);
        return listener;
      });
      return () => {
        // Cleanup
      };
    }

    // Subscribe to single type
    const listener = (event: AnyEvent) => {
      setEvents((prev) => [...prev, event]);
    };
    bus.onType(eventType, listener);
    return () => {
      // Cleanup
    };
  }, [eventType]);

  return events;
}

/**
 * Hook to manage global application state
 */
export function useAppState(stateManager: StateManager) {
  const [state, setState] = useState(stateManager.getState());

  useEffect(() => {
    return stateManager.subscribeAll((newState) => {
      setState(newState);
    });
  }, [stateManager]);

  return state;
}

/**
 * Hook to subscribe to specific state key
 */
export function useStateKey<K extends keyof ReturnType<typeof StateManager.prototype.getState>>(
  stateManager: StateManager,
  key: K
) {
  const [value, setValue] = useState(stateManager.getState()[key]);

  useEffect(() => {
    return stateManager.subscribe(key as string, (newValue) => {
      setValue(newValue);
    });
  }, [stateManager, key]);

  return value;
}

/**
 * Hook to handle approval requests
 */
export function useApprovalHandling(
  client: OrchestratorClient | null,
  stateManager: StateManager
) {
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);

  useEffect(() => {
    if (!client) return;

    const handleApprovalRequest = (event: ApprovalRequestedEvent) => {
      setApprovals((prev) => [...prev, event.data as any]);
    };

    client.on("event:APPROVAL_REQUESTED", handleApprovalRequest);

    return () => {
      client.removeListener("event:APPROVAL_REQUESTED", handleApprovalRequest);
    };
  }, [client, stateManager]);

  const approveAction = useCallback(
    async (approvalId: string, reasoning?: string) => {
      if (!client) return;
      try {
        await client.approveAction(approvalId, reasoning);
        setApprovals((prev) => prev.filter((a) => a.id !== approvalId));
        stateManager.recordApprovalGranted();
      } catch (err) {
        console.error("Failed to approve action:", err);
      }
    },
    [client, stateManager]
  );

  const rejectAction = useCallback(
    async (approvalId: string, reason: string) => {
      if (!client) return;
      try {
        await client.rejectAction(approvalId, reason);
        setApprovals((prev) => prev.filter((a) => a.id !== approvalId));
        stateManager.recordApprovalRejected();
      } catch (err) {
        console.error("Failed to reject action:", err);
      }
    },
    [client, stateManager]
  );

  return {
    approvals,
    approveAction,
    rejectAction,
  };
}

/**
 * Hook to filter events by criteria
 */
export function useFilteredEvents(
  events: AnyEvent[],
  filter: {
    type?: EventType;
    agentId?: string;
    minSeverity?: "low" | "medium" | "high" | "critical";
    timeRange?: [number, number];
  }
) {
  return events.filter((event) => {
    if (filter.type && event.type !== filter.type) return false;

    if (filter.agentId && (event as any).agentId !== filter.agentId)
      return false;

    if (filter.timeRange) {
      const timestamp = event.timestamp.getTime();
      if (timestamp < filter.timeRange[0] || timestamp > filter.timeRange[1])
        return false;
    }

    return true;
  });
}

/**
 * Hook to manage keyboard input
 */
export function useKeyboardInput(handler: (key: string) => void) {
  useEffect(() => {
    const onKeypress = (_: any, key: any) => {
      if (key.name) {
        handler(key.name);
      }
    };

    // Note: This would need proper readline setup in a real implementation
    // Placeholder for now
    return () => {};
  }, [handler]);
}

/**
 * Hook to manage command execution
 */
export function useCommandExecution(client: OrchestratorClient | null) {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(
    async (command: string, args?: string[]) => {
      if (!client) {
        setError("Client not connected");
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const result = await client.executeCommand(command, args);
        setResult(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    },
    [client]
  );

  return { execute, result, loading, error };
}

/**
 * Hook to track metrics
 */
export function useMetrics(stateManager: StateManager) {
  const [metrics, setMetrics] = useState(stateManager.getState().metrics);

  useEffect(() => {
    return stateManager.subscribe("metrics" as any, (newMetrics) => {
      setMetrics(newMetrics);
    });
  }, [stateManager]);

  return metrics;
}

/**
 * Hook to manage dashboard mode
 */
export function useDashboardMode(stateManager: StateManager) {
  const uiState = useStateKey(stateManager, "ui" as any);
  const mode = (uiState as any)?.mode as DashboardMode;

  const setMode = useCallback(
    (newMode: DashboardMode) => {
      stateManager.setDashboardMode(newMode);
    },
    [stateManager]
  );

  return { mode, setMode };
}

/**
 * Hook to manage notifications
 */
export function useNotifications(stateManager: StateManager) {
  const appState = useAppState(stateManager);
  const notifications = appState.notifications;

  const addNotification = useCallback(
    (type: "info" | "success" | "warning" | "error", message: string) => {
      stateManager.addNotification(type, message);
    },
    [stateManager]
  );

  const removeNotification = useCallback(
    (id: string) => {
      stateManager.removeNotification(id);
    },
    [stateManager]
  );

  return {
    notifications,
    addNotification,
    removeNotification,
  };
}

/**
 * Hook for debounced value
 */
export function useDebouncedValue<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Hook for local storage
 */
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item =
        typeof window !== "undefined"
          ? window.localStorage?.getItem(key)
          : null;
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore =
        value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      if (typeof window !== "undefined") {
        window.localStorage?.setItem(key, JSON.stringify(valueToStore));
      }
    } catch {
      console.error("Failed to set local storage");
    }
  };

  return [storedValue, setValue] as const;
}
