# Hermes Core Integration / Hermes 核心接入说明

中文 | [English](#english)

Hermes 当前公开的 `pre_llm_call` hook 主要用于注入上下文，不能在请求发送前合法替换 provider/model。因此，真正的自动模型切换需要 Hermes core 在每轮对话发起前调用路由器。

本文件说明需要接入的位置和推荐的未来 hook 设计。

## 接入目标

每一轮用户消息进入模型调用前，Hermes 应调用：

```python
from agent.smart_model_routing import resolve_smart_model_route

route = resolve_smart_model_route(
    user_message,
    config,
    primary_model,
    primary_runtime,
)
```

然后使用：

- `route["model"]`
- `route["runtime"]`
- `route.get("reasoning_config")`
- `route["signature"]`

如果某个 tier 没配置、凭据缺失、provider 解析失败，路由器会返回主模型。

## 当前需要接入的位置

参考实现接入了这些 Hermes 表面：

- `cli.py`: `HermesCLI._resolve_turn_agent_config`
- `gateway/run.py`: `GatewayRunner._resolve_turn_agent_config`
- `tui_gateway/server.py`: 桌面版/TUI 每轮 `run_conversation` 前切换 live `AIAgent`
- `hermes_cli/config.py`: 增加 `smart_model_routing` 默认配置
- `cli-config.yaml.example`: 增加 tiered routing 配置示例

## 桌面版/TUI 注意点

Hermes Desktop 走 TUI 后端，并且会复用同一个 live `AIAgent`。因此不能只在启动时决定模型，必须在每轮发送前：

1. 调用路由器得到目标模型。
2. 如果目标模型与当前 agent 不一致，调用 `agent.switch_model(...)`。
3. 更新 `agent.reasoning_config`，以支持不同 tier 的 thinking 开关。
4. 刷新 session info，让状态栏显示当前模型。

## CLI/Gateway 注意点

CLI 和 Gateway 可以在创建 agent 前解析 route。缓存签名需要包含：

- model
- provider
- base_url
- api_mode
- ACP command/args
- tier-specific `reasoning_config`

否则同一个模型但 thinking 设置不同的两轮可能错误复用旧 agent。

## 推荐的未来原生 hook

更干净的上游接口可以是：

```python
ctx.register_hook("resolve_model_route", callback)
```

传入：

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

返回：

```python
{
    "model": "...",
    "runtime": {...},
    "reasoning_config": {"enabled": True, "effort": "medium"},
    "metadata": {"tier": "code", "reason": "codeish"}
}
```

有了这个 hook 后，本插件就可以直接注册路由回调，不再需要 core patch。

---

## English

Hermes currently exposes `pre_llm_call` mainly for context injection. It cannot safely replace the provider/model before the request is sent. Automatic model switching therefore needs Hermes core to call the router before each turn.

This file describes the required integration points and a recommended future hook design.

## Integration Goal

Before each user turn reaches the model request, Hermes should call:

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

If a tier is missing, credentials are unavailable, or provider resolution fails, the router returns the primary model.

## Current Integration Points

The reference implementation integrates these Hermes surfaces:

- `cli.py`: `HermesCLI._resolve_turn_agent_config`
- `gateway/run.py`: `GatewayRunner._resolve_turn_agent_config`
- `tui_gateway/server.py`: Desktop/TUI switches the live `AIAgent` before each `run_conversation`
- `hermes_cli/config.py`: adds `smart_model_routing` defaults
- `cli-config.yaml.example`: documents tiered routing config

## Desktop/TUI Notes

Hermes Desktop uses the TUI backend and reuses one live `AIAgent`. The route cannot be decided only at startup. Before each turn:

1. Call the router to get the target route.
2. If the target differs from the current agent, call `agent.switch_model(...)`.
3. Update `agent.reasoning_config` so each tier can control thinking settings.
4. Emit refreshed session info so the status bar can show the active model.

## CLI/Gateway Notes

CLI and Gateway can resolve the route before creating an agent. Cache signatures should include:

- model
- provider
- base_url
- api_mode
- ACP command/args
- tier-specific `reasoning_config`

Otherwise, two turns using the same model with different thinking settings may incorrectly reuse the previous agent.

## Recommended Future Hook

A cleaner upstream interface would be:

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

Once that hook exists, this plugin can register the router callback directly and no core patch will be needed.
