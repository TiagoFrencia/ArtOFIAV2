/**
 * Base/Reusable UI Components for Ink.js
 */

import React from "react";
import { Box, Text } from "ink";
import { StyleHelpers } from "../utils/helpers";

interface BoxProps {
  title?: string;
  padding?: number;
  borderColor?: "red" | "green" | "yellow" | "blue" | "cyan" | "magenta";
  width?: number | string;
  height?: number;
  children: React.ReactNode;
}

/**
 * Bordered box component
 */
export const BorderedBox: React.FC<BoxProps> = ({
  title,
  padding = 1,
  borderColor = "cyan",
  width,
  children,
}) => {
  return (
    <Box flexDirection="column" borderStyle="round" borderColor={borderColor} paddingX={padding} paddingY={padding}>
      {title && (
        <Box marginBottom={1}>
          <Text bold color={borderColor}>
            {title}
          </Text>
        </Box>
      )}
      {children}
    </Box>
  );
};

interface TextProps {
  color?: "red" | "green" | "yellow" | "blue" | "cyan" | "magenta" | "white" | "gray";
  bold?: boolean;
  dim?: boolean;
  wrap?: "wrap" | "truncate" | "truncate-middle";
  children: React.ReactNode;
}

/**
 * Styled text component
 */
export const StyledText: React.FC<TextProps> = ({
  color,
  bold = false,
  dim = false,
  wrap = "wrap",
  children,
}) => {
  return (
    <Text color={color} bold={bold} dimColor={dim} wrap={wrap}>
      {children}
    </Text>
  );
};

interface StatusIndicatorProps {
  status: "connected" | "disconnected" | "loading" | "error" | "paused";
  label?: string;
}

/**
 * Connection/Status indicator
 */
export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label = "Status",
}) => {
  const statusSymbols: Record<string, string> = {
    connected: "✓",
    disconnected: "✗",
    loading: "⟳",
    error: "!",
    paused: "⏸",
  };

  const statusColors: Record<string, "red" | "green" | "yellow" | "blue"> = {
    connected: "green",
    disconnected: "red",
    loading: "yellow",
    error: "red",
    paused: "yellow",
  };

  return (
    <Box>
      <Text color={statusColors[status]} bold>
        {statusSymbols[status]} {label}: {status}
      </Text>
    </Box>
  );
};

interface BadgeProps {
  label: string;
  color?: "red" | "green" | "yellow" | "blue" | "cyan" | "magenta";
}

/**
 * Badge component for small labels
 */
export const Badge: React.FC<BadgeProps> = ({ label, color = "cyan" }) => {
  return (
    <Box borderStyle="round" paddingX={1} borderColor={color}>
      <Text color={color} bold>
        {label}
      </Text>
    </Box>
  );
};

interface ProgressBarProps {
  current: number;
  total: number;
  width?: number;
  label?: string;
  showPercentage?: boolean;
}

/**
 * Progress bar component
 */
export const ProgressBar: React.FC<ProgressBarProps> = ({
  current,
  total,
  width = 30,
  label,
  showPercentage = true,
}) => {
  const percentage = total > 0 ? (current / total) * 100 : 0;
  const filledWidth = Math.round((percentage / 100) * width);
  const bar = "█".repeat(filledWidth) + "░".repeat(width - filledWidth);

  return (
    <Box flexDirection="column">
      {label && <Text>{label}</Text>}
      <Box>
        <Text color="cyan">{bar}</Text>
        {showPercentage && (
          <Text marginLeft={1} color="yellow">
            {percentage.toFixed(1)}%
          </Text>
        )}
      </Box>
    </Box>
  );
};

interface LoadingSpinnerProps {
  message?: string;
}

/**
 * Loading spinner component
 */
export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = "Loading",
}) => {
  const [frame, setFrame] = React.useState(0);
  const frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];

  React.useEffect(() => {
    const interval = setInterval(() => {
      setFrame((f) => (f + 1) % frames.length);
    }, 80);
    return () => clearInterval(interval);
  }, []);

  return (
    <Box>
      <Text color="yellow" bold>
        {frames[frame]} {message}
      </Text>
    </Box>
  );
};

interface DividerProps {
  width?: number;
  char?: string;
  color?: "red" | "green" | "yellow" | "blue" | "cyan" | "magenta" | "gray";
}

/**
 * Horizontal divider
 */
export const Divider: React.FC<DividerProps> = ({
  width = 80,
  char = "─",
  color = "gray",
}) => {
  return (
    <Box width={width}>
      <Text color={color}>{char.repeat(width)}</Text>
    </Box>
  );
};

interface TabsProps {
  tabs: { label: string; key: string }[];
  activeTab: string;
  onTabChange: (key: string) => void;
}

/**
 * Tabs component
 */
export const Tabs: React.FC<TabsProps> = ({ tabs, activeTab, onTabChange }) => {
  return (
    <Box flexDirection="row" gap={2}>
      {tabs.map((tab, index) => (
        <Box key={tab.key}>
          {index > 0 && <Text color="gray">│</Text>}
          <Text
            color={activeTab === tab.key ? "cyan" : "gray"}
            bold={activeTab === tab.key}
            onPress={() => onTabChange(tab.key)}
          >
            {tab.label}
          </Text>
        </Box>
      ))}
    </Box>
  );
};

interface AlertProps {
  type: "info" | "success" | "warning" | "error";
  message: string;
  title?: string;
}

/**
 * Alert component
 */
export const Alert: React.FC<AlertProps> = ({ type, message, title }) => {
  const icons: Record<string, string> = {
    info: "ℹ",
    success: "✓",
    warning: "⚠",
    error: "✗",
  };

  const colors: Record<string, "blue" | "green" | "yellow" | "red"> = {
    info: "blue",
    success: "green",
    warning: "yellow",
    error: "red",
  };

  return (
    <Box flexDirection="column" borderStyle="round" borderColor={colors[type]} paddingX={1} paddingY={1}>
      {title && (
        <Box marginBottom={1}>
          <Text color={colors[type]} bold>
            {icons[type]} {title}
          </Text>
        </Box>
      )}
      <Text color={colors[type]}>{message}</Text>
    </Box>
  );
};

interface KeyBindingsHelpProps {
  bindings: { key: string; description: string }[];
}

/**
 * Keyboard bindings help display
 */
export const KeyBindingsHelp: React.FC<KeyBindingsHelpProps> = ({ bindings }) => {
  return (
    <Box flexDirection="column">
      <Text bold color="cyan" marginBottom={1}>
        Keyboard Shortcuts:
      </Text>
      {bindings.map((binding, index) => (
        <Box key={index} marginLeft={2}>
          <Text bold color="yellow" width={4}>
            {binding.key}
          </Text>
          <Text> - {binding.description}</Text>
        </Box>
      ))}
    </Box>
  );
};

interface TableProps {
  headers: string[];
  rows: (string | number)[][];
  columnWidths?: number[];
}

/**
 * Simple table component
 */
export const Table: React.FC<TableProps> = ({ headers, rows, columnWidths }) => {
  const widths = columnWidths || headers.map(() => 20);

  return (
    <Box flexDirection="column">
      {/* Header */}
      <Box>
        {headers.map((header, index) => (
          <Box key={index} width={widths[index]} marginRight={1}>
            <Text bold color="cyan">
              {String(header).padEnd(widths[index] - 1)}
            </Text>
          </Box>
        ))}
      </Box>

      {/* Divider */}
      <Box margin={0}>
        <Text color="gray">{headers.map(() => "─".repeat(20)).join(" ")}</Text>
      </Box>

      {/* Rows */}
      {rows.map((row, rowIndex) => (
        <Box key={rowIndex}>
          {row.map((cell, cellIndex) => (
            <Box key={cellIndex} width={widths[cellIndex]} marginRight={1}>
              <Text>{String(cell).padEnd(widths[cellIndex] - 1)}</Text>
            </Box>
          ))}
        </Box>
      ))}
    </Box>
  );
};

interface MenuProps {
  items: { label: string; key: string }[];
  selectedIndex?: number;
  onSelect: (key: string) => void;
}

/**
 * Menu selection component
 */
export const Menu: React.FC<MenuProps> = ({ items, selectedIndex = 0, onSelect }) => {
  const [selected, setSelected] = React.useState(selectedIndex);

  React.useEffect(() => {
    const handleInput = (ch: string, key: any) => {
      if (key.upArrow) {
        setSelected((prev) => (prev > 0 ? prev - 1 : items.length - 1));
      } else if (key.downArrow) {
        setSelected((prev) => (prev < items.length - 1 ? prev + 1 : 0));
      } else if (key.return) {
        onSelect(items[selected].key);
      }
    };

    // Note: This is simplified. In a real implementation, you'd use stdin/readline
    return () => {};
  }, [selected, items, onSelect]);

  return (
    <Box flexDirection="column">
      {items.map((item, index) => (
        <Box
          key={item.key}
          paddingX={1}
          borderStyle={index === selected ? "round" : undefined}
          borderColor={index === selected ? "cyan" : undefined}
        >
          <Text color={index === selected ? "cyan" : "white"} bold={index === selected}>
            {index === selected ? "▶ " : "  "}
            {item.label}
          </Text>
        </Box>
      ))}
    </Box>
  );
};

export default {
  BorderedBox,
  StyledText,
  StatusIndicator,
  Badge,
  ProgressBar,
  LoadingSpinner,
  Divider,
  Tabs,
  Alert,
  KeyBindingsHelp,
  Table,
  Menu,
};
