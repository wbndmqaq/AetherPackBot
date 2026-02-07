# AetherPackBot

A modern, modular multi-platform chatbot framework with LLM support.

## Features

- **Multi-Platform Support**: Telegram, Discord, and more
- **Multiple LLM Providers**: OpenAI, Anthropic Claude, Google Gemini
- **Plugin System**: Extensible architecture with hot-reload support
- **Event-Driven**: Async-first design with event bus
- **Web Dashboard**: RESTful API with FastAPI
- **Type-Safe**: Full type hints with Pydantic validation

## Quick Start

```bash
# Install with UV
pip install uv
uv sync

# Run the bot
uv run aetherpack
```

## Configuration

Create a `config.yaml` file:

```yaml
bot:
  name: "MyBot"
  
platforms:
  telegram:
    enabled: true
    token: "YOUR_BOT_TOKEN"

providers:
  openai:
    enabled: true
    api_key: "YOUR_API_KEY"
    model: "gpt-4"
```

## Architecture

```
aetherpackbot/
├── core/           # Core engine and event system
├── platforms/      # Platform adapters (Telegram, Discord)
├── providers/      # LLM providers (OpenAI, Claude)
├── plugins/        # Plugin system
├── api/            # Web API
└── utils/          # Utilities
```

## License

MIT License
