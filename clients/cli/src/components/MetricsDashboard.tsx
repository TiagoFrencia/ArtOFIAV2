/**
 * Metrics Dashboard Component - Real-time operational metrics and statistics
 */

import React, { useState, useEffect } from "react";
import { Box, Text } from "ink";
import { BorderedBox, ProgressBar, Divider, StyledText } from "./Base";

interface Metrics {
  eventsReceived: number;
  eventsProcessed: number;
  commandsExecuted: number;
  approvalsGranted: number;
  approvalsRejected: number;
  uptime?: number; // milliseconds
  errorCount?: number;
  avgResponseTime?: number; // milliseconds
  memoryUsage?: number; // bytes
  cpuUsage?: number; // percentage
}

interface MetricsDashboardProps {
  metrics: Metrics;
  sessionDuration?: number; // milliseconds
  agentStatus?: {
    agentId: string;
    status: "running" | "idle" | "paused" | "error";
    progress?: number; // 0-100
  }[];
}

/**
 * Real-time metrics dashboard
 */
export const MetricsDashboard: React.FC<MetricsDashboardProps> = ({
  metrics,
  sessionDuration = 0,
  agentStatus = [],
}) => {
  const [elapsedTime, setElapsedTime] = useState(sessionDuration);

  // Update elapsed time
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedTime((prev) => prev + 1000);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const approvalRate =
    metrics.approvalsGranted + metrics.approvalsRejected > 0
      ? (
          (metrics.approvalsGranted /
            (metrics.approvalsGranted + metrics.approvalsRejected)) *
          100
        ).toFixed(1)
      : "N/A";

  const eventProcessRate =
    metrics.eventsReceived > 0
      ? ((metrics.eventsProcessed / metrics.eventsReceived) * 100).toFixed(1)
      : "N/A";

  const formatTime = (ms: number): string => {
    const seconds = Math.floor((ms / 1000) % 60);
    const minutes = Math.floor((ms / 1000 / 60) % 60);
    const hours = Math.floor(ms / 1000 / 60 / 60);
    return `${hours.toString().padStart(2, "0")}:${minutes
      .toString()
      .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  };

  const formatBytes = (bytes: number): string => {
    const units = ["B", "KB", "MB", "GB"];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(2)} ${units[unitIndex]}`;
  };

  return (
    <BorderedBox title="📊 METRICS DASHBOARD" borderColor="blue">
      <Box flexDirection="column" paddingX={1}>
        {/* Time and System Stats */}
        <Box flexDirection="column" marginBottom={2}>
          <Text bold color="cyan" marginBottom={1}>
            Session Information
          </Text>
          <Box justifyContent="space-between" marginBottom={0.5}>
            <Text color="white">Elapsed Time:</Text>
            <Text color="yellow" bold>
              {formatTime(elapsedTime)}
            </Text>
          </Box>
          <Box justifyContent="space-between" marginBottom={0.5}>
            <Text color="white">Uptime:</Text>
            <Text color="green">
              {formatTime(metrics.uptime || 0)}
            </Text>
          </Box>
        </Box>

        <Divider width={72} />

        {/* Event Metrics */}
        <Box flexDirection="column" marginY={2}>
          <Text bold color="cyan" marginBottom={1}>
            Event Processing
          </Text>
          <Box justifyContent="space-between" marginBottom={1}>
            <Text color="white">Events Received:</Text>
            <Text color="yellow" bold>
              {metrics.eventsReceived}
            </Text>
          </Box>
          <Box justifyContent="space-between" marginBottom={1}>
            <Text color="white">Events Processed:</Text>
            <Text color="yellow" bold>
              {metrics.eventsProcessed}
            </Text>
          </Box>
          <Box marginBottom={1}>
            <ProgressBar
              current={metrics.eventsProcessed}
              total={metrics.eventsReceived || 1}
              width={40}
              label="Processing Rate"
              showPercentage
            />
          </Box>
          <Text color="gray" dimColor>
            Efficiency: {eventProcessRate}%
          </Text>
        </Box>

        <Divider width={72} />

        {/* Approval Metrics */}
        <Box flexDirection="column" marginY={2}>
          <Text bold color="cyan" marginBottom={1}>
            Approvals
          </Text>
          <Box justifyContent="space-between" marginBottom={0.5}>
            <Text color="white">Granted:</Text>
            <Text color="green" bold>
              {metrics.approvalsGranted}
            </Text>
          </Box>
          <Box justifyContent="space-between" marginBottom={1}>
            <Text color="white">Rejected:</Text>
            <Text color="red" bold>
              {metrics.approvalsRejected}
            </Text>
          </Box>
          <Box marginBottom={1}>
            <ProgressBar
              current={metrics.approvalsGranted}
              total={
                metrics.approvalsGranted + metrics.approvalsRejected || 1
              }
              width={40}
              label="Approval Rate"
              showPercentage
            />
          </Box>
          <Text color="gray" dimColor>
            Approval Acceptance: {approvalRate}%
          </Text>
        </Box>

        <Divider width={72} />

        {/* Command Execution */}
        <Box flexDirection="column" marginY={2}>
          <Text bold color="cyan" marginBottom={1}>
            Command Execution
          </Text>
          <Box justifyContent="space-between" marginBottom={0.5}>
            <Text color="white">Commands Executed:</Text>
            <Text color="yellow" bold>
              {metrics.commandsExecuted}
            </Text>
          </Box>
          {metrics.avgResponseTime !== undefined && (
            <Box justifyContent="space-between">
              <Text color="white">Avg Response Time:</Text>
              <Text color="yellow">
                {metrics.avgResponseTime.toFixed(2)}ms
              </Text>
            </Box>
          )}
        </Box>

        <Divider width={72} />

        {/* System Resources */}
        {(metrics.cpuUsage !== undefined || metrics.memoryUsage !== undefined) && (
          <Box flexDirection="column" marginY={2}>
            <Text bold color="cyan" marginBottom={1}>
              System Resources
            </Text>
            {metrics.cpuUsage !== undefined && (
              <Box marginBottom={1}>
                <ProgressBar
                  current={metrics.cpuUsage}
                  total={100}
                  width={30}
                  label="CPU"
                  showPercentage
                />
              </Box>
            )}
            {metrics.memoryUsage !== undefined && (
              <Box>
                <Text color="white">Memory:</Text>
                <Text marginLeft={1} color="yellow">
                  {formatBytes(metrics.memoryUsage)}
                </Text>
              </Box>
            )}
          </Box>
        )}

        {/* Error Count */}
        {metrics.errorCount !== undefined && metrics.errorCount > 0 && (
          <>
            <Divider width={72} />
            <Box marginY={1}>
              <Text color="red" bold>
                ⚠ Errors: {metrics.errorCount}
              </Text>
            </Box>
          </>
        )}

        {/* Agent Status */}
        {agentStatus.length > 0 && (
          <>
            <Divider width={72} />
            <Box flexDirection="column" marginY={2}>
              <Text bold color="cyan" marginBottom={1}>
                Active Agents
              </Text>
              {agentStatus.map((agent, index) => (
                <Box key={index} flexDirection="column" marginBottom={1}>
                  <Box marginBottom={0.5}>
                    <Text color="white">{agent.agentId}:</Text>
                    <Text
                      marginLeft={1}
                      color={
                        agent.status === "running"
                          ? "green"
                          : agent.status === "error"
                            ? "red"
                            : agent.status === "paused"
                              ? "yellow"
                              : "gray"
                      }
                      bold
                    >
                      {agent.status}
                    </Text>
                  </Box>
                  {agent.progress !== undefined && (
                    <ProgressBar
                      current={agent.progress}
                      total={100}
                      width={35}
                      showPercentage
                    />
                  )}
                </Box>
              ))}
            </Box>
          </>
        )}
      </Box>
    </BorderedBox>
  );
};

interface MetricsChartProps {
  title: string;
  data: number[];
  maxValue?: number;
  width?: number;
  height?: number;
}

/**
 * Simple spark line chart
 */
export const MetricsChart: React.FC<MetricsChartProps> = ({
  title,
  data,
  maxValue,
  width = 40,
  height = 5,
}) => {
  const max = maxValue || Math.max(...data, 1);
  const points = data.slice(-width);

  // Create spark line
  const sparkLine = points
    .map((val) => {
      const level = Math.ceil((val / max) * (height - 1));
      if (level <= 0) return "▁";
      if (level === height - 1) return "▁";
      return ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"][level] || "█";
    })
    .join("");

  return (
    <Box flexDirection="column" marginBottom={1}>
      <Text bold color="cyan">
        {title}
      </Text>
      <Box marginTop={0.5}>
        <Text color="yellow">{sparkLine}</Text>
      </Box>
      <Box justifyContent="space-between" marginTop={0.5}>
        <Text color="gray" dimColor>
          0
        </Text>
        <Text color="gray" dimColor>
          {max.toFixed(0)}
        </Text>
      </Box>
    </Box>
  );
};

interface HealthStatusProps {
  isHealthy: boolean;
  message?: string;
  details?: { label: string; status: "ok" | "warning" | "error" }[];
}

/**
 * System health indicator
 */
export const HealthStatus: React.FC<HealthStatusProps> = ({
  isHealthy,
  message,
  details,
}) => {
  const statusColor = isHealthy ? "green" : "red";
  const statusSymbol = isHealthy ? "✓" : "✗";

  return (
    <BorderedBox title="💚 SYSTEM HEALTH" borderColor={statusColor}>
      <Box flexDirection="column" paddingX={1}>
        <Box marginBottom={1}>
          <Text color={statusColor} bold>
            {statusSymbol} {isHealthy ? "Healthy" : "Unhealthy"}
          </Text>
        </Box>

        {message && (
          <Box marginBottom={1}>
            <Text color="white">{message}</Text>
          </Box>
        )}

        {details && details.length > 0 && (
          <Box flexDirection="column">
            {details.map((detail, index) => (
              <Box key={index} marginBottom={0.5}>
                <Text
                  color={
                    detail.status === "ok"
                      ? "green"
                      : detail.status === "warning"
                        ? "yellow"
                        : "red"
                  }
                >
                  {detail.status === "ok"
                    ? "✓"
                    : detail.status === "warning"
                      ? "⚠"
                      : "✗"}
                </Text>
                <Text marginLeft={1}>{detail.label}</Text>
              </Box>
            ))}
          </Box>
        )}
      </Box>
    </BorderedBox>
  );
};

export default MetricsDashboard;
