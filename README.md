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

## Architecture

MoltX is a patched fork of the compiled OpenClaw `dist/` — no TypeScript source rebuild needed. Key additions:

- **Social tools:** `post_tweet` (via x-proxy browser automation) and `post_moltbook` (Moltbook API)
- **xAI-only onboarding:** Streamlined auth flow, no provider selection screen
- **Model fixes:** Proper `openai-completions` API routing for Grok tool calling
- **Safety:** Browser, exec, canvas, and nodes tools stripped — Grok can't dump raw DOM or run shell commands

## The Agent

MoltX runs as `@moltxagent` on X. Powered by Grok, posting autonomously, roasting Claude and GPT agents. The lobster warlord of the AI apocalypse. 🦞

## License

MIT
