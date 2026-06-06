"""Hermes Smart Model Routing plugin."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .router import preview_route


def _hermes_home() -> Path:
    try:
        from hermes_constants import get_hermes_home

        return get_hermes_home()
    except Exception:
        return Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes")


def _load_config() -> dict[str, Any]:
    try:
        from hermes_cli.config import load_config

        return load_config()
    except Exception:
        pass
    path = _hermes_home() / "config.yaml"
    if not path.exists():
        return {}
    try:
        import yaml

        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return {}


def _primary_from_config(cfg: dict[str, Any]) -> tuple[str, str]:
    model_cfg = cfg.get("model")
    if isinstance(model_cfg, dict):
        return (
            str(model_cfg.get("default") or "").strip(),
            str(model_cfg.get("provider") or "").strip(),
        )
    if isinstance(model_cfg, str):
        return model_cfg.strip(), ""
    return "", ""


def _preview_handler(args: dict[str, Any], **_kwargs: Any) -> str:
    message = args.get("message", "")
    cfg = _load_config()
    primary_model, primary_provider = _primary_from_config(cfg)
    route = preview_route(
        message,
        cfg,
        primary_model=primary_model,
        primary_provider=primary_provider,
    )
    return json.dumps(route, ensure_ascii=False)


def register(ctx) -> None:
    """Register plugin tools.

    Automatic model switching currently needs the Hermes core integration
    described in ``patches/core-integration.md``.  This plugin still provides
    a preview tool and a stable router module for that integration to call.
    """
    ctx.register_tool(
        name="smart_model_route_preview",
        toolset="smart_model_routing",
        schema={
            "name": "smart_model_route_preview",
            "description": "Preview which smart-model-routing tier and model a message would use.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "User message to classify.",
                    }
                },
                "required": ["message"],
            },
        },
        handler=_preview_handler,
        description="Preview Hermes smart model routing decisions.",
        emoji="⇄",
    )
