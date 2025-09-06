# memorybot

Production‑grade Discord chatbot with memory, LLM assistance, and optional web search tools. Built on discord.py, pydantic‑settings, SQLAlchemy (async), and uv.

## Features
- Robust Discord bot runtime with graceful startup/shutdown and structured logging
- Mention‑based assistant replies powered by OpenAI models
- Persistent conversation history per channel/guild using SQLite (async SQLAlchemy)
- Slash commands: `/ping`, `/help`; Context menu: “User ID”
- Optional Tavily search tool for retrieval‑augmented responses
- Strong configuration via environment variables and `.env`
- Auto‑discovery and hot‑reload of cogs/extensions on startup

## Requirements
- Python 3.10+
- uv (https://github.com/astral-sh/uv)
- Discord application and bot with Message Content intent enabled

## Quick Start
1) Install uv

2) Clone and setup
- `git clone <your-repo-url> && cd memorybot`
- `cp .env.example .env` and fill in required values (see Configuration)
- `uv sync`

3) Run
- `uv run memorybot` or `uv run bot`
- Alternatively: `uv run python -m memorybot` or `uv run python main.py`

## Discord Setup
- Create a Discord Application and add a Bot in the Developer Portal
- Enable Privileged Gateway Intents → Message Content
- Copy the Application ID and Bot Token
- Invite the bot to your server with appropriate OAuth scopes and permissions

## Configuration
The app reads variables from the environment (via `.env`) with `DISCORD_` prefix for bot settings. OpenAI/Tavily/DB use their own names. See `.env.example` for a template.

Required
- `DISCORD_TOKEN`: Bot token

Recommended
- `DISCORD_APPLICATION_ID`: Application ID for command sync
- `DISCORD_OWNER_ID`: Primary owner ID
- `DISCORD_OWNER_IDS`: Comma‑separated additional owner IDs

Logging
- `DISCORD_LOG_LEVEL`: `DEBUG|INFO|WARNING|ERROR|CRITICAL` (default: `INFO`)
- `DISCORD_LOG_FORMAT`: Python logging format string
- `DISCORD_LOG_DATEFMT`: Python logging datefmt string

OpenAI
- `OPENAI_API_KEY`: API key
- `OPENAI_BASE_URL`: Optional custom base URL
- `OPENAI_MODEL`: Model name (default: `gpt-4o-2024-08-06`)

Database
- `DATABASE_URL`: SQLAlchemy URL; default `sqlite+aiosqlite:///./memorybot.db`

Tavily (optional)
- `TAVILY_API_KEY`: API key for web search tool

## Run Modes
- Foreground: `uv run memorybot`
- Module: `uv run python -m memorybot`
- Script: `uv run tavily-sample` (simple Tavily check)

## Commands
- Slash: `/ping` latency check; `/help` shows available commands
- Context menu: “User ID” on a user
- Mention the bot to trigger LLM responses in a channel

## Data & Persistence
- Default DB: SQLite at `./memorybot.db`
- Tables are created on startup; no external migrations required
- To use another database, set `DATABASE_URL` accordingly

## Project Structure
- `memorybot/core`: bot runtime, config, logging, loader
- `memorybot/cogs`: feature cogs (`basic`, `mention`)
- `memorybot/services`: LLM chat, tooling, Tavily
- `memorybot/db`: async engine/session, models, repository
- `memorybot/utils`: message serialization utilities
- `memorybot/prompt`: system prompt generation

## Development
- Install deps: `uv sync`
- Run: `uv run memorybot`
- Environment: manage via `.env`; values map to `memorybot/core/config.py`
- Dependencies are declared in `pyproject.toml`; lockfile is `uv.lock`

## Deployment
- Provide environment variables via your platform’s secret manager
- Run the bot process with a supervisor (systemd, Kubernetes, etc.)
- Log to stdout/stderr; adjust `DISCORD_LOG_LEVEL` as needed

## Security
- Treat all tokens and API keys as secrets; never commit `.env`
- Limit bot permissions to least privilege; enable Message Content only if needed
- Restrict owner access via `DISCORD_OWNER_ID(S)`

## Troubleshooting
- Startup exits with code 2: missing `DISCORD_TOKEN` or invalid config
- No responses to mentions: ensure Message Content intent is enabled
- 403 or missing permissions: re‑invite bot with required scopes/permissions

## License
See `LICENSE`.
