#!/usr/bin/env node

/**
 * portkey-router.js - Model routing service for Roo Code
 *
 * This script implements a Portkey-based router for directing requests to
 * appropriate AI models based on mode and task requirements.
 */

const http = require("http");
const https = require("https");
const url = require("url");

// Configuration for model routing
const MODEL_CONFIG = {
  architect: {
    provider: "anthropic",
    model: "claude-3-sonnet-20240229",
    variant: "thinking",
    temperature: 0.3,
    api_key_env: "ANTHROPIC_API_KEY",
  },
  code: {
    provider: "openai",
    model: "gpt-4-1106-preview",
    temperature: 0.02,
    api_key_env: "OPENAI_API_KEY",
  },
  reviewer: {
    provider: "google",
    model: "gemini-1.5-pro-latest",
    temperature: 0.2,
    api_key_env: "GOOGLE_API_KEY",
  },
  ask: {
    provider: "perplexity",
    model: "sonar-medium-online",
    temperature: 0.2,
    api_key_env: "PERPLEXITY_API_KEY",
  },
  strategy: {
    provider: "xai",
    model: "grok-1",
    temperature: 0.5,
    api_key_env: "XAI_API_KEY",
  },
  creative: {
    provider: "openai",
    model: "gpt-4-1106-preview",
    temperature: 0.7,
    api_key_env: "OPENAI_API_KEY",
  },
  debug: {
    provider: "anthropic",
    model: "claude-3-sonnet-20240229",
    temperature: 0.1,
    api_key_env: "ANTHROPIC_API_KEY",
  },
};

// Portkey API configuration
const PORTKEY_API_URL = "https://api.portkey.ai/v1/completions";
const PORTKEY_API_KEY = process.env.PORTKEY_API_KEY;

/**
 * Get API key for the specified provider from environment variables
 */
function getApiKey(keyEnv) {
  const apiKey = process.env[keyEnv];
  if (!apiKey) {
    console.warn(`API key ${keyEnv} not found in environment`);
    return null;
  }
  return apiKey;
}

/**
 * Route a model request via Portkey
 */
async function routeModelRequest(mode, prompt, systemPrompt) {
  if (!mode || !MODEL_CONFIG[mode]) {
    throw new Error(`Unknown or missing mode: ${mode}`);
  }

  const config = MODEL_CONFIG[mode];
  const apiKey = getApiKey(config.api_key_env);

  if (!apiKey) {
    throw new Error(`No API key available for ${mode} mode`);
  }

  // Prepare headers with Portkey authentication
  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${PORTKEY_API_KEY}`,
  };

  // Construct payload based on provider
  const provider = config.provider;
  const payload = {
    provider: provider,
    model: config.model,
    mode: "completion",
    temperature: config.temperature,
    messages: [{ role: "user", content: prompt }],
    virtual_key: apiKey,
    metadata: {
      mode: mode,
      project: "orchestra",
    },
  };

  // Add system prompt if provided
  if (systemPrompt) {
    payload.messages.unshift({ role: "system", content: systemPrompt });
  }

  // Add provider-specific parameters
  if (provider === "anthropic" && config.variant) {
    payload.parameters = { variant: config.variant };
  }

  // Log the request (excluding sensitive data)
  const safePayload = { ...payload, virtual_key: "***REDACTED***" };
  console.log(`Sending request to ${provider}/${config.model}`);
  console.log(`Request payload: ${JSON.stringify(safePayload)}`);

  return new Promise((resolve, reject) => {
    const req = https.request(
      PORTKEY_API_URL,
      {
        method: "POST",
        headers: headers,
      },
      (res) => {
        let data = "";

        res.on("data", (chunk) => {
          data += chunk;
        });

        res.on("end", () => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            try {
              const result = JSON.parse(data);
              resolve(result.choices[0].message.content);
            } catch (error) {
              reject(new Error(`Failed to parse response: ${error.message}`));
            }
          } else {
            reject(
              new Error(
                `Request failed with status ${res.statusCode}: ${data}`,
              ),
            );
          }
        });
      },
    );

    req.on("error", (error) => {
      reject(new Error(`Request error: ${error.message}`));
    });

    req.write(JSON.stringify(payload));
    req.end();
  });
}

/**
 * Handle MCP requests
 */
async function handleRequest(req, res) {
  // Parse URL and query parameters
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;

  // Basic routing
  if (pathname === "/route_model_request") {
    // Get request body for POST requests
    let body = "";
    req.on("data", (chunk) => {
      body += chunk.toString();
    });

    req.on("end", async () => {
      try {
        const requestData = JSON.parse(body);
        const { mode, prompt, systemPrompt } = requestData;

        if (!mode || !prompt) {
          res.writeHead(400, { "Content-Type": "application/json" });
          res.end(
            JSON.stringify({
              error: "Missing required parameters: mode and prompt",
            }),
          );
          return;
        }

        try {
          const result = await routeModelRequest(mode, prompt, systemPrompt);
          res.writeHead(200, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ result }));
        } catch (error) {
          console.error(`Error routing model request: ${error.message}`);
          res.writeHead(500, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ error: error.message }));
        }
      } catch (error) {
        console.error(`Error parsing request: ${error.message}`);
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "Invalid JSON in request body" }));
      }
    });
  } else {
    res.writeHead(404, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: "Not found" }));
  }
}

// Create and start the server
const server = http.createServer(handleRequest);
const PORT = process.env.PORT || 3000;

server.listen(PORT, () => {
  console.log(`Portkey Router MCP server listening on port ${PORT}`);

  // Write to stdout for MCP to connect
  console.log(
    JSON.stringify({
      schema: {
        route_model_request: {
          description:
            "Route a model request to the appropriate provider via Portkey",
          parameters: {
            mode: {
              type: "string",
              description: "The Roo mode (architect, code, etc.)",
            },
            prompt: {
              type: "string",
              description: "The user prompt to send to the model",
            },
            systemPrompt: {
              type: "string",
              description: "Optional system prompt",
            },
          },
          returns: {
            type: "string",
            description: "The model's response",
          },
        },
      },
    }),
  );
});
