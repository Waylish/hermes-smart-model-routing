---
name: smart-model-routing
description: Route Hermes turns across configured models.
---

# Smart Model Routing

Use this skill when configuring, testing, or tuning Hermes Agent's
per-turn model router.

## Workflow

1. Confirm that Hermes has the core integration from `patches/core-integration.md`.
   The plugin alone can preview routes, but Hermes must call the router before
   each model request for automatic switching.
2. Add a `smart_model_routing` section to `config.yaml`. Start from
   `config.example.yaml`.
3. Keep API keys in `.env`; reference them with `api_key_env`.
4. Test representative prompts with `smart_model_route_preview` before relying
   on live routing.
5. Restart Hermes Desktop, TUI, CLI, or Gateway after changing plugin files or
   core integration code.

## Tier Meanings

- `cheap`: short, text-only questions.
- `standard`: medium-size normal explanations.
- `code`: code, traceback, debugging, refactoring, or tests.
- `reasoning`: analysis, research, comparison, strategy, proof, or forecasting.
- `long_context`: `@file` references or large document-style prompts.
- `media`: image or non-text attachment turns.

Missing tiers fall back to the primary model in the normal `model:` config.

## Validation Prompts

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

## Tuning

Adjust size thresholds first:

- `max_simple_chars`, `max_simple_words`, `max_simple_lines`
- `max_standard_chars`, `max_standard_words`, `max_standard_lines`

Then add domain words:

- `code_keywords`
- `reasoning_keywords`
- `long_context_keywords`

Prefer conservative routing. When in doubt, route to a stronger or larger
context model.
