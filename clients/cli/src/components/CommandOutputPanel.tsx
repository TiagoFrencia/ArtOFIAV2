/**
 * Command Output Panel Component - Display command execution results and STDOUT/STDERR
 */

import React, { useState, useEffect, useRef } from "react";
import { Box, Text } from "ink";
import { BorderedBox, Badge, Divider } from "./Base";

interface CommandOutput {
  command: string;
  timestamp: Date;
  stdout: string;
  stderr: string;
  exitCode?: number;
  duration?: number; // milliseconds
}

interface CommandOutputPanelProps {
  outputs: CommandOutput[];
  selectedIndex?: number;
  onSelectOutput?: (index: number) => void;
  maxVisibleLines?: number;
  autoScroll?: boolean;
}

/**
 * Display command output with syntax highlighting
 */
export const CommandOutputPanel: React.FC<CommandOutputPanelProps> = ({
  outputs,
  selectedIndex = -1,
  onSelectOutput,
  maxVisibleLines = 20,
  autoScroll = true,
}) => {
  const [scrollOffset, setScrollOffset] = useState(0);
  const currentOutput = selectedIndex >= 0 ? outputs[selectedIndex] : outputs[outputs.length - 1];

  useEffect(() => {
    if (autoScroll && currentOutput) {
      const lines = currentOutput.stdout.split("\n").length;
      const maxScroll = Math.max(0, lines - maxVisibleLines);
      setScrollOffset(maxScroll);
    }
  }, [currentOutput, autoScroll, maxVisibleLines]);

  if (!currentOutput) {
    return (
      <BorderedBox title="💻 COMMAND OUTPUT" borderColor="cyan">
        <Text color="gray" dimColor marginX={1}>
          No command output available
        </Text>
      </BorderedBox>
    );
  }

  const outputLines = currentOutput.stdout.split("\n");
  const errorLines = currentOutput.stderr.split("\n");
  const visibleLines = outputLines.slice(scrollOffset, scrollOffset + maxVisibleLines);

  return (
    <BorderedBox title="💻 COMMAND OUTPUT" borderColor="cyan">
      <Box flexDirection="column" paddingX={1}>
        {/* Command header */}
        <Box marginBottom={1}>
          <Box borderColor="yellow" borderStyle="round" paddingX={1}>
            <Text color="yellow" bold>
              {currentOutput.command}
            </Text>
          </Box>
        </Box>

        {/* Metadata */}
        <Box gap={2} marginBottom={1}>
          <Text color="gray" dimColor>
            {currentOutput.timestamp.toISOString()}
          </Text>
          {currentOutput.duration && (
            <Text color="gray" dimColor>
              Duration: {currentOutput.duration}ms
            </Text>
          )}
          {currentOutput.exitCode !== undefined && (
            <Badge
              label={`Exit: ${currentOutput.exitCode}`}
              color={currentOutput.exitCode === 0 ? "green" : "red"}
            />
          )}
        </Box>

        <Divider width={72} />

        {/* STDOUT */}
        <Box flexDirection="column" marginY={1}>
          {errorLines.length > 0 && errorLines.join("").trim().length === 0 ? null : (
            <>
              <Text bold color="green" marginBottom={0.5}>
                Output:
              </Text>
              <Box flexDirection="column" marginLeft={2}>
                {visibleLines.map((line, index) => (
                  <Text key={index} color="white" wrap="wrap">
                    {line}
                  </Text>
                ))}
              </Box>
            </>
          )}
        </Box>

        {/* STDERR */}
        {errorLines.length > 0 && errorLines.join("").trim().length > 0 && (
          <Box flexDirection="column" marginY={1}>
            <Text bold color="red" marginBottom={0.5}>
              Errors:
            </Text>
            <Box flexDirection="column" marginLeft={2}>
              {errorLines.slice(0, maxVisibleLines).map((line, index) => (
                <Text key={index} color="red" wrap="wrap">
                  {line}
                </Text>
              ))}
            </Box>
          </Box>
        )}

        {/* Scroll indicators */}
        <Divider width={72} margin={1} />
        <Box marginTop={1}>
          <Text color="gray" dimColor>
            {scrollOffset > 0 && "[↑] Scroll up"}
            {scrollOffset > 0 && scrollOffset + maxVisibleLines < outputLines.length && " • "}
            {scrollOffset + maxVisibleLines < outputLines.length && "[↓] Scroll down"}
          </Text>
        </Box>
      </Box>
    </BorderedBox>
  );
};

interface CommandHistoryProps {
  outputs: CommandOutput[];
  selectedIndex?: number;
  onSelectOutput?: (index: number) => void;
  maxItems?: number;
}

/**
 * Command history sidebar
 */
export const CommandHistory: React.FC<CommandHistoryProps> = ({
  outputs,
  selectedIndex = -1,
  onSelectOutput,
  maxItems = 10,
}) => {
  const items = outputs.slice(-maxItems);

  return (
    <BorderedBox title="📜 HISTORY" borderColor="blue">
      <Box flexDirection="column" paddingX={1}>
        {items.length === 0 ? (
          <Text color="gray" dimColor>
            No commands executed yet
          </Text>
        ) : (
          items.map((output, index) => {
            const actualIndex = outputs.length - items.length + index;
            const isSelected = selectedIndex === actualIndex;

            return (
              <Box
                key={index}
                flexDirection="column"
                marginBottom={1}
                borderStyle={isSelected ? "round" : undefined}
                borderColor={isSelected ? "cyan" : undefined}
                paddingX={isSelected ? 1 : 0}
                onPress={() => onSelectOutput?.(actualIndex)}
              >
                <Text
                  color={isSelected ? "cyan" : "white"}
                  bold={isSelected}
                  wrap="truncate"
                  width={30}
                >
                  {isSelected ? "▶ " : "  "}
                  {output.command.length > 25 ? output.command.slice(0, 22) + "..." : output.command}
                </Text>
                <Box marginLeft={2}>
                  <Badge
                    label={
                      output.exitCode === 0 || output.exitCode === undefined
                        ? "Success"
                        : `Error: ${output.exitCode}`
                    }
                    color={
                      output.exitCode === 0 || output.exitCode === undefined
                        ? "green"
                        : "red"
                    }
                  />
                </Box>
              </Box>
            );
          })
        )}
      </Box>
    </BorderedBox>
  );
};

interface LiveLogProps {
  lines: string[];
  maxLines?: number;
  logLevel?: "info" | "warning" | "error" | "debug";
  title?: string;
}

/**
 * Live log stream display
 */
export const LiveLog: React.FC<LiveLogProps> = ({
  lines,
  maxLines = 30,
  logLevel = "info",
  title = "LOG STREAM",
}) => {
  const visibleLines = lines.slice(-maxLines);

  const logColors: Record<string, "blue" | "yellow" | "red" | "gray"> = {
    info: "blue",
    warning: "yellow",
    error: "red",
    debug: "gray",
  };

  const logSymbols: Record<string, string> = {
    info: "ℹ",
    warning: "⚠",
    error: "✗",
    debug: "◆",
  };

  return (
    <BorderedBox title={logSymbols[logLevel] + " " + title} borderColor={logColors[logLevel]}>
      <Box flexDirection="column" paddingX={1}>
        {visibleLines.map((line, index) => (
          <Text key={index} color={logColors[logLevel]} wrap="wrap">
            {line}
          </Text>
        ))}
      </Box>
    </BorderedBox>
  );
};

interface CommandProgressProps {
  command: string;
  progress: number; // 0-100
  stage?: string;
  eta?: number; // seconds remaining
}

/**
 * Display command progress
 */
export const CommandProgress: React.FC<CommandProgressProps> = ({
  command,
  progress,
  stage,
  eta,
}) => {
  const progressBar = "█".repeat(Math.floor(progress / 5)) + "░".repeat(Math.ceil((100 - progress) / 5));

  return (
    <BorderedBox title="⚙ EXECUTION" borderColor="magenta">
      <Box flexDirection="column" paddingX={1}>
        <Box marginBottom={1}>
          <Box borderColor="yellow" borderStyle="round" paddingX={1}>
            <Text color="yellow" bold>
              {command}
            </Text>
          </Box>
        </Box>

        {stage && (
          <Box marginBottom={1}>
            <Text color="cyan">Stage:</Text>
            <Text marginLeft={1} color="white">
              {stage}
            </Text>
          </Box>
        )}

        <Box marginBottom={1}>
          <Text color="cyan">{progressBar}</Text>
          <Text marginLeft={1} color="yellow" bold>
            {progress}%
          </Text>
        </Box>

        {eta && (
          <Box>
            <Text color="gray" dimColor>
              ETA: {eta}s
            </Text>
          </Box>
        )}
      </Box>
    </BorderedBox>
  );
};

export default CommandOutputPanel;
