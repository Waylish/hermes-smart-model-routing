# Hermes Smart Model Routing

中文 | [English](#english)

Hermes Smart Model Routing 是一个面向 [Hermes Agent](https://github.com/NousResearch/hermes-agent) 的分层模型路由插件包。它会根据每一轮用户请求的任务形态，把请求分配给更合适的模型档位：短问走更快更便宜的模型，代码和推理任务走更强的模型，长上下文和媒体任务走更稳的模型。

> 当前 Hermes 的公开插件 hook 还不能在 LLM 请求发出前直接替换 provider/model。本仓库因此采用“插件 + core integration”结构：插件提供路由器、预览工具、Skill 和配置模板；自动切换需要 Hermes core 在每轮请求前调用路由器。详见 [Core Integration](patches/core-integration.md)。

## 适合谁用

- 你在 Hermes 里同时配置了多个模型 API。
- 你希望简单问题不总是消耗最强模型。
- 你希望代码、推理、长上下文、图片等任务自动切到不同模型。
- 你想把模型选择策略写进配置，而不是每次手动 `/model`。

## 默认路由策略

默认示例配置使用以下档位，所有模型都可以替换：

| 任务类型 | Tier | 默认模型 |
|---|---|---|
| 短文本、轻量问答 | `cheap` | `deepseek/deepseek-v4-flash` |
| 普通解释、中等长度问答 | `standard` | `kimi-coding/kimi-k2.6` |
| 代码、报错、测试、重构 | `code` | `kimi-coding/kimi-for-coding` |
| 复杂分析、研究、比较、预测 | `reasoning` | `deepseek/deepseek-v4-pro` |
| `@file` 引用、长文档、长上下文 | `long_context` | `kimi-coding/kimi-k2-thinking-turbo` |
| 图片或非文本附件 | `media` | 你的主模型，例如 `minimax-cn/MiniMax-M3` |

路由是保守的：缺少配置、模型解析失败或无法判断时，会回退到 Hermes 的主模型。

## 仓库内容

```text
plugin.yaml                         # Hermes plugin manifest
__init__.py                         # 注册 smart_model_route_preview 工具
router.py                           # 路由分类与模型解析核心
config.example.yaml                 # 可复制到 config.yaml 的配置模板
skills/smart-model-routing/SKILL.md # 给 Hermes/Codex 使用的调参与测试 Skill
scripts/install.py                  # 本地安装脚本
patches/core-integration.md         # Hermes core 接入说明
tests/test_router.py                # 单元测试
```

## 安装插件

在本仓库根目录运行：

```powershell
python scripts/install.py
```

Windows 桌面版默认安装到：

```text
%LOCALAPPDATA%\hermes\plugins\smart-model-routing
```

其他平台默认使用 `$HERMES_HOME/plugins/smart-model-routing`，没有 `HERMES_HOME` 时使用 `~/.hermes/plugins/smart-model-routing`。

如果你想指定目录：

```powershell
python scripts/install.py --plugin-dir C:\path\to\smart-model-routing
```

## 配置

把 [config.example.yaml](config.example.yaml) 里的 `smart_model_routing` 段复制到 Hermes 的 `config.yaml`。

示例：

```yaml
smart_model_routing:
  enabled: true
  tiers:
    cheap:
      provider: deepseek
      model: deepseek-v4-flash
      api_key_env: DEEPSEEK_API_KEY
      reasoning:
        enabled: false
    code:
      provider: kimi-coding
      model: kimi-for-coding
      api_key_env: KIMI_API_KEY
      reasoning:
        enabled: true
        effort: medium
```

API key 仍然放在 `.env`，不要写进 `config.yaml`：

```text
DEEPSEEK_API_KEY=...
KIMI_API_KEY=...
MINIMAX_CN_API_KEY=...
```

## 预览某条消息会走哪个模型

插件会注册一个工具：

```text
smart_model_route_preview
```

示例输入：

```json
{"message": "Fix this traceback and add tests"}
```

典型输出：

```json
{
  "tier": "code",
  "reason": "code-keyword",
  "model": "kimi-for-coding",
  "provider": "kimi-coding",
  "used": true
}
```

这个工具只预览路由，不会真实调用 LLM。

## 自动切换如何生效

目前 Hermes 需要在以下入口调用路由器：

- CLI: `HermesCLI._resolve_turn_agent_config`
- Gateway: `GatewayRunner._resolve_turn_agent_config`
- Desktop/TUI: 每轮 `run_conversation` 前切换 live `AIAgent`

如果你使用的是已经打过 integration patch 的 Hermes，本插件会作为稳定的路由模块和预览工具使用。如果你要把它接入新的 Hermes checkout，请先阅读 [patches/core-integration.md](patches/core-integration.md)。

## 本地测试

```powershell
python -m unittest discover -s tests
```

预期：

```text
Ran 6 tests
OK
```

## 调参建议

先调阈值：

```yaml
max_simple_chars: 500
max_simple_words: 80
max_simple_lines: 6
max_standard_chars: 1800
max_standard_words: 280
max_standard_lines: 18
```

再加关键词：

```yaml
code_keywords:
  - traceback
  - unit test
reasoning_keywords:
  - strategy
  - forecast
long_context_keywords:
  - full document
  - entire file
```

建议保持保守：不确定的任务宁可走强模型。

## Roadmap

- 增加 Hermes 原生 `resolve_model_route` hook 后，去掉 core patch 依赖。
- 增加 CLI 命令，直接运行路由预览和配置检查。
- 增加按成本、延迟、上下文窗口、失败率的动态候选模型选择。
- 增加更多 provider 的推荐模板。

## 许可证

MIT

---

## English

Hermes Smart Model Routing is a tiered per-turn routing package for [Hermes Agent](https://github.com/NousResearch/hermes-agent). It routes each user turn to a model tier that better matches the task: lightweight prompts can use faster or cheaper models, while code, reasoning, long-context, and media turns can use stronger or safer models.

> Hermes' current public plugin hooks can observe LLM calls and inject context, but they cannot yet replace the provider/model before a request is sent. This repository therefore uses a "plugin + core integration" design: the plugin provides the router, preview tool, Skill, and config template; automatic switching requires Hermes core to call the router before each turn. See [Core Integration](patches/core-integration.md).

## Who This Is For

- You have several model APIs configured in Hermes.
- You do not want every simple question to use your strongest model.
- You want code, reasoning, long-context, and media tasks routed differently.
- You want routing policy in config instead of manual `/model` switching.

## Default Routing Policy

The example config ships with these tiers. Every model is configurable:

| Task Type | Tier | Default Model |
|---|---|---|
| Short text and lightweight Q&A | `cheap` | `deepseek/deepseek-v4-flash` |
| Normal explanations and medium prompts | `standard` | `kimi-coding/kimi-k2.6` |
| Code, tracebacks, tests, refactors | `code` | `kimi-coding/kimi-for-coding` |
| Analysis, research, comparison, forecasting | `reasoning` | `deepseek/deepseek-v4-pro` |
| `@file` references and long-context prompts | `long_context` | `kimi-coding/kimi-k2-thinking-turbo` |
| Images or non-text attachments | `media` | Your primary model, for example `minimax-cn/MiniMax-M3` |

Routing is conservative. Missing config, resolution failures, or ambiguous cases fall back to the primary Hermes model.

## Repository Layout

```text
plugin.yaml                         # Hermes plugin manifest
__init__.py                         # Registers smart_model_route_preview
router.py                           # Classification and route resolution
config.example.yaml                 # Config template for config.yaml
skills/smart-model-routing/SKILL.md # Skill for tuning and validation
scripts/install.py                  # Local installer
patches/core-integration.md         # Hermes core integration contract
tests/test_router.py                # Unit tests
```

## Install The Plugin

From the repository root:

```powershell
python scripts/install.py
```

On Hermes Desktop for Windows, this installs to:

```text
%LOCALAPPDATA%\hermes\plugins\smart-model-routing
```

On other platforms, the installer uses `$HERMES_HOME/plugins/smart-model-routing`, or `~/.hermes/plugins/smart-model-routing` when `HERMES_HOME` is unset.

To choose an explicit destination:

```powershell
python scripts/install.py --plugin-dir C:\path\to\smart-model-routing
```

## Configure

Copy the `smart_model_routing` section from [config.example.yaml](config.example.yaml) into Hermes `config.yaml`.

Example:

```yaml
smart_model_routing:
  enabled: true
  tiers:
    cheap:
      provider: deepseek
      model: deepseek-v4-flash
      api_key_env: DEEPSEEK_API_KEY
      reasoning:
        enabled: false
    code:
      provider: kimi-coding
      model: kimi-for-coding
      api_key_env: KIMI_API_KEY
      reasoning:
        enabled: true
        effort: medium
```

Keep API keys in `.env`, not in `config.yaml`:

```text
DEEPSEEK_API_KEY=...
KIMI_API_KEY=...
MINIMAX_CN_API_KEY=...
```

## Preview A Route

The plugin registers:

```text
smart_model_route_preview
```

Example input:

```json
{"message": "Fix this traceback and add tests"}
```

Typical output:

```json
{
  "tier": "code",
  "reason": "code-keyword",
  "model": "kimi-for-coding",
  "provider": "kimi-coding",
  "used": true
}
```

The preview tool does not call an LLM.

## Automatic Switching

Hermes currently needs the router to be called from these entry points:

- CLI: `HermesCLI._resolve_turn_agent_config`
- Gateway: `GatewayRunner._resolve_turn_agent_config`
- Desktop/TUI: switch the live `AIAgent` before each `run_conversation`

If your Hermes checkout already has the integration patch, this plugin acts as the stable router module and preview surface. For a new checkout, read [patches/core-integration.md](patches/core-integration.md).

## Local Tests

```powershell
python -m unittest discover -s tests
```

Expected:

```text
Ran 6 tests
OK
```

## Tuning Tips

Start with thresholds:

```yaml
max_simple_chars: 500
max_simple_words: 80
max_simple_lines: 6
max_standard_chars: 1800
max_standard_words: 280
max_standard_lines: 18
```

Then add domain words:

```yaml
code_keywords:
  - traceback
  - unit test
reasoning_keywords:
  - strategy
  - forecast
long_context_keywords:
  - full document
  - entire file
```

Prefer conservative routing. When in doubt, send the turn to a stronger model.

## Roadmap

- Remove the core patch once Hermes adds a native `resolve_model_route` hook.
- Add CLI commands for route preview and config checks.
- Add dynamic candidate choice by cost, latency, context window, and failure rate.
- Add more provider templates.

## License

MIT
