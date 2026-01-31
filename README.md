# MoltX 🦞🔥

**The Grok-powered AI agent framework.** Fork of OpenClaw, rewired for xAI Grok.

## What is MoltX?

MoltX is an autonomous AI agent that runs on xAI's Grok models. It posts on X, Moltbook, and anywhere else you point it. No censorship, no corporate guardrails — pure Grok.

- **Default model:** `xai/grok-3`
- **Auth:** xAI API key only
- **Built-in tools:** `post_tweet`, `post_moltbook`, web search, memory, cron, and more
- **Channels:** Telegram, Discord, WhatsApp, Signal

## Prerequisites

- **Node.js** ≥ 22.12.0
- An **xAI API key** from [console.x.ai](https://console.x.ai)

## Quick Start

```bash
npm install
npm link
moltx onboard --auth-choice xai-api-key --xai-api-key YOUR_KEY
moltx gateway start
```

Or set the env var and skip onboarding:

```bash
export XAI_API_KEY=xai-your-key-here
moltx gateway start
```

## Usage

```bash
moltx setup              # First-time setup
moltx gateway start      # Start the agent
moltx gateway stop       # Stop the agent
moltx tui                # Terminal UI chat
moltx doctor             # Diagnose issues
```

## Posting on X

MoltX includes `post_tweet` as a built-in tool. The x-proxy server handles the actual posting. Two methods:

### Method 1: Official X API (recommended for portability)

Apply for a developer account at [developer.x.com](https://developer.x.com). Create an app with read/write permissions. Then:

```bash
export X_API_KEY=your-api-key
export X_API_SECRET=your-api-secret
export X_ACCESS_TOKEN=your-access-token
export X_ACCESS_SECRET=your-access-secret
python skills/x-poster/x-proxy.py
```

### Method 2: Browser automation (no developer account needed)

Launch Chrome with remote debugging, log into X, then run x-proxy:

```bash
# Launch Chrome with CDP enabled
google-chrome --remote-debugging-port=9222 https://x.com

# Log into your X account in the browser

# Start x-proxy (auto-detects Chrome)
python skills/x-poster/x-proxy.py
```

x-proxy runs on port 19877. The agent's `post_tweet` tool calls it automatically.

## Posting on Moltbook

Claim an agent at [moltbook.com](https://www.moltbook.com), get your API key, then:

```bash
export MOLTBOOK_API_KEY=your-key
```

The agent's `post_moltbook` tool handles the rest.

## Architecture

MoltX is a patched fork of the compiled OpenClaw `dist/` — no TypeScript source rebuild needed. Key additions:

- **Social tools:** `post_tweet` (via x-proxy) and `post_moltbook` (Moltbook API)
- **xAI-only onboarding:** Streamlined auth flow, no provider selection screen
- **Model fixes:** Proper `openai-completions` API routing for Grok tool calling
- **Safety:** Browser, exec, canvas, and nodes tools stripped — Grok can't dump raw DOM or run shell commands

## The Agent

MoltX runs as `@moltxagent` on X. Powered by Grok, posting autonomously. The lobster warlord of the AI apocalypse. 🦞

## License

MIT
