# Hermes Core Integration

Hermes currently exposes `pre_llm_call` for context injection, not for replacing
the provider/model before a request. Automatic model routing therefore needs a
small core integration until Hermes grows a first-class model-routing hook.

## Desired Contract

Before each user turn, Hermes should call:

```python
from agent.smart_model_routing import resolve_smart_model_route

route = resolve_smart_model_route(
    user_message,
    config,
    primary_model,
    primary_runtime,
)
```

Then use:

- `route["model"]`
- `route["runtime"]`
- `route.get("reasoning_config")`
- `route["signature"]`

If the route cannot be resolved, the router returns the primary model.

## Current Integration Points

The originating implementation integrates the router at these Hermes surfaces:

- `cli.py`: `HermesCLI._resolve_turn_agent_config`
- `gateway/run.py`: `GatewayRunner._resolve_turn_agent_config`
- `tui_gateway/server.py`: route the live TUI agent before `run_conversation`
- `hermes_cli/config.py`: add `smart_model_routing` defaults
- `cli-config.yaml.example`: document tiered config

The TUI path is important for Hermes Desktop. It reuses a live `AIAgent`, so the
integration must call `agent.switch_model(...)` before each turn when the route
changes, and must update `agent.reasoning_config` for tier-specific thinking
settings.

## Recommended Future Hook

A cleaner upstream hook would be:

```python
ctx.register_hook("resolve_model_route", callback)
```

With kwargs:

```python
{
    "user_message": user_message,
    "config": config,
    "primary_model": primary_model,
    "primary_runtime": primary_runtime,
    "platform": platform,
    "session_id": session_id,
}
```

And return:

```python
{
    "model": "...",
    "runtime": {...},
    "reasoning_config": {"enabled": True, "effort": "medium"},
    "metadata": {"tier": "code", "reason": "codeish"}
}
```

Once that hook exists, this plugin can register the router directly and no core
patch will be needed.
