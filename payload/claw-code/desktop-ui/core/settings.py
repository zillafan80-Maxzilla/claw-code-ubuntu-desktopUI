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

    def to_env(self) -> dict[str, str]:
        return {
            "OPENAI_BASE_URL": self.base_url.strip(),
            "OPENAI_API_KEY": self.api_key.strip(),
            "CLAW_DESKTOP_MODEL": self.model.strip(),
            "CLAW_TOOL_CALL_STYLE": self.tool_call_style.strip(),
        }

    def masked_api_key(self) -> str:
        key = self.api_key.strip()
        if not key:
            return "未设置"
        if len(key) <= 8:
            return "*" * len(key)
        return f"{key[:4]}...{key[-4:]}"

    def provider_label(self) -> str:
        model = self.model.strip().lower()
        if model.startswith("openai/") or "gemma" in model:
            return "OpenAI 兼容"
        if model.startswith("claude"):
            return "Anthropic"
        if model.startswith("grok"):
            return "xAI"
        return "自动识别"

    def tool_style_label(self) -> str:
        return {
            "auto": "自动适配",
            "native": "原生工具协议",
            "gemma-json": "Gemma JSON 提示适配",
        }.get(self.tool_call_style, self.tool_call_style)


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
        )

    def save(self, settings: DesktopSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(settings), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
