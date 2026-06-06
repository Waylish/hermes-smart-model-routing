---
name: smart-model-routing
description: Route Hermes turns across configured models.
---

# Smart Model Routing

Use this skill when configuring, testing, or tuning Hermes Agent's per-turn
model router.

中文说明在英文说明之后。 / Chinese instructions follow the English section.

## English

### Workflow

1. Confirm that Hermes has the core integration from `patches/core-integration.md`.
   The plugin can preview routes by itself, but automatic switching requires
   Hermes to call the router before each model request.
2. Add a `smart_model_routing` section to Hermes `config.yaml`. Start from
   `config.example.yaml`.
3. Keep API keys in `.env`; reference them with `api_key_env`.
4. Preview representative prompts with `smart_model_route_preview`.
5. Restart Hermes Desktop, TUI, CLI, or Gateway after changing plugin files or
   core integration code.

### Tier Meanings

- `cheap`: short, text-only questions.
- `standard`: medium-size normal explanations.
- `code`: code, traceback, debugging, refactoring, or tests.
- `reasoning`: analysis, research, comparison, strategy, proof, or forecasting.
- `long_context`: `@file` references or large document-style prompts.
- `media`: image or non-text attachment turns.

Missing tiers fall back to the primary model in the normal `model:` config.

### Validation Prompts

Use prompts like these:

```text
hello
```

Expected tier: `cheap`.

```text
Please give me a practical overview of TCP congestion control, including slow start and congestion avoidance.
```

Expected tier: `standard`.

````text
Fix this traceback and add tests:
```python
raise ValueError("x")
```
````

Expected tier: `code`.

```text
Analyze 2026-2028 AI chip supply chain risk across policy, capex, alternatives, and demand.
```

Expected tier: `reasoning`.

```text
Summarize @docs/spec.md and identify contradictions.
```

Expected tier: `long_context`.

### Tuning

Adjust size thresholds first:

- `max_simple_chars`, `max_simple_words`, `max_simple_lines`
- `max_standard_chars`, `max_standard_words`, `max_standard_lines`

Then add domain words:

- `code_keywords`
- `reasoning_keywords`
- `long_context_keywords`

Prefer conservative routing. When in doubt, route to a stronger or larger
context model.

## 中文

### 工作流

1. 先确认 Hermes 已经接入 `patches/core-integration.md` 里的 core patch。
   插件本身可以预览路由，但自动切换必须发生在每轮模型请求之前。
2. 把 `config.example.yaml` 里的 `smart_model_routing` 段复制到 Hermes
   的 `config.yaml`。
3. API key 继续放在 `.env`，配置里只写 `api_key_env`。
4. 用 `smart_model_route_preview` 先测试代表性提示词。
5. 修改插件文件或 core integration 后，重启 Hermes Desktop、TUI、CLI
   或 Gateway。

### Tier 含义

- `cheap`: 短文本、轻量问题。
- `standard`: 中等长度的普通解释。
- `code`: 代码、报错、调试、重构、测试。
- `reasoning`: 分析、研究、比较、策略、证明、预测。
- `long_context`: `@file` 引用或长文档/长上下文提示。
- `media`: 图片或非文本附件。

未配置的 tier 会回退到普通 `model:` 配置里的主模型。

### 测试提示词

```text
hello
```

预期 tier: `cheap`。

```text
请给我一个实用的 TCP 拥塞控制概览，包括 slow start、拥塞避免、丢包后的行为，以及为什么现代网络仍然关心它。
```

预期 tier: `standard`。

````text
帮我修复这个报错，并给出 3 个测试用例：
```python
raise ValueError("x")
```
````

预期 tier: `code`。

```text
分析 2026-2028 年 AI 芯片供应链风险，从政策、资本开支、替代方案、需求弹性四个维度展开，并给出三种情景推演。
```

预期 tier: `reasoning`。

```text
Summarize @docs/spec.md and identify contradictions.
```

预期 tier: `long_context`。

### 调参建议

先调长度阈值：

- `max_simple_chars`, `max_simple_words`, `max_simple_lines`
- `max_standard_chars`, `max_standard_words`, `max_standard_lines`

再加领域关键词：

- `code_keywords`
- `reasoning_keywords`
- `long_context_keywords`

建议保持保守：不确定的任务宁可走更强或更大上下文的模型。
