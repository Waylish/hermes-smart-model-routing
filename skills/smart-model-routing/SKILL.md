---
name: smart-model-routing
description: Route Hermes turns across configured models.
version: 0.1.0
author: Waylish (@Waylish), with Hermes Agent/Codex
license: MIT
platforms: [windows, linux, macos]
tags: [models, routing, plugin]
category: productivity
metadata:
  hermes:
    tags: [models, routing, plugin]
    category: productivity
    related_skills: []
    config:
      - smart_model_routing
---

# Smart Model Routing

Use this skill when the user wants Hermes Agent to configure, test, tune, or
explain smart per-turn routing across multiple configured model APIs.

中文说明在英文说明之后。 / Chinese instructions follow the English section.

## English

### Ground Rules

- Treat this skill as a routing workflow and tuning guide. The skill itself does
  not replace Hermes core model selection.
- Use the `smart_model_route_preview` tool to inspect routing decisions when the
  plugin is installed.
- Keep secrets out of `config.yaml`; use `api_key_env` and store keys in Hermes'
  secret environment file.
- Do not claim automatic switching is active unless Hermes has either native
  `resolve_model_route` support or the documented core integration applied.
- Prefer conservative routing. Ambiguous, high-risk, long, code-heavy, or
  analysis-heavy tasks should use the stronger tier.

### Workflow

1. Inspect the `smart_model_routing` config block.
2. Confirm `enabled: true` and that each intended tier has `provider`, `model`,
   and either `api_key_env` or inherited provider credentials.
3. Preview representative prompts with `smart_model_route_preview`.
4. Compare the previewed tier, reason, provider, model, and reasoning settings
   against the user's intent.
5. Tune thresholds first, then keywords, then tier model choices.
6. If automatic switching is missing, explain that preview works but per-turn
   switching needs native `resolve_model_route` support or the integration notes
   in `patches/core-integration.md`.

### Recommended Tiers

| Tier | Use For | Typical Model |
|---|---|---|
| `cheap` | Short greetings, tiny factual questions, low-risk text | `deepseek-v4-flash` |
| `standard` | Normal explanations and medium prompts | `kimi-k2.6` |
| `code` | Code, tracebacks, refactors, tests, repo work | `kimi-for-coding` |
| `reasoning` | Multi-step analysis, strategy, research, proof, forecasting | `deepseek-v4-pro` |
| `long_context` | `@file` references, whole documents, large prompts | `kimi-k2-thinking-turbo` |
| `media` | Images or non-text attachments | A vision-capable primary model, such as `MiniMax-M3` |

Missing tiers should fall back to Hermes' primary `model:` config.

### Preview Cases

Use cases like these when validating a config:

| Prompt | Expected Tier | Why |
|---|---|---|
| `hello` | `cheap` | Short text |
| `Explain TCP congestion control in practical terms.` | `standard` | Medium explanation |
| `Fix this traceback and add tests: ...` | `code` | Code/debug keyword |
| `Analyze 2026-2028 AI chip supply chain risk...` | `reasoning` | Strategic analysis |
| `Summarize @docs/spec.md and identify contradictions.` | `long_context` | Context reference |
| A message with an attached image | `media` | Non-text input |

### Tuning Order

Tune in this order:

1. `max_simple_chars`, `max_simple_words`, `max_simple_lines`
2. `max_standard_chars`, `max_standard_words`, `max_standard_lines`
3. `code_keywords`, `reasoning_keywords`, `long_context_keywords`
4. Tier models and reasoning settings

If a prompt routes too cheaply, lower the relevant threshold or add a keyword.
If a prompt over-routes to an expensive model, raise the threshold or remove an
overbroad keyword.

### Reporting Results

When reporting a route, include:

- selected tier
- reason
- provider/model
- reasoning settings, if any
- whether the result is preview-only or automatic switching is active
- fallback behavior if the tier is missing or credentials are unavailable

## 中文

### 基本原则

- 把这个 skill 当成“路由配置与调参手册”。skill 本身不会直接替换 Hermes
  核心的模型选择。
- 插件安装后，用 `smart_model_route_preview` 预览某条消息会走哪个 tier。
- API key 不要写进 `config.yaml`；配置里写 `api_key_env`，密钥放在 Hermes
  的环境密钥文件里。
- 不要声称自动切换已经生效，除非 Hermes 已经有原生 `resolve_model_route`
  支持，或已经应用 `patches/core-integration.md` 里的 core integration。
- 路由策略保持保守：不确定、高风险、长上下文、代码、复杂分析任务优先走更强档位。

### 工作流

1. 检查 `smart_model_routing` 配置段。
2. 确认 `enabled: true`，并且目标 tier 都配置了 `provider`、`model`，
   以及 `api_key_env` 或可继承的 provider 凭据。
3. 用 `smart_model_route_preview` 预览代表性 prompt。
4. 对照用户意图检查 tier、reason、provider、model 和 reasoning 设置。
5. 先调阈值，再调关键词，最后替换各 tier 的模型。
6. 如果没有自动切换能力，说明当前只能预览；每轮自动切换需要 Hermes 原生
   `resolve_model_route` 支持或 core integration。

### 推荐档位

| Tier | 适合任务 | 典型模型 |
|---|---|---|
| `cheap` | 问候、短问题、低风险文本 | `deepseek-v4-flash` |
| `standard` | 普通解释、中等长度 prompt | `kimi-k2.6` |
| `code` | 代码、报错、重构、测试、仓库任务 | `kimi-for-coding` |
| `reasoning` | 多步分析、策略、研究、证明、预测 | `deepseek-v4-pro` |
| `long_context` | `@file` 引用、整份文档、大 prompt | `kimi-k2-thinking-turbo` |
| `media` | 图片或非文本附件 | 支持视觉的主模型，例如 `MiniMax-M3` |

没有配置的 tier 应回退到 Hermes 普通 `model:` 主模型。

### 预览用例

| Prompt | 预期 Tier | 原因 |
|---|---|---|
| `hello` | `cheap` | 短文本 |
| `解释 TCP 拥塞控制的实用逻辑。` | `standard` | 普通解释 |
| `修复这个 traceback，并补 3 个测试：...` | `code` | 代码/调试关键词 |
| `分析 2026-2028 年 AI 芯片供应链风险...` | `reasoning` | 战略分析 |
| `Summarize @docs/spec.md and identify contradictions.` | `long_context` | 上下文引用 |
| 带图片附件的消息 | `media` | 非文本输入 |

### 调参顺序

1. `max_simple_chars`, `max_simple_words`, `max_simple_lines`
2. `max_standard_chars`, `max_standard_words`, `max_standard_lines`
3. `code_keywords`, `reasoning_keywords`, `long_context_keywords`
4. 各 tier 的模型和 reasoning 设置

如果任务被分到太便宜的模型，降低对应阈值或增加关键词。如果任务过度路由到昂贵模型，
提高阈值或删掉过宽的关键词。

### 汇报格式

汇报路由结果时包含：

- 选中的 tier
- 触发原因
- provider/model
- reasoning 设置
- 当前是 preview-only，还是自动切换已生效
- tier 缺失或凭据不可用时的 fallback 行为
