/**
 * Event Stream Panel Component - Real-time event visualization
 */

import React, { useState, useEffect, useRef } from "react";
import { Box, Text } from "ink";
import { BorderedBox, Badge, StyledText, Divider } from "./Base";
import { AnyEvent, EventType } from "../types/events";
import { Formatters } from "../utils/formatters";
import { EventHelpers } from "../utils/helpers";

interface EventStreamPanelProps {
  events: AnyEvent[];
  maxVisibleEvents?: number;
  autoScroll?: boolean;
  onEventClick?: (event: AnyEvent) => void;
}

/**
 * Real-time event stream visualization
 */
export const EventStreamPanel: React.FC<EventStreamPanelProps> = ({
  events,
  maxVisibleEvents = 15,
  autoScroll = true,
  onEventClick,
}) => {
  const [scrollOffset, setScrollOffset] = useState(0);
  const [selectedEventIndex, setSelectedEventIndex] = useState(-1);
  const [filter, setFilter] = useState<EventType | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest events
  useEffect(() => {
    if (autoScroll) {
      const maxScroll = Math.max(0, events.length - maxVisibleEvents);
      setScrollOffset(maxScroll);
    }
  }, [events.length, maxVisibleEvents, autoScroll]);

  // Filter events
  const filteredEvents = filter
    ? events.filter((e) => e.type === filter)
    : events;

  const visibleEvents = filteredEvents.slice(
    Math.max(0, scrollOffset),
    scrollOffset + maxVisibleEvents
  );

  const getEventColor = (type: EventType): "red" | "yellow" | "green" | "cyan" | "blue" => {
    // Error events
    if (
      type.includes("ERROR") ||
      type === "VULNERABILITY_FOUND" ||
      type === "APPROVAL_REJECTED"
    ) {
      return "red";
    }
    // Warning events
    if (
      type === "COMMAND_OUTPUT" ||
      type === "APPROVAL_REQUESTED" ||
      type === "PERMISSION_DENIED"
    ) {
      return "yellow";
    }
    // Success events
    if (
      type === "AGENT_COMPLETED" ||
      type === "TOOL_COMPLETED" ||
      type === "APPROVAL_GRANTED"
    ) {
      return "green";
    }
    // Info events
    if (
      type === "AGENT_STARTED" ||
      type === "TOOL_INVOKED" ||
      type === "SERVICE_DISCOVERED"
    ) {
      return "cyan";
    }
    // Default
    return "blue";
  };

  const getEventIcon = (type: EventType): string => {
    const icons: Record<EventType, string> = {
      AGENT_STARTED: "▶",
      AGENT_COMPLETED: "✓",
      AGENT_ERROR: "✗",
      TOOL_INVOKED: "→",
      TOOL_COMPLETED: "✓",
      TOOL_ERROR: "✗",
      SERVICE_DISCOVERED: "◆",
      VULNERABILITY_FOUND: "⚠",
      TECHNOLOGY_IDENTIFIED: "~",
      COMMAND_EXECUTED: "⚡",
      COMMAND_OUTPUT: "›",
      COMMAND_ERROR: "✗",
      APPROVAL_REQUESTED: "❓",
      APPROVAL_GRANTED: "✓",
      APPROVAL_REJECTED: "✗",
      CONNECTION_ESTABLISHED: "↔",
      CONNECTION_LOST: "✗",
      OPERATION_STARTED: "▶",
      OPERATION_COMPLETED: "✓",
      LEARNING_RECORDED: "📚",
      TECHNIQUE_OPTIMIZED: "⚙",
      STATUS_UPDATE: "◆",
      METRICS_UPDATE: "◆",
    };
    return icons[type] || "•";
  };

  const formatEventContent = (event: AnyEvent): string => {
    try {
      // Specific formatting for different event types
      const content = Formatters.formatEvent(event);
      return content || JSON.stringify((event as any).data || "");
    } catch {
      return JSON.stringify(event);
    }
  };

  const isEventSelected = (index: number): boolean => {
    return selectedEventIndex === index - scrollOffset;
  };

  return (
    <BorderedBox title="📊 EVENT STREAM" borderColor="cyan">
      <Box flexDirection="column" paddingX={1}>
        {/* Header with stats */}
        <Box marginBottom={1} gap={2}>
          <Text color="cyan" bold>
            Total Events: {events.length}
          </Text>
          <Text color="yellow" bold>
            Visible: {visibleEvents.length}
          </Text>
          {filter && (
            <Badge label={`Filter: ${filter}`} color="yellow" />
          )}
        </Box>

        <Divider width={76} />

        {/* Event list */}
        <Box flexDirection="column" marginY={1}>
          {visibleEvents.length === 0 ? (
            <Text color="gray" dimColor>
              No events to display
            </Text>
          ) : (
            visibleEvents.map((event, index) => (
              <Box
                key={index}
                flexDirection="column"
                marginBottom={1}
                borderStyle={isEventSelected(index) ? "round" : undefined}
                borderColor={isEventSelected(index) ? "cyan" : undefined}
                paddingX={isEventSelected(index) ? 1 : 0}
              >
                {/* Event header */}
                <Box>
                  <Text color={getEventColor(event.type)} bold>
                    {getEventIcon(event.type)}
                  </Text>
                  <Text color={getEventColor(event.type)} marginLeft={1} bold>
                    {event.type}
                  </Text>
                  <Text color="gray" marginLeft={1} dimColor>
                    {Formatters.formatTime(event.timestamp)}
                  </Text>
                </Box>

                {/* Event content */}
                {(event as any).data && (
                  <Box marginLeft={3} marginTop={0.5} wrap="wrap">
                    <Text color="white" wrap="wrap">
                      {formatEventContent(event)}
                    </Text>
                  </Box>
                )}

                {/* Additional metadata */}
                {(event as any).agentId && (
                  <Box marginLeft={3} marginTop={0.5}>
                    <Text color="gray" dimColor>
                      Agent: {(event as any).agentId}
                    </Text>
                  </Box>
                )}
              </Box>
            ))
          )}
        </Box>

        <Divider width={76} />

        {/* Scroll info */}
        <Box marginTop={1} justifyContent="space-between">
          <Text color="gray" dimColor>
            {scrollOffset > 0 && "[↑] Scroll up"}
            {scrollOffset > 0 && scrollOffset + maxVisibleEvents < filteredEvents.length && " • "}
            {scrollOffset + maxVisibleEvents < filteredEvents.length && "[↓] Scroll down"}
          </Text>
          <Text color="gray" dimColor>
            {Math.floor((scrollOffset / Math.max(1, filteredEvents.length)) * 100)}%
          </Text>
        </Box>

        {/* Filter info */}
        <Box marginTop={1}>
          <Text color="gray" dimColor>
            [F]ilter • [C]lear • [S]earch • [D]etails
          </Text>
        </Box>
      </Box>
    </BorderedBox>
  );
};

interface EventSummaryProps {
  events: AnyEvent[];
}

/**
 * Event summary/statistics
 */
export const EventSummary: React.FC<EventSummaryProps> = ({ events }) => {
  const counts = EventHelpers.countByType(events);
  const byAgent = EventHelpers.groupByAgent(events);

  const stats = [
    { label: "Total Events", value: events.length },
    { label: "Error Events", value: Object.values(counts).filter((_, i) => String(Object.keys(counts)[i]).includes("ERROR")).reduce((a, b) => a + b, 0) },
    { label: "Unique Agents", value: byAgent.size },
    { label: "Time Span", value: events.length > 0 ? Formatters.formatDuration(events[events.length - 1].timestamp.getTime() - events[0].timestamp.getTime()) : "N/A" },
  ];

  return (
    <BorderedBox title="📈 EVENT STATISTICS" borderColor="blue">
      <Box flexDirection="column" paddingX={1}>
        {stats.map((stat, index) => (
          <Box key={index} justifyContent="space-between" marginBottom={0.5}>
            <Text color="cyan" bold>
              {stat.label}:
            </Text>
            <Text color="yellow">{stat.value}</Text>
          </Box>
        ))}

        {/* Top event types */}
        <Box marginY={2}>
          <Text bold color="cyan">
            Most Common Events:
          </Text>
        </Box>
        {Object.entries(counts)
          .slice(0, 5)
          .map(([type, count], index) => (
            <Box key={index} marginLeft={2} marginBottom={0.5}>
              <Text color="white">{type}:</Text>
              <Text color="yellow" marginLeft={1}>
                {count}
              </Text>
            </Box>
          ))}
      </Box>
    </BorderedBox>
  );
};

interface EventDetailsProps {
  event: AnyEvent;
}

/**
 * Detailed event information
 */
export const EventDetails: React.FC<EventDetailsProps> = ({ event }) => {
  return (
    <BorderedBox title="🔍 EVENT DETAILS" borderColor="yellow">
      <Box flexDirection="column" paddingX={1}>
        <Box marginBottom={1}>
          <Text bold color="cyan">
            Type:
          </Text>
          <Text marginLeft={1} color="white">
            {event.type}
          </Text>
        </Box>

        <Box marginBottom={1}>
          <Text bold color="cyan">
            Timestamp:
          </Text>
          <Text marginLeft={1} color="white">
            {event.timestamp.toISOString()}
          </Text>
        </Box>

        {/* JSON representation */}
        <Box flexDirection="column" marginTop={1}>
          <Text bold color="cyan" marginBottom={1}>
            Raw Data:
          </Text>
          <Box marginLeft={2} marginRight={2}>
            <Text wrap="wrap" color="gray">
              {Formatters.formatJSON(event, 2)}
            </Text>
          </Box>
        </Box>
      </Box>
    </BorderedBox>
  );
};

export default EventStreamPanel;
