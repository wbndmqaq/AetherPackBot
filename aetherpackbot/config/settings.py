"""Application settings with Pydantic."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    """Bot-specific settings."""

    name: str = "AetherPackBot"
    prefix: str = "/"
    admin_users: list[str] = Field(default_factory=list)


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    level: str = "INFO"
    format: str = "json"
    file: str | None = None


class APISettings(BaseSettings):
    """API server settings."""

    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 8080
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])


class PlatformSettings(BaseSettings):
    """Platform-specific settings container."""

    telegram: dict[str, Any] = Field(default_factory=dict)
    discord: dict[str, Any] = Field(default_factory=dict)


class ProviderSettings(BaseSettings):
    """LLM provider settings container."""

    openai: dict[str, Any] = Field(default_factory=dict)
    anthropic: dict[str, Any] = Field(default_factory=dict)
    gemini: dict[str, Any] = Field(default_factory=dict)


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_prefix="AETHERPACK_",
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Core settings
    debug: bool = False
    data_dir: Path = Path("data")
    plugins_dir: Path = Path("plugins")
    default_provider: str = "openai"

    # Nested settings
    bot: BotSettings = Field(default_factory=BotSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    api: APISettings = Field(default_factory=APISettings)
    platforms: PlatformSettings = Field(default_factory=PlatformSettings)
    providers: ProviderSettings = Field(default_factory=ProviderSettings)

    @classmethod
    def from_file(cls, path: str | Path) -> Settings:
        """Load settings from YAML/JSON file."""
        import json

        path = Path(path)
        if not path.exists():
            return cls()

        content = path.read_text()

        if path.suffix in (".yaml", ".yml"):
            try:
                import yaml

                data = yaml.safe_load(content)
            except ImportError as e:
                raise ImportError("PyYAML required for YAML config: pip install pyyaml") from e
        else:
            data = json.loads(content)

        return cls(**data) if data else cls()

    def save(self, path: str | Path) -> None:
        """Save settings to file."""
        import json

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.suffix in (".yaml", ".yml"):
            try:
                import yaml

                content = yaml.dump(self.model_dump(), default_flow_style=False)
            except ImportError:
                content = json.dumps(self.model_dump(), indent=2)
        else:
            content = json.dumps(self.model_dump(), indent=2)

        path.write_text(content)
