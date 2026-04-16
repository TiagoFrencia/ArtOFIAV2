/**
 * Main Application Component - Ink.js TUI orchestrator
 */

import React, { useState, useEffect } from "react";
import { Box, Text, useInput } from "ink";
import {
  EventStreamPanel,
  ApprovalPanel,
  AttackGraphVisualizer,
  MetricsDashboard,
  CommandOutputPanel,
  StatusIndicator,
  Tabs,
  Alert,
} from "./index";
import {
  useOrchestratorConnection,
  useEventStream,
  useAppState,
  useApprovalHandling,
  useKeyboardInput,
  useNotifications,
} from "../utils/hooks";
import { StateManager } from "../client/StateManager";
import { OrchestratorClient } from "../client/OrchestratorClient";
import { AnyEvent } from "../types/events";
import { ApprovalRequest } from "../types/approval";
import { DashboardMode } from "../types/ui";

interface AppProps {
  orchestratorUrl?: string;
  sessionId?: string;
  username?: string;
}

/**
 * Main TUI application
 */
export const App: React.FC<AppProps> = ({
  orchestratorUrl = "ws://localhost:9000",
  sessionId = "default-session",
  username = "operator",
}) => {
  // Connection
  const { client, connected, error: connectionError } = useOrchestratorConnection({
    orchestratorUrl,
    sessionId,
    username,
  });

  // State management
  const stateManager = React.useRef(new StateManager(sessionId, username)).current;
  const appState = useAppState(stateManager);

  // Events
  const { events } = useEventStream(client, { maxEvents: 1000 });

  // Approvals
  const { approvals, approveAction, rejectAction } = useApprovalHandling(
    client,
    stateManager
  );

  // Notifications
  const { notifications, addNotification } = useNotifications(stateManager);

  // State
  const [dashboardMode, setDashboardMode] = useState<DashboardMode>("overview");
  const [selectedTab, setSelectedTab] = useState<string>("events");

  // Handle keyboard input
  useInput((input, key) => {
    // Quit application
    if (input === "q" || key.escape) {
      process.exit(0);
    }

    // Mode switching
    if (input === "1") setDashboardMode("overview");
    if (input === "2") setDashboardMode("detailed");
    if (input === "3") setDashboardMode("graph_view");
    if (input === "4") setDashboardMode("metrics");

    // Tab switching
    if (key.leftArrow) {
      const tabs = ["events", "commands", "vulnerabilities"];
      const currentIdx = tabs.indexOf(selectedTab);
      setSelectedTab(tabs[(currentIdx - 1 + tabs.length) % tabs.length]);
    }
    if (key.rightArrow) {
      const tabs = ["events", "commands", "vulnerabilities"];
      const currentIdx = tabs.indexOf(selectedTab);
      setSelectedTab(tabs[(currentIdx + 1) % tabs.length]);
    }

    // Pause/Resume
    if (input === "p") {
      stateManager.pauseOperation();
      addNotification("info", "Operation paused");
    }
    if (input === "r") {
      stateManager.resumeOperation();
      addNotification("info", "Operation resumed");
    }

    // Help
    if (input === "h") {
      setDashboardMode("metrics");
    }

    // Approval handling
    if (approvals.length > 0) {
      if (input === "y") {
        approveAction(approvals[0].id);
        addNotification("success", "Action approved");
      }
      if (input === "n") {
        rejectAction(approvals[0].id, "Operator rejected");
        addNotification("warning", "Action rejected");
      }
    }
  });

  // Update state on changes
  useEffect(() => {
    if (connected) {
      stateManager.setConnected();
    } else if (connectionError) {
      stateManager.setError(connectionError);
    } else {
      stateManager.setDisconnected();
    }
  }, [connected, connectionError]);

  // Render main dashboard based on mode
  const renderDashboard = () => {
    switch (dashboardMode) {
      case "overview":
        return (
          <Box flexDirection="column" width={80}>
            <EventStreamPanel
              events={events.slice(-20)}
              maxVisibleEvents={15}
              autoScroll
            />
          </Box>
        );

      case "graph_view":
        return (
          <Box flexDirection="column" width={80}>
            <AttackGraphVisualizer
              attackSurface={{
                id: "surface-1",
                services: [],
                vulnerabilities: [],
                attackPaths: [],
              }}
            />
          </Box>
        );

      case "metrics":
        return (
          <Box flexDirection="column" width={80}>
            <MetricsDashboard
              metrics={appState.metrics}
              sessionDuration={Date.now() - appState.session.startedAt.getTime()}
            />
          </Box>
        );

      case "approval":
        if (approvals.length === 0) {
          return <Text color="gray">No pending approvals</Text>;
        }
        return (
          <Box flexDirection="column" width={80}>
            <ApprovalPanel
              approval={approvals[0]}
              onApprove={(reasoning) => approveAction(approvals[0].id, reasoning)}
              onReject={(reason) => rejectAction(approvals[0].id, reason)}
            />
          </Box>
        );

      case "detailed":
      case "command_output":
      default:
        return (
          <Box flexDirection="column" width={80}>
            <Box marginBottom={2}>
              <Tabs
                tabs={[
                  { label: "Events", key: "events" },
                  { label: "Commands", key: "commands" },
                  { label: "Vulnerabilities", key: "vulnerabilities" },
                ]}
                activeTab={selectedTab}
                onTabChange={setSelectedTab}
              />
            </Box>

            {selectedTab === "events" && (
              <EventStreamPanel events={events.slice(-25)} maxVisibleEvents={20} />
            )}

            {selectedTab === "commands" && (
              <CommandOutputPanel outputs={[]} selectedIndex={-1} />
            )}

            {selectedTab === "vulnerabilities" && (
              <AttackGraphVisualizer
                attackSurface={{
                  id: "surface-1",
                  services: [],
                  vulnerabilities: [],
                  attackPaths: [],
                }}
              />
            )}
          </Box>
        );
    }
  };

  return (
    <Box flexDirection="column" width={80} height={25}>
      {/* Header */}
      <Box flexDirection="row" justifyContent="space-between" marginBottom={1} paddingX={1}>
        <Text bold color="cyan">
          🕵️ ArtOfIA V2 Terminal UI
        </Text>
        <StatusIndicator
          status={connected ? "connected" : connectionError ? "error" : "disconnected"}
          label="Connection"
        />
      </Box>

      {/* Main Content */}
      <Box flexDirection="column" flexGrow={1} marginBottom={1}>
        {/* Approval interruption overlay */}
        {approvals.length > 0 && dashboardMode !== "approval" && (
          <Box flexDirection="column" marginBottom={1}>
            <Alert
              type="warning"
              message={`⚠ APPROVAL REQUIRED: ${approvals[0].action.name}`}
              title="Pending Approval"
            />
          </Box>
        )}

        {/* Main dashboard */}
        {renderDashboard()}
      </Box>

      {/* Notifications */}
      {notifications.length > 0 && (
        <Box flexDirection="column" marginBottom={1} paddingX={1}>
          {notifications.slice(-2).map((notif, idx) => (
            <Text
              key={idx}
              color={
                notif.type === "error"
                  ? "red"
                  : notif.type === "success"
                    ? "green"
                    : notif.type === "warning"
                      ? "yellow"
                      : "blue"
              }
            >
              {notif.message}
            </Text>
          ))}
        </Box>
      )}

      {/* Footer - Keyboard shortcuts */}
      <Box flexDirection="row" justifyContent="space-between" paddingX={1}>
        <Text color="gray" dimColor>
          [1-4] Modes • [←→] Tabs • [Y/N] Approve • [P]ause • [Q]uit • [H]elp
        </Text>
        <Text color="gray" dimColor>
          Events: {events.length} • Approvals: {approvals.length}
        </Text>
      </Box>
    </Box>
  );
};

// Entry point
export default App;
