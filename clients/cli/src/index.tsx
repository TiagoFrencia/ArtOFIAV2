#!/usr/bin/env node

/**
 * Entry point for ArtOfIA CLI TUI
 */

import React from "react";
import { render } from "ink";
import App from "./components/App";

// Parse command line arguments
const parseArgs = () => {
  const args: Record<string, string> = {};
  for (let i = 0; i < process.argv.length; i++) {
    if (process.argv[i].startsWith("--")) {
      const key = process.argv[i].substring(2);
      const value = process.argv[i + 1];
      if (!value?.startsWith("--")) {
        args[key] = value;
        i++;
      } else {
        args[key] = "true";
      }
    }
  }
  return args;
};

const args = parseArgs();

// Determine config
const config = {
  orchestratorUrl: args.orchestrator || args.url || "ws://localhost:9000",
  sessionId: args.session || generateSessionId(),
  username: args.username || process.env.USER || "operator",
};

function generateSessionId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// Handle exit gracefully
process.on("SIGINT", () => {
  console.log("\nExiting ArtOfIA CLI...");
  process.exit(0);
});

process.on("SIGTERM", () => {
  console.log("\nTerminating ArtOfIA CLI...");
  process.exit(0);
});

// Start application
try {
  const { unmount } = render(
    <App
      orchestratorUrl={config.orchestratorUrl}
      sessionId={config.sessionId}
      username={config.username}
    />
  );

  // Keep process alive
  process.on("exit", unmount);
} catch (err) {
  console.error("Failed to start CLI:", err);
  process.exit(1);
}
