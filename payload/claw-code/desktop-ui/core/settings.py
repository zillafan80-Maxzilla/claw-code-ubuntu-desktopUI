from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class DesktopSettings:
    model: str = "openai/gemma-4-31b-it-q8-prod"
    base_url: str = "http://127.0.0.1:8001/v1"
    api_key: str = "local-dev-token"
    tool_call_style: str = "auto"
    locale: str = "en"
    high_privilege: bool = False
    autonomous_execution: bool = False

    def to_env(self) -> dict[str, str]:
        return {
            "OPENAI_BASE_URL": self.base_url.strip(),
            "OPENAI_API_KEY": self.api_key.strip(),
            "CLAW_DESKTOP_MODEL": self.model.strip(),
            "CLAW_TOOL_CALL_STYLE": self.tool_call_style.strip(),
            "CLAW_DESKTOP_LOCALE": self.locale.strip() or "en",
            "CLAW_DESKTOP_HIGH_PRIVILEGE": "1" if self.high_privilege else "0",
            "CLAW_DESKTOP_AUTONOMOUS": "1" if self.autonomous_execution else "0",
        }

    def masked_api_key(self) -> str:
        key = self.api_key.strip()
        if not key:
            return "未设置"
        if len(key) <= 8:
            return "*" * len(key)
        return f"{key[:4]}...{key[-4:]}"

    def provider_label(self, locale: str = "en") -> str:
        model = self.model.strip().lower()
        if model.startswith("openai/") or "gemma" in model:
            return {
                "en": "OpenAI Compatible",
                "ja": "OpenAI 互換",
                "ko": "OpenAI 호환",
                "zh": "OpenAI 兼容",
            }.get(locale, "OpenAI Compatible")
        if model.startswith("claude"):
            return "Anthropic"
        if model.startswith("grok"):
            return "xAI"
        return {
            "en": "Auto Detect",
            "ja": "自動判別",
            "ko": "자동 감지",
            "zh": "自动识别",
        }.get(locale, "Auto Detect")

    def tool_style_label(self, locale: str = "en") -> str:
        labels = {
            "en": {
                "auto": "Automatic Adaptation",
                "native": "Native Tool Protocol",
                "gemma-json": "Gemma JSON Prompt Adapter",
            },
            "ja": {
                "auto": "自動適応",
                "native": "ネイティブツールプロトコル",
                "gemma-json": "Gemma JSON プロンプト適応",
            },
            "ko": {
                "auto": "자동 적응",
                "native": "기본 도구 프로토콜",
                "gemma-json": "Gemma JSON 프롬프트 어댑터",
            },
            "zh": {
                "auto": "自动适配",
                "native": "原生工具协议",
                "gemma-json": "Gemma JSON 提示适配",
            },
        }
        return labels.get(locale, labels["en"]).get(
            self.tool_call_style, self.tool_call_style
        )


class DesktopSettingsStore:
    def __init__(self) -> None:
        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            base = Path(config_home)
        else:
            base = Path.home() / ".config"
        self.path = base / "claw-code-desktop" / "settings.json"

    def load(self) -> DesktopSettings:
        defaults = DesktopSettings(
            model=os.environ.get("CLAW_DESKTOP_MODEL", DesktopSettings.model),
            base_url=os.environ.get("OPENAI_BASE_URL", DesktopSettings.base_url),
            api_key=os.environ.get("OPENAI_API_KEY", DesktopSettings.api_key),
            tool_call_style=os.environ.get(
                "CLAW_TOOL_CALL_STYLE", DesktopSettings.tool_call_style
            ),
            locale=os.environ.get("CLAW_DESKTOP_LOCALE", DesktopSettings.locale),
            high_privilege=os.environ.get("CLAW_DESKTOP_HIGH_PRIVILEGE", "0") in {"1", "true", "yes"},
            autonomous_execution=os.environ.get("CLAW_DESKTOP_AUTONOMOUS", "0") in {"1", "true", "yes"},
        )
        if not self.path.exists():
            return defaults
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return defaults
        return DesktopSettings(
            model=str(payload.get("model") or defaults.model),
            base_url=str(payload.get("base_url") or defaults.base_url),
            api_key=str(payload.get("api_key") or defaults.api_key),
            tool_call_style=str(payload.get("tool_call_style") or defaults.tool_call_style),
            locale=str(payload.get("locale") or defaults.locale or "en"),
            high_privilege=bool(payload.get("high_privilege", defaults.high_privilege)),
            autonomous_execution=bool(payload.get("autonomous_execution", defaults.autonomous_execution)),
        )

    def save(self, settings: DesktopSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(settings), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
