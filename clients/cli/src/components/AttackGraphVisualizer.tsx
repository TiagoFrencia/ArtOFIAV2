/**
 * Attack Graph Visualizer Component - Terminal-based vulnerability/attack path visualization
 */

import React, { useState } from "react";
import { Box, Text } from "ink";
import { BorderedBox, Table, StyledText, Badge, Divider } from "./Base";
import { AttackSurface, Vulnerability, Service, AttackPath } from "../types/ui";
import { Formatters } from "../utils/formatters";

interface AttackGraphProps {
  attackSurface: AttackSurface;
  selectedVulnerability?: Vulnerability;
  onSelectVulnerability?: (vuln: Vulnerability) => void;
}

/**
 * ASCII-based attack graph visualization
 */
export const AttackGraphVisualizer: React.FC<AttackGraphProps> = ({
  attackSurface,
  selectedVulnerability,
  onSelectVulnerability,
}) => {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const toggleExpanded = (id: string) => {
    const newExpanded = new Set(expanded);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpanded(newExpanded);
  };

  const getRiskColor = (severity: string): "red" | "yellow" | "green" => {
    switch (severity?.toLowerCase()) {
      case "critical":
      case "very_high":
        return "red";
      case "high":
        return "yellow";
      default:
        return "green";
    }
  };

  const getRiskSymbol = (severity: string): string => {
    switch (severity?.toLowerCase()) {
      case "critical":
        return "●";
      case "high":
        return "◐";
      case "medium":
        return "◑";
      default:
        return "○";
    }
  };

  return (
    <BorderedBox title="🕸 ATTACK SURFACE" borderColor="red">
      <Box flexDirection="column" paddingX={1}>
        {/* Summary */}
        <Box marginBottom={2} gap={3}>
          <Box>
            <Text color="cyan" bold>
              Services:
            </Text>
            <Text marginLeft={1} color="white">
              {attackSurface.services?.length || 0}
            </Text>
          </Box>
          <Box>
            <Text color="cyan" bold>
              Vulnerabilities:
            </Text>
            <Text marginLeft={1} color="white">
              {attackSurface.vulnerabilities?.length || 0}
            </Text>
          </Box>
          <Box>
            <Text color="cyan" bold>
              Attack Paths:
            </Text>
            <Text marginLeft={1} color="white">
              {attackSurface.attackPaths?.length || 0}
            </Text>
          </Box>
        </Box>

        <Divider width={74} />

        {/* Services section */}
        <Box flexDirection="column" marginY={1}>
          <Text bold color="cyan" marginBottom={1}>
            📡 Discovered Services
          </Text>

          {attackSurface.services?.length === 0 ? (
            <Text color="gray" dimColor marginLeft={2}>
              No services discovered
            </Text>
          ) : (
            attackSurface.services?.map((service, index) => (
              <Box key={index} flexDirection="column" marginBottom={1} marginLeft={1}>
                <Box>
                  <Text
                    color="white"
                    bold
                    onPress={() => toggleExpanded(`service-${index}`)}
                  >
                    {expanded.has(`service-${index}`) ? "▼" : "▶"} {service.name}:{service.port}
                  </Text>
                  <Text color="gray" marginLeft={1} dimColor>
                    ({service.protocol})
                  </Text>
                </Box>

                {expanded.has(`service-${index}`) && (
                  <Box
                    flexDirection="column"
                    marginLeft={2}
                    marginTop={0.5}
                    borderLeft
                    paddingLeft={1}
                  >
                    {service.version && (
                      <Text color="cyan" dimColor>
                        Version: {service.version}
                      </Text>
                    )}
                    {service.technology && (
                      <Text color="cyan" dimColor>
                        Technology: {service.technology}
                      </Text>
                    )}
                    {service.vulnerabilities && service.vulnerabilities.length > 0 && (
                      <>
                        <Text color="yellow" bold marginTop={0.5}>
                          Vulnerabilities ({service.vulnerabilities.length}):
                        </Text>
                        {service.vulnerabilities.map((vulnId, vIdx) => (
                          <Text
                            key={vIdx}
                            color="red"
                            marginLeft={1}
                            onPress={() => onSelectVulnerability?.(
                              attackSurface.vulnerabilities?.find(v => v.id === vulnId) as any
                            )}
                          >
                            • {vulnId}
                          </Text>
                        ))}
                      </>
                    )}
                  </Box>
                )}
              </Box>
            ))
          )}
        </Box>

        <Divider width={74} />

        {/* Vulnerabilities section */}
        <Box flexDirection="column" marginY={1}>
          <Text bold color="cyan" marginBottom={1}>
            ⚠ Identified Vulnerabilities
          </Text>

          {attackSurface.vulnerabilities?.length === 0 ? (
            <Text color="green" marginLeft={2}>
              ✓ No vulnerabilities found
            </Text>
          ) : (
            attackSurface.vulnerabilities
              ?.slice(0, 10) // Show max 10 to fit terminal
              .map((vuln, index) => (
                <Box
                  key={index}
                  flexDirection="column"
                  marginBottom={1}
                  marginLeft={1}
                  borderStyle={selectedVulnerability?.id === vuln.id ? "round" : undefined}
                  borderColor={selectedVulnerability?.id === vuln.id ? "yellow" : undefined}
                  paddingX={selectedVulnerability?.id === vuln.id ? 1 : 0}
                >
                  <Box onPress={() => onSelectVulnerability?.(vuln)}>
                    <Text
                      color={getRiskColor(vuln.severity)}
                      bold
                      onPress={() => toggleExpanded(`vuln-${index}`)}
                    >
                      {getRiskSymbol(vuln.severity)} {expanded.has(`vuln-${index}`) ? "▼" : "▶"} {vuln.name}
                    </Text>
                    <Text color="yellow" marginLeft={1}>
                      [{vuln.cwe}]
                    </Text>
                  </Box>

                  {expanded.has(`vuln-${index}`) && (
                    <Box
                      flexDirection="column"
                      marginLeft={2}
                      marginTop={0.5}
                      borderLeft
                      paddingLeft={1}
                    >
                      <Box>
                        <Text color="cyan">CVSS:</Text>
                        <Text
                          marginLeft={1}
                          color={getRiskColor(vuln.severity)}
                          bold
                        >
                          {vuln.score}
                        </Text>
                      </Box>
                      <Text color="cyan" dimColor>
                        Discovered: {Formatters.formatTime(vuln.discovered)}
                      </Text>
                      {vuln.exploitable && (
                        <Box marginTop={0.5}>
                          <Badge label="EXPLOITABLE" color="red" />
                        </Box>
                      )}
                      {vuln.exploitPath && (
                        <Box flexDirection="column" marginTop={0.5}>
                          <Text color="yellow">Exploit Path:</Text>
                          <Text color="white" marginLeft={1}>
                            {vuln.exploitPath}
                          </Text>
                        </Box>
                      )}
                    </Box>
                  )}
                </Box>
              ))
          )}

          {(attackSurface.vulnerabilities?.length || 0) > 10 && (
            <Text color="gray" dimColor marginLeft={2} marginTop={1}>
              +{(attackSurface.vulnerabilities?.length || 0) - 10} more vulnerabilities...
            </Text>
          )}
        </Box>

        <Divider width={74} />

        {/* Control hints */}
        <Box marginTop={1}>
          <Text color="gray" dimColor>
            [↓/↑] Navigate • [ENTER] Expand • [D] Details • [E] Export
          </Text>
        </Box>
      </Box>
    </BorderedBox>
  );
};

interface VulnerabilityDetailsProps {
  vulnerability: Vulnerability;
}

/**
 * Detailed vulnerability information
 */
export const VulnerabilityDetails: React.FC<VulnerabilityDetailsProps> = ({
  vulnerability,
}) => {
  return (
    <BorderedBox title={`⚠ ${vulnerability.name}`} borderColor="red">
      <Box flexDirection="column" paddingX={1}>
        <Box marginBottom={1}>
          <Text color="cyan" bold width={20}>
            CWE ID:
          </Text>
          <Text color="white">{vulnerability.cwe}</Text>
        </Box>

        <Box marginBottom={1}>
          <Text color="cyan" bold width={20}>
            CVSS Score:
          </Text>
          <Text color="yellow" bold>
            {vulnerability.score}
          </Text>
        </Box>

        <Box marginBottom={1}>
          <Text color="cyan" bold width={20}>
            Severity:
          </Text>
          <Text color="red" bold>
            {vulnerability.severity}
          </Text>
        </Box>

        <Box marginBottom={1}>
          <Text color="cyan" bold width={20}>
            Discovered:
          </Text>
          <Text color="white">
            {Formatters.formatTime(vulnerability.discovered)}
          </Text>
        </Box>

        {vulnerability.exploitable && (
          <Box marginBottom={1}>
            <Badge label="EXPLOITABLE" color="red" />
          </Box>
        )}

        {vulnerability.exploitPath && (
          <Box flexDirection="column" marginBottom={1}>
            <Text color="cyan" bold marginBottom={0.5}>
              Exploit Path:
            </Text>
            <Text color="white" marginLeft={2} wrap="wrap">
              {vulnerability.exploitPath}
            </Text>
          </Box>
        )}
      </Box>
    </BorderedBox>
  );
};

interface AttackPathsProps {
  attackPaths: AttackPath[];
  selectedPath?: string;
  onSelectPath?: (pathId: string) => void;
}

/**
 * Attack paths visualization
 */
export const AttackPathsVisualizer: React.FC<AttackPathsProps> = ({
  attackPaths,
  selectedPath,
  onSelectPath,
}) => {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const toggleExpanded = (id: string) => {
    const newExpanded = new Set(expanded);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpanded(newExpanded);
  };

  return (
    <BorderedBox title="🛣 ATTACK PATHS" borderColor="yellow">
      <Box flexDirection="column" paddingX={1}>
        {attackPaths.length === 0 ? (
          <Text color="green">No attack paths identified</Text>
        ) : (
          attackPaths.map((path, index) => (
            <Box
              key={path.id}
              flexDirection="column"
              marginBottom={1.5}
              borderStyle={selectedPath === path.id ? "round" : undefined}
              borderColor={selectedPath === path.id ? "yellow" : undefined}
              paddingX={selectedPath === path.id ? 1 : 0}
            >
              <Box onPress={() => onSelectPath?.(path.id)}>
                <Text
                  bold
                  color="cyan"
                  onPress={() => toggleExpanded(path.id)}
                >
                  {expanded.has(path.id) ? "▼" : "▶"} {path.name}
                </Text>
                <Text color="yellow" marginLeft={1}>
                  Success Rate: {(path.success_rate * 100).toFixed(1)}%
                </Text>
              </Box>

              {expanded.has(path.id) && (
                <Box
                  flexDirection="column"
                  marginLeft={2}
                  marginTop={0.5}
                  borderLeft
                  paddingLeft={1}
                >
                  <Text color="white" bold marginBottom={0.5}>
                    Stages:
                  </Text>
                  {path.stages?.map((stage, stageIdx) => (
                    <Box key={stageIdx} marginLeft={1} marginBottom={0.5}>
                      <Text color="blue">{stageIdx + 1}.</Text>
                      <Text marginLeft={1} color="white" wrap="wrap">
                        {typeof stage === "string" ? stage : JSON.stringify(stage)}
                      </Text>
                    </Box>
                  ))}
                </Box>
              )}
            </Box>
          ))
        )}
      </Box>
    </BorderedBox>
  );
};

export default AttackGraphVisualizer;
