"""Tiered per-turn model routing for Hermes Agent."""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Mapping

logger = logging.getLogger(__name__)


DEFAULT_MAX_SIMPLE_CHARS = 500
DEFAULT_MAX_SIMPLE_WORDS = 80
DEFAULT_MAX_SIMPLE_LINES = 6
DEFAULT_MAX_STANDARD_CHARS = 1800
DEFAULT_MAX_STANDARD_WORDS = 280
DEFAULT_MAX_STANDARD_LINES = 18

DEFAULT_CODE_KEYWORDS = (
    "implement",
    "refactor",
    "debug",
    "fix",
    "failing",
    "traceback",
    "stack trace",
    "write tests",
    "unit test",
    "code",
    "代码",
    "实现",
    "修复",
    "调试",
    "重构",
    "测试",
)

DEFAULT_REASONING_KEYWORDS = (
    "review",
    "architecture",
    "design",
    "analyze",
    "analyse",
    "compare",
    "research",
    "prove",
    "derive",
    "optimize",
    "profile",
    "deploy",
    "database",
    "migration",
    "security",
    "strategy",
    "forecast",
    "分析",
    "架构",
    "设计",
    "论文",
    "研究",
    "推理",
    "比较",
    "预测",
)

DEFAULT_LONG_CONTEXT_KEYWORDS = (
    "long context",
    "full document",
    "entire file",
    "summarize the document",
    "summarise the document",
    "长上下文",
    "全文",
    "整篇",
    "整份",
    "文档",
)

CODEISH_MARKERS = (
    "```",
    "diff --git",
    "traceback",
    "exception:",
    "error:",
    "def ",
    "class ",
    "import ",
    "from ",
    "function ",
    "const ",
    "let ",
    "var ",
    "select ",
    "insert ",
    "update ",
    "delete ",
    "<html",
)

CONTEXT_REFERENCE_RE = re.compile(r"(?<!\w)@[^\s@]+")


def _enabled(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}
    return bool(value)


def _as_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


def _as_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _as_list(value: Any, default: tuple[str, ...]) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return list(default)


def _keywords(value: Any, default: tuple[str, ...]) -> list[str]:
    parsed = _as_list(value, default)
    return parsed or list(default)


def _matches_any(lowered: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in lowered for keyword in keywords if keyword)


def _configured_secret(entry: Mapping[str, Any]) -> str | None:
    api_key = str(entry.get("api_key") or "").strip()
    if api_key:
        return api_key
    env_name = str(entry.get("api_key_env") or entry.get("key_env") or "").strip()
    if env_name:
        return os.getenv(env_name, "").strip() or None
    return None


def extract_text_and_media_flag(content: Any) -> tuple[str, bool]:
    """Return readable text plus whether the message includes non-text media."""
    if isinstance(content, str):
        return content, False

    if isinstance(content, list):
        chunks: list[str] = []
        has_media = False
        for part in content:
            if isinstance(part, str):
                chunks.append(part)
                continue
            if not isinstance(part, Mapping):
                continue
            part_type = str(part.get("type") or "").lower()
            if part_type in {"text", "input_text"}:
                chunks.append(str(part.get("text") or ""))
            elif "text" in part and not part_type:
                chunks.append(str(part.get("text") or ""))
            else:
                has_media = True
        return "\n".join(chunk for chunk in chunks if chunk), has_media

    if isinstance(content, Mapping):
        if "text" in content:
            return str(content.get("text") or ""), False
        return "", True

    return str(content or ""), False


def classify_message(
    user_message: Any,
    routing_config: Mapping[str, Any] | None = None,
) -> tuple[str, str]:
    """Classify a user message into a routing tier with a short reason."""
    cfg = _as_mapping(routing_config)
    text, has_media = extract_text_and_media_flag(user_message)
    text = (text or "").strip()
    lowered = text.lower()

    if not text:
        return "primary", "empty"
    if has_media and not _enabled(cfg.get("allow_media")):
        return "media", "media"
    if CONTEXT_REFERENCE_RE.search(text):
        return "long_context", "context-reference"

    code_keywords = _keywords(cfg.get("code_keywords"), DEFAULT_CODE_KEYWORDS)
    reasoning_keywords = _keywords(
        cfg.get("reasoning_keywords"),
        DEFAULT_REASONING_KEYWORDS,
    )
    long_context_keywords = _keywords(
        cfg.get("long_context_keywords"),
        DEFAULT_LONG_CONTEXT_KEYWORDS,
    )
    legacy_complex_keywords = _as_list(cfg.get("complex_keywords"), ())

    if _matches_any(lowered, code_keywords):
        return "code", "code-keyword"
    if any(marker in lowered for marker in CODEISH_MARKERS):
        return "code", "codeish"
    if _matches_any(lowered, long_context_keywords):
        return "long_context", "long-context-keyword"
    if _matches_any(lowered, reasoning_keywords):
        return "reasoning", "reasoning-keyword"
    if _matches_any(lowered, legacy_complex_keywords):
        return "reasoning", "complex-keyword"

    word_count = len(re.findall(r"\S+", text))
    line_count = text.count("\n") + 1

    if (
        len(text) <= _as_int(cfg.get("max_simple_chars"), DEFAULT_MAX_SIMPLE_CHARS)
        and word_count <= _as_int(cfg.get("max_simple_words"), DEFAULT_MAX_SIMPLE_WORDS)
        and line_count <= _as_int(cfg.get("max_simple_lines"), DEFAULT_MAX_SIMPLE_LINES)
    ):
        return "cheap", "short-text"

    if (
        len(text) <= _as_int(cfg.get("max_standard_chars"), DEFAULT_MAX_STANDARD_CHARS)
        and word_count <= _as_int(cfg.get("max_standard_words"), DEFAULT_MAX_STANDARD_WORDS)
        and line_count <= _as_int(cfg.get("max_standard_lines"), DEFAULT_MAX_STANDARD_LINES)
    ):
        return "standard", "medium-text"

    return "long_context", "too-large"


def _primary_route(
    model: str,
    runtime: Mapping[str, Any],
    *,
    reason: str = "primary",
) -> dict[str, Any]:
    runtime_copy = {
        "api_key": runtime.get("api_key"),
        "base_url": runtime.get("base_url"),
        "provider": runtime.get("provider"),
        "api_mode": runtime.get("api_mode"),
        "command": runtime.get("command"),
        "args": list(runtime.get("args") or []),
        "credential_pool": runtime.get("credential_pool"),
    }
    return {
        "model": model,
        "runtime": runtime_copy,
        "signature": (
            model,
            runtime_copy["provider"],
            runtime_copy["base_url"],
            runtime_copy["api_mode"],
            runtime_copy["command"],
            tuple(runtime_copy["args"]),
            None,
        ),
        "smart_model_routing": {"used": False, "tier": "primary", "reason": reason},
    }


def _legacy_model_config(routing_config: Mapping[str, Any], tier: str) -> dict[str, Any]:
    raw = routing_config.get(f"{tier}_model")
    if raw is None and tier == "cheap":
        raw = routing_config.get("cheap_model")
    if isinstance(raw, str):
        return {
            "provider": routing_config.get(f"{tier}_provider") or routing_config.get("provider"),
            "model": raw,
            "base_url": routing_config.get(f"{tier}_base_url") or routing_config.get("base_url"),
            "api_key": routing_config.get(f"{tier}_api_key") or routing_config.get("api_key"),
            "api_key_env": routing_config.get(f"{tier}_api_key_env") or routing_config.get("api_key_env"),
            "api_mode": routing_config.get(f"{tier}_api_mode") or routing_config.get("api_mode"),
        }
    return _as_mapping(raw)


def _merge_entry(parent: Mapping[str, Any], child: Any) -> dict[str, Any]:
    child_map = {"model": child} if isinstance(child, str) else _as_mapping(child)
    merged = {
        key: parent.get(key)
        for key in (
            "provider",
            "base_url",
            "api_key",
            "api_key_env",
            "key_env",
            "api_mode",
            "reasoning",
            "reasoning_enabled",
            "reasoning_effort",
        )
        if parent.get(key) not in (None, "")
    }
    merged.update(child_map)
    return merged


def _tier_candidates(
    routing_config: Mapping[str, Any],
    tier: str,
) -> list[dict[str, Any]]:
    tiers = _as_mapping(routing_config.get("tiers"))
    raw = tiers.get(tier)
    used_tiers_entry = raw is not None
    if raw is None:
        raw = _legacy_model_config(routing_config, tier)
    if isinstance(raw, str):
        return [{"model": raw}]
    entry = _as_mapping(raw)
    if not entry or _enabled(entry.get("enabled", True), default=True) is False:
        return []
    candidates = entry.get("candidates") or entry.get("models")
    if isinstance(candidates, (list, tuple)):
        return [_merge_entry(entry, candidate) for candidate in candidates]
    if used_tiers_entry and not str(entry.get("model") or "").strip():
        legacy = _legacy_model_config(routing_config, tier)
        if legacy:
            return [legacy]
        return []
    return [entry]


def _reasoning_config(entry: Mapping[str, Any]) -> dict[str, Any] | None:
    raw = entry.get("reasoning")
    if raw is None and ("reasoning_enabled" in entry or "reasoning_effort" in entry):
        raw = {
            "enabled": entry.get("reasoning_enabled", True),
            "effort": entry.get("reasoning_effort", ""),
        }
    if isinstance(raw, bool):
        return {"enabled": raw}
    if isinstance(raw, str):
        value = raw.strip().lower()
        if value in {"", "default", "inherit"}:
            return None
        if value in {"off", "none", "false", "disabled", "disable"}:
            return {"enabled": False}
        return {"enabled": True, "effort": value}
    if isinstance(raw, Mapping):
        cfg = {key: value for key, value in dict(raw).items() if value not in (None, "")}
        if not cfg:
            return None
        effort = str(cfg.get("effort") or "").strip()
        if effort and "enabled" not in cfg:
            cfg["enabled"] = True
        return cfg
    return None


def _freeze_reasoning_config(config: Mapping[str, Any] | None) -> tuple | None:
    if not isinstance(config, Mapping):
        return None
    return tuple(sorted((str(key), str(value)) for key, value in config.items()))


def preview_route(
    user_message: Any,
    config: Mapping[str, Any] | None,
    *,
    primary_model: str = "",
    primary_provider: str = "",
) -> dict[str, Any]:
    """Return the configured tier/model without resolving credentials."""
    root_config = _as_mapping(config)
    routing_config = _as_mapping(root_config.get("smart_model_routing"))
    if not _enabled(routing_config.get("enabled")):
        return {
            "tier": "primary",
            "reason": "disabled",
            "model": primary_model,
            "provider": primary_provider,
            "used": False,
        }
    tier, reason = classify_message(user_message, routing_config)
    candidates = _tier_candidates(routing_config, tier)
    if not candidates:
        return {
            "tier": "primary",
            "reason": f"{tier}-missing",
            "model": primary_model,
            "provider": primary_provider,
            "used": False,
        }
    chosen = candidates[0]
    model = str(chosen.get("model") or "").strip()
    if not model or model.lower() in {"primary", "default", "inherit"}:
        return {
            "tier": "primary",
            "reason": f"{tier}-primary",
            "model": primary_model,
            "provider": primary_provider,
            "used": False,
        }
    return {
        "tier": tier,
        "reason": reason,
        "model": model,
        "provider": str(chosen.get("provider") or primary_provider or "").strip(),
        "reasoning": _reasoning_config(chosen),
        "used": True,
    }


def resolve_smart_model_route(
    user_message: Any,
    config: Mapping[str, Any] | None,
    primary_model: str,
    primary_runtime: Mapping[str, Any],
) -> dict[str, Any]:
    """Resolve the effective per-turn route.

    This function expects to run inside Hermes Agent, where
    ``hermes_cli.runtime_provider.resolve_runtime_provider`` is importable.
    """
    root_config = _as_mapping(config)
    routing_config = _as_mapping(root_config.get("smart_model_routing"))
    primary = _primary_route(primary_model, primary_runtime)
    if not _enabled(routing_config.get("enabled")):
        return primary

    tier, reason = classify_message(user_message, routing_config)
    if tier == "primary":
        primary["smart_model_routing"] = {
            "used": False,
            "tier": "primary",
            "reason": reason,
        }
        return primary

    candidates = _tier_candidates(routing_config, tier)
    if not candidates:
        primary["smart_model_routing"] = {
            "used": False,
            "tier": "primary",
            "reason": f"{tier}-missing",
        }
        return primary

    last_error = ""
    for candidate in candidates:
        model = str(candidate.get("model") or "").strip()
        if not model:
            last_error = "model-missing"
            continue
        if model.lower() in {"primary", "default", "inherit"}:
            primary["smart_model_routing"] = {
                "used": False,
                "tier": "primary",
                "reason": f"{tier}-primary",
            }
            return primary

        provider = (
            str(candidate.get("provider") or primary_runtime.get("provider") or "auto")
            .strip()
            or "auto"
        )
        base_url = str(candidate.get("base_url") or "").strip() or None
        api_key = _configured_secret(candidate)

        try:
            from hermes_cli.runtime_provider import resolve_runtime_provider

            runtime = resolve_runtime_provider(
                requested=provider,
                explicit_api_key=api_key,
                explicit_base_url=base_url,
                target_model=model,
            )
        except Exception as exc:
            last_error = "resolve-failed"
            logger.warning(
                "smart_model_routing %s route failed for provider=%s model=%s: %s",
                tier,
                provider,
                model,
                exc,
            )
            continue

        api_mode = str(candidate.get("api_mode") or "").strip()
        if api_mode:
            runtime["api_mode"] = api_mode

        runtime_copy = {
            "api_key": runtime.get("api_key"),
            "base_url": runtime.get("base_url"),
            "provider": runtime.get("provider"),
            "api_mode": runtime.get("api_mode"),
            "command": runtime.get("command"),
            "args": list(runtime.get("args") or []),
            "credential_pool": runtime.get("credential_pool"),
        }
        reasoning_config = _reasoning_config(candidate)
        logger.info(
            "smart_model_routing: tier=%s provider=%s model=%s reason=%s",
            tier,
            runtime_copy["provider"],
            model,
            reason,
        )
        route = {
            "model": model,
            "runtime": runtime_copy,
            "signature": (
                model,
                runtime_copy["provider"],
                runtime_copy["base_url"],
                runtime_copy["api_mode"],
                runtime_copy["command"],
                tuple(runtime_copy["args"]),
                _freeze_reasoning_config(reasoning_config),
            ),
            "smart_model_routing": {"used": True, "tier": tier, "reason": reason},
        }
        if reasoning_config is not None:
            route["reasoning_config"] = reasoning_config
        return route

    primary["smart_model_routing"] = {
        "used": False,
        "tier": "primary",
        "reason": last_error or f"{tier}-unresolved",
    }
    return primary
