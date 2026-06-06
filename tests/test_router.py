import os
import unittest

from router import classify_message, preview_route, resolve_smart_model_route


CONFIG = {
    "smart_model_routing": {
        "enabled": True,
        "tiers": {
            "cheap": {
                "provider": "deepseek",
                "model": "deepseek-v4-flash",
                "api_key_env": "DEEPSEEK_API_KEY",
                "reasoning": {"enabled": False},
            },
            "standard": {
                "provider": "kimi-coding",
                "model": "kimi-k2.6",
                "api_key_env": "KIMI_API_KEY",
                "reasoning": {"enabled": False},
            },
            "code": {
                "provider": "kimi-coding",
                "model": "kimi-for-coding",
                "api_key_env": "KIMI_API_KEY",
                "reasoning": {"enabled": True, "effort": "medium"},
            },
            "reasoning": {
                "provider": "deepseek",
                "model": "deepseek-v4-pro",
                "api_key_env": "DEEPSEEK_API_KEY",
                "reasoning": {"enabled": True, "effort": "high"},
            },
            "long_context": {
                "provider": "kimi-coding",
                "model": "kimi-k2-thinking-turbo",
                "api_key_env": "KIMI_API_KEY",
            },
            "media": {
                "provider": "minimax-cn",
                "model": "MiniMax-M3",
                "api_key_env": "MINIMAX_CN_API_KEY",
            },
        },
        "max_simple_chars": 20,
        "max_simple_words": 4,
    }
}


class RouterTests(unittest.TestCase):
    def test_classifies_short_text_as_cheap(self):
        self.assertEqual(classify_message("hello", CONFIG["smart_model_routing"])[0], "cheap")

    def test_classifies_medium_text_as_standard(self):
        tier, reason = classify_message(
            "Please explain TCP congestion control in practical terms.",
            CONFIG["smart_model_routing"],
        )
        self.assertEqual((tier, reason), ("standard", "medium-text"))

    def test_classifies_code_as_code(self):
        tier, _ = classify_message("Fix this traceback:\n```python\nraise ValueError('x')\n```")
        self.assertEqual(tier, "code")

    def test_classifies_at_reference_as_long_context(self):
        self.assertEqual(classify_message("Summarize @docs/spec.md")[0], "long_context")

    def test_preview_route_uses_configured_tier_model(self):
        route = preview_route(
            "Analyze 2026 AI chip supply chain risk.",
            CONFIG,
            primary_model="MiniMax-M3",
            primary_provider="minimax-cn",
        )
        self.assertEqual(route["tier"], "reasoning")
        self.assertEqual(route["model"], "deepseek-v4-pro")
        self.assertEqual(route["reasoning"], {"enabled": True, "effort": "high"})

    def test_resolve_route_uses_runtime_provider(self):
        os.environ["KIMI_API_KEY"] = "sk-test"

        import types
        import sys

        hermes_cli = types.ModuleType("hermes_cli")
        runtime_provider = types.ModuleType("hermes_cli.runtime_provider")

        def fake_resolve_runtime_provider(**kwargs):
            return {
                "provider": kwargs["requested"],
                "base_url": kwargs["explicit_base_url"] or "",
                "api_key": kwargs["explicit_api_key"],
                "api_mode": "chat_completions",
            }

        runtime_provider.resolve_runtime_provider = fake_resolve_runtime_provider
        sys.modules["hermes_cli"] = hermes_cli
        sys.modules["hermes_cli.runtime_provider"] = runtime_provider
        try:
            route = resolve_smart_model_route(
                "Fix this traceback and add tests",
                CONFIG,
                "MiniMax-M3",
                {"provider": "minimax-cn", "api_key": "sk-primary"},
            )
        finally:
            sys.modules.pop("hermes_cli.runtime_provider", None)
            sys.modules.pop("hermes_cli", None)

        self.assertEqual(route["model"], "kimi-for-coding")
        self.assertEqual(route["runtime"]["provider"], "kimi-coding")
        self.assertEqual(route["reasoning_config"], {"enabled": True, "effort": "medium"})


if __name__ == "__main__":
    unittest.main()
