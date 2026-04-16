/**
 * Approval Panel Component - State-Managed Human-in-the-Loop Interruption
 */

import React, { useState, useEffect } from "react";
import { Box, Text } from "ink";
import { BorderedBox, Alert, StyledText, Badge } from "./Base";
import { ApprovalRequest } from "../types/approval";
import { Formatters } from "../utils/formatters";
import { StyleHelpers } from "../utils/helpers";

interface ApprovalPanelProps {
  approval: ApprovalRequest;
  onApprove: (reasoning?: string) => Promise<void>;
  onReject: (reason: string) => Promise<void>;
  autoRejectInSeconds?: number;
}

/**
 * Interactive approval panel for high-risk actions
 * Displays action details and waits for operator Y/N decision
 */
export const ApprovalPanel: React.FC<ApprovalPanelProps> = ({
  approval,
  onApprove,
  onReject,
  autoRejectInSeconds = 300, // 5 minutes default
}) => {
  const [decision, setDecision] = useState<"approve" | "reject" | null>(null);
  const [reasoning, setReasoning] = useState("");
  const [timeRemaining, setTimeRemaining] = useState(autoRejectInSeconds);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Countdown timer
  useEffect(() => {
    if (decision) return; // Stop countdown once decision made

    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          // Auto-reject on timeout
          handleReject("Timeout - auto-rejected");
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [decision]);

  const handleApprove = async () => {
    setLoading(true);
    setError(null);
    try {
      setDecision("approve");
      await onApprove(reasoning);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve");
      setDecision(null);
      setLoading(false);
    }
  };

  const handleReject = async (reason?: string) => {
    setLoading(true);
    setError(null);
    try {
      setDecision("reject");
      await onReject(reason || "Operator rejected");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reject");
      setDecision(null);
      setLoading(false);
    }
  };

  const riskColor = (level: string): "red" | "yellow" | "green" | "cyan" => {
    switch (level) {
      case "critical":
        return "red";
      case "high":
        return "yellow";
      default:
        return "cyan";
    }
  };

  return (
    <BorderedBox title="⚠ APPROVAL REQUIRED" borderColor={riskColor(approval.action.riskLevel as string)}>
      <Box flexDirection="column" marginBottom={2} paddingX={1}>
        {/* Action Summary */}
        <Box marginBottom={2}>
          <Text bold color="white">
            Action: {approval.action.name}
          </Text>
        </Box>

        {/* Risk Level Badge */}
        <Box marginBottom={2}>
          <Badge
            label={`RISK: ${approval.action.riskLevel?.toUpperCase()}`}
            color={riskColor(approval.action.riskLevel as string)}
          />
        </Box>

        {/* Description */}
        <Box flexDirection="column" marginBottom={2}>
          <Text bold color="cyan" marginBottom={1}>
            Description:
          </Text>
          <Text marginLeft={2}>{approval.action.description}</Text>
        </Box>

        {/* Command to be executed */}
        <Box flexDirection="column" marginBottom={2}>
          <Text bold color="cyan" marginBottom={1}>
            Command:
          </Text>
          <Box marginLeft={2} borderStyle="round" borderColor="yellow" paddingX={1}>
            <Text color="yellow" wrap="wrap">
              {approval.action.command || "N/A"}
            </Text>
          </Box>
        </Box>

        {/* Target information */}
        {approval.action.target && (
          <Box flexDirection="column" marginBottom={2}>
            <Text bold color="cyan" marginBottom={1}>
              Target:
            </Text>
            <Text marginLeft={2}>{approval.action.target}</Text>
          </Box>
        )}

        {/* Impact assessment */}
        {approval.action.impact && (
          <Box flexDirection="column" marginBottom={2}>
            <Text bold color="cyan" marginBottom={1}>
              Potential Impact:
            </Text>
            <Box marginLeft={2} borderStyle="round" borderColor="red" paddingX={1} paddingY={1}>
              <Text color="red" wrap="wrap">
                {approval.action.impact}
              </Text>
            </Box>
          </Box>
        )}

        {/* Request timestamp */}
        <Box marginBottom={2}>
          <Text color="gray" dimColor>
            Requested at: {Formatters.formatTime(approval.requestedAt)}
          </Text>
        </Box>

        {/* Timeout countdown */}
        <Box marginBottom={2}>
          <Text
            color={timeRemaining < 60 ? "yellow" : "cyan"}
            bold={timeRemaining < 60}
          >
            Time remaining: {Formatters.formatDuration(timeRemaining * 1000)}
          </Text>
        </Box>

        {/* Authorization requirements */}
        {approval.requiredMethod && approval.requiredMethod !== "interactive" && (
          <Box marginBottom={2}>
            <Alert
              type="warning"
              message={`This approval requires: ${approval.requiredMethod}`}
              title="Authentication Required"
            />
          </Box>
        )}

        {/* Error message if any */}
        {error && (
          <Box marginBottom={2}>
            <Alert type="error" message={error} title="Error" />
          </Box>
        )}

        {/* Decision status */}
        {decision && (
          <Box marginBottom={2}>
            {decision === "approve" && (
              <Alert
                type="success"
                message="Action approved. Resuming operation..."
                title="Approved"
              />
            )}
            {decision === "reject" && (
              <Alert
                type="warning"
                message="Action rejected. Terminating operation..."
                title="Rejected"
              />
            )}
          </Box>
        )}

        {/* Reasoning input */}
        {!decision && approval.requiresReasoning && (
          <Box flexDirection="column" marginBottom={2}>
            <Text bold color="cyan" marginBottom={1}>
              Reasoning (optional):
            </Text>
            <Box
              marginLeft={2}
              borderStyle="round"
              borderColor="cyan"
              paddingX={1}
              paddingY={1}
            >
              <Text color="white">{reasoning || "(Enter reasoning...)"}</Text>
            </Box>
          </Box>
        )}

        {/* Action Buttons / Instructions */}
        {!decision || error ? (
          <Box flexDirection="column" marginTop={2} paddingTop={1}>
            <Text bold color="white" marginBottom={1}>
              Press to decide:
            </Text>
            <Box flexDirection="row" gap={4}>
              <Box borderColor="green" borderStyle="round" paddingX={2}>
                <Text color="green" bold>
                  [Y] APPROVE
                </Text>
              </Box>
              <Box borderColor="red" borderStyle="round" paddingX={2}>
                <Text color="red" bold>
                  [N] REJECT
                </Text>
              </Box>
            </Box>
            <Text color="gray" marginTop={1} dimColor>
              [?] Help • [Q] Quit (auto-reject in {timeRemaining}s)
            </Text>
          </Box>
        ) : (
          <Box marginTop={2}>
            <Text color="yellow" bold>
              Processing your decision...
            </Text>
          </Box>
        )}
      </Box>
    </BorderedBox>
  );
};

interface ApprovalQueueProps {
  approvals: ApprovalRequest[];
  onApprove: (approvalId: string, reasoning?: string) => Promise<void>;
  onReject: (approvalId: string, reason: string) => Promise<void>;
}

/**
 * Queue of pending approvals
 */
export const ApprovalQueue: React.FC<ApprovalQueueProps> = ({
  approvals,
  onApprove,
  onReject,
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  if (approvals.length === 0) {
    return <Text color="gray">No pending approvals</Text>;
  }

  const current = approvals[currentIndex];

  return (
    <Box flexDirection="column">
      <Box marginBottom={1}>
        <Text color="yellow">
          Approval {currentIndex + 1} of {approvals.length}
        </Text>
      </Box>

      <ApprovalPanel
        approval={current}
        onApprove={(reasoning) => {
          return onApprove(current.id, reasoning).then(() => {
            if (currentIndex < approvals.length - 1) {
              setCurrentIndex(currentIndex + 1);
            }
          });
        }}
        onReject={(reason) => {
          return onReject(current.id, reason).then(() => {
            if (currentIndex < approvals.length - 1) {
              setCurrentIndex(currentIndex + 1);
            }
          });
        }}
      />

      {/* Navigation */}
      {approvals.length > 1 && (
        <Box marginTop={2}>
          <Text color="gray" dimColor>
            [←] Previous • [→] Next
          </Text>
        </Box>
      )}
    </Box>
  );
};

export default ApprovalPanel;
