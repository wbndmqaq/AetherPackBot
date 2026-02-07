"""Configuration management routes."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()

# Default config path
CONFIG_PATH = Path("config.yaml")


class ConfigResponse(BaseModel):
    """Configuration response."""

    content: str


class ConfigUpdateRequest(BaseModel):
    """Configuration update request."""

    content: str


@router.get("")
async def get_config() -> ConfigResponse:
    """Get current configuration."""
    if not CONFIG_PATH.exists():
        # Try example config
        example_path = Path("config.example.yaml")
        if example_path.exists():
            return ConfigResponse(content=example_path.read_text(encoding="utf-8"))
        return ConfigResponse(content="# 配置文件不存在\n")

    return ConfigResponse(content=CONFIG_PATH.read_text(encoding="utf-8"))


@router.post("")
async def update_config(body: ConfigUpdateRequest) -> dict[str, str]:
    """Update configuration."""
    try:
        # Validate YAML syntax
        import yaml
        yaml.safe_load(body.content)

        # Backup existing config
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix(".yaml.bak")
            backup_path.write_text(CONFIG_PATH.read_text(encoding="utf-8"), encoding="utf-8")

        # Write new config
        CONFIG_PATH.write_text(body.content, encoding="utf-8")

        return {"status": "saved", "message": "配置已保存"}
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"YAML 语法错误: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/reload")
async def reload_config(request: Request) -> dict[str, str]:
    """Reload configuration from file."""
    engine = request.app.state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    try:
        from aetherpackbot.config.settings import Settings

        if CONFIG_PATH.exists():
            new_settings = Settings.from_file(CONFIG_PATH)
            engine._settings = new_settings
            return {"status": "reloaded", "message": "配置已重新加载"}
        else:
            raise HTTPException(status_code=404, detail="配置文件不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
