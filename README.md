# GrokClaw 🦎⚡

**A Grok-only edition of [Clawdbot/OpenClaw](https://github.com/openclaw/openclaw)** — streamlined to use xAI's Grok models exclusively.

## What is this?

GrokClaw is a patched fork of Clawdbot that strips the onboarding flow down to a single provider: **xAI (Grok)**. No more scrolling through 15+ auth options — just enter your xAI API key and go.

- **Default model:** `xai/grok-4`
- **Auth:** xAI API key only (via `XAI_API_KEY`)
- **Everything else:** Same powerful Clawdbot feature set (Telegram, Discord, WhatsApp, browser control, tools, memory, etc.)

## Prerequisites

- **Node.js** ≥ 22.12.0
- An **xAI API key** from [console.x.ai](https://console.x.ai)

## Installation

### Option A: Install globally from this folder

```bash
cd grok-claw
npm install
npm link
```

Then run:
```bash
grok-claw setup
# or
clawdbot setup
```

### Option B: Run directly

```bash
cd grok-claw
npm install
node dist/entry.js setup
```

### Option C: Set the env var and skip onboarding

```bash
export XAI_API_KEY=xai-your-key-here
grok-claw gateway start
```

## Usage

GrokClaw works exactly like Clawdbot. All commands are the same:

```bash
grok-claw setup          # First-time setup (xAI key only)
grok-claw gateway start  # Start the gateway daemon
grok-claw gateway stop   # Stop the gateway
grok-claw tui            # Terminal UI chat
grok-claw doctor         # Diagnose issues
```

## What was changed?

This is a **surgical patch** of the compiled `dist/` files — no source rebuild needed:

| File | Change |
|------|--------|
| `dist/commands/auth-choice-options.js` | Stripped `AUTH_CHOICE_GROUP_DEFS` to xAI only; `buildAuthChoiceOptions` returns only `xai-api-key` + skip |
| `dist/commands/auth-choice.apply.api-providers.js` | Added `xai-api-key` handler block (prompts for key, stores credential, sets default model) |
| `dist/commands/onboard-auth.credentials.js` | Added `XAI_DEFAULT_MODEL_REF` constant and `setXaiApiKey()` function |
| `dist/commands/onboard-auth.config-core.js` | Added `applyXaiConfig()` and `applyXaiProviderConfig()` functions |
| `dist/commands/onboard-auth.js` | Updated exports to include new xAI functions and constants |
| `package.json` | Renamed to `grok-claw`, added `grok-claw` bin alias |

## How it works

xAI is already a built-in provider in Clawdbot's model system — the `XAI_API_KEY` env var and `xai/` model prefix are natively supported. GrokClaw simply:

1. Removes all other providers from the onboarding UI
2. Adds a proper credential storage flow for xAI (matching the pattern of OpenRouter, Moonshot, etc.)
3. Sets `xai/grok-4` as the default model

## License

MIT (same as upstream Clawdbot)
