# Hermes Smart Model Routing

Tiered per-turn model routing for Hermes Agent.

This repository packages the router behind the local Hermes setup discussed in
the originating conversation:

- short text -> DeepSeek V4 Flash
- normal explanations -> Kimi K2.6
- code/debugging/tests -> Kimi for Coding
- complex reasoning -> DeepSeek V4 Pro
- file/long-context turns -> Kimi thinking turbo
- media turns -> the primary model

The exact models are configurable.

## Current Status

Hermes Agent's public plugin hook surface can observe LLM calls and inject
context, but it cannot yet replace the provider/model before the request. For
that reason this project has two parts:

1. A Hermes plugin with a reusable router and `smart_model_route_preview` tool.
2. A small Hermes core integration point that calls the router before each turn.

See `patches/core-integration.md` for the integration contract.

## Files

```text
plugin.yaml
__init__.py
router.py
config.example.yaml
skills/smart-model-routing/SKILL.md
scripts/install.py
patches/core-integration.md
tests/test_router.py
```

## Install The Plugin

From this repository:

```powershell
python scripts/install.py
```

The script copies the plugin to:

```text
%LOCALAPPDATA%\hermes\plugins\smart-model-routing
```

On non-Windows Hermes installs it uses `$HERMES_HOME` or `~/.hermes`.

## Configure

Add a section like `config.example.yaml` to your Hermes `config.yaml`.

Keep API keys in `.env`:

```text
DEEPSEEK_API_KEY=...
KIMI_API_KEY=...
MINIMAX_CN_API_KEY=...
```

Do not put raw API keys in `config.yaml`.

## Preview A Route

After the plugin is installed and its toolset is enabled, ask Hermes to call:

```text
smart_model_route_preview({"message": "Fix this traceback and add tests"})
```

Expected result:

```json
{
  "tier": "code",
  "model": "kimi-for-coding"
}
```

## Test Locally

```powershell
python -m unittest discover -s tests
```

## License

MIT
