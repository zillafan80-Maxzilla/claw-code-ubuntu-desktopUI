from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from core.lifecycle import LifecycleManager
from core.settings import DesktopSettings, DesktopSettingsStore


@dataclass
class CommandResult:
    request_text: str
    argv: list[str]
    exit_code: int
    stdout: str
    stderr: str
    started_at: float
    finished_at: float
    pid: int | None = None
    parsed_stdout: object | None = None

    @property
    def duration_seconds(self) -> float:
        return max(self.finished_at - self.started_at, 0.0)


@dataclass
class BridgeEvent:
    request_text: str
    kind: str
    text: str
    created_at: float


class ClawBridge:
    def __init__(
        self,
        project_root: Path,
        lifecycle: LifecycleManager,
        settings_store: DesktopSettingsStore,
    ):
        self.project_root = Path(project_root)
        self.lifecycle = lifecycle
        self.settings_store = settings_store
        self.claw_bin = self.project_root.parent / "bin" / "claw"
        self.base_env = dict(os.environ)
        self.is_autopilot = False
        self.history: list[str] = []
        self.conversation: list[tuple[str, str]] = []
        self._lock = threading.Lock()
        self._active: dict[int, subprocess.Popen[str]] = {}

    def set_autopilot(self, enabled: bool) -> str:
        self.is_autopilot = enabled
        return "高权限自动执行已开启" if enabled else "已恢复安全权限模式"

    def active_process_count(self) -> int:
        with self._lock:
            return len(self._active)

    def active_process_rows(self) -> list[str]:
        return self.lifecycle.describe_processes()

    def current_settings(self) -> DesktopSettings:
        return self.settings_store.load()

    def shutdown(self) -> None:
        self.lifecycle.terminate_registered()

    def reset_conversation(self) -> None:
        self.conversation.clear()

    def set_conversation(self, turns: list[tuple[str, str]]) -> None:
        self.conversation = [
            (role.strip(), text.strip())
            for role, text in turns
            if role.strip() and text.strip()
        ][-24:]

    def cancel_active(self) -> bool:
        cancelled = False
        with self._lock:
            processes = list(self._active.values())
        for proc in processes:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                cancelled = True
            except OSError:
                try:
                    proc.terminate()
                    cancelled = True
                except OSError:
                    continue
        if cancelled:
            self._append_history("cancelled active desktop request")
        return cancelled

    def submit(
        self,
        request_text: str,
        on_complete: Callable[[CommandResult], None],
        on_event: Callable[[BridgeEvent], None] | None = None,
    ) -> None:
        settings = self.current_settings()
        argv = self._build_command(request_text, settings)
        env = self._build_env(settings)
        started_at = time.time()
        self._append_history(
            f"排队: {settings.model} · {' '.join(argv[1:])}"
        )
        worker = threading.Thread(
            target=self._run_command,
            args=(request_text, argv, env, started_at, on_complete, on_event),
            daemon=True,
        )
        worker.start()

    def _build_env(self, settings: DesktopSettings) -> dict[str, str]:
        env = dict(self.base_env)
        env.update(settings.to_env())
        return env

    def _build_command(self, request_text: str, settings: DesktopSettings) -> list[str]:
        text = request_text.strip()
        if not text:
            raise ValueError("输入内容不能为空。")

        if text.startswith("/"):
            return self._build_slash_command(text, settings)

        effective_prompt = self._compose_prompt(text)

        argv = [
            str(self.claw_bin),
            "--model",
            settings.model,
        ]
        if self.is_autopilot:
            argv.append("--dangerously-skip-permissions")
        argv.extend(["prompt", effective_prompt])
        return argv

    def _build_slash_command(
        self, request_text: str, settings: DesktopSettings
    ) -> list[str]:
        text = request_text.strip()
        parts = text.split()
        name = self._normalize_slash_alias(parts[0])
        args = parts[1:]
        shared_prefix = [str(self.claw_bin), "--model", settings.model]
        commands = {
            "/help": ["help"],
            "/status": ["--output-format", "json", "status"],
            "/sandbox": ["--output-format", "json", "sandbox"],
            "/doctor": ["--output-format", "json", "doctor"],
            "/version": ["--output-format", "json", "version"],
            "/agents": ["--output-format", "json", "agents", *args],
            "/mcp": ["--output-format", "json", "mcp", *args],
            "/skills": ["--output-format", "json", "skills", *args],
        }
        if name == "/clear":
            raise ValueError("/清空 由桌面界面直接处理。")
        if name not in commands:
            raise ValueError(
                f"暂不支持命令：{parts[0]}。可用命令：/帮助 /状态 /体检 /沙箱 /版本 /智能体 /mcp /技能。"
            )
        return [*shared_prefix, *commands[name]]

    @staticmethod
    def _normalize_slash_alias(name: str) -> str:
        aliases = {
            "/帮助": "/help",
            "/状态": "/status",
            "/体检": "/doctor",
            "/诊断": "/doctor",
            "/沙箱": "/sandbox",
            "/版本": "/version",
            "/智能体": "/agents",
            "/技能": "/skills",
            "/清空": "/clear",
        }
        return aliases.get(name, name)

    def _run_command(
        self,
        request_text: str,
        argv: list[str],
        env: dict[str, str],
        started_at: float,
        on_complete: Callable[[CommandResult], None],
        on_event: Callable[[BridgeEvent], None] | None,
    ) -> None:
        proc: subprocess.Popen[str] | None = None
        try:
            json_mode = "--output-format" in argv and "json" in argv
            proc = subprocess.Popen(
                argv,
                cwd=self.project_root.parent,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=json_mode,
                bufsize=1 if json_mode else 0,
                start_new_session=True,
            )
            with self._lock:
                self._active[proc.pid] = proc
            self.lifecycle.register_process("claw-cli", proc.pid, argv, self.project_root.parent)
            if json_mode:
                stdout, stderr = proc.communicate()
            else:
                stdout, stderr = self._stream_command_output(
                    proc,
                    request_text,
                    on_event,
                )
            result = CommandResult(
                request_text=request_text,
                argv=argv,
                exit_code=proc.returncode,
                stdout=(stdout or "").strip(),
                stderr=(stderr or "").strip(),
                started_at=started_at,
                finished_at=time.time(),
                pid=proc.pid,
                parsed_stdout=self._try_parse_json(stdout),
            )
            self._append_history(
                f"完成[{result.exit_code}] {Path(argv[0]).name} · {result.duration_seconds:.2f}s"
            )
            self._record_conversation_turn(request_text, result)
            on_complete(result)
        except Exception as exc:
            result = CommandResult(
                request_text=request_text,
                argv=argv,
                exit_code=1,
                stdout="",
                stderr=str(exc),
                started_at=started_at,
                finished_at=time.time(),
                pid=proc.pid if proc else None,
            )
            self._append_history(f"失败: {exc}")
            on_complete(result)
        finally:
            if proc is not None:
                self.lifecycle.unregister_process(proc.pid)
                with self._lock:
                    self._active.pop(proc.pid, None)

    def _append_history(self, entry: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.history.append(f"[{timestamp}] {entry}")
        self.history[:] = self.history[-200:]

    def _compose_prompt(self, latest_user_text: str) -> str:
        history = self.conversation[-12:]
        if not history:
            return latest_user_text
        lines = [
            "Continue this existing conversation.",
            "Preserve task continuity across turns.",
            "If the user is in the middle of a multi-step task, keep working until that task is complete.",
            "When tools are available and useful, use them instead of only describing what you would do.",
            "",
            "Conversation so far:",
        ]
        for role, text in history:
            prefix = "User" if role == "user" else "Assistant"
            lines.append(f"{prefix}: {text}")
        lines.extend(
            [
                "",
                "Latest user message:",
                latest_user_text,
            ]
        )
        return "\n".join(lines)

    def _record_conversation_turn(self, request_text: str, result: CommandResult) -> None:
        if request_text.strip().startswith("/"):
            return
        self.conversation.append(("user", request_text.strip()))
        reply = self._extract_assistant_text(result)
        if reply:
            self.conversation.append(("assistant", reply))
        self.conversation[:] = self.conversation[-24:]

    def _extract_assistant_text(self, result: CommandResult) -> str:
        if isinstance(result.parsed_stdout, dict):
            message = result.parsed_stdout.get("message")
            if isinstance(message, str):
                return self._normalize_assistant_message(message)
        return self._clean_terminal_output(result.stdout)

    def normalize_result_text(self, result: CommandResult) -> str:
        if isinstance(result.parsed_stdout, dict):
            message = result.parsed_stdout.get("message")
            if isinstance(message, str):
                normalized = self._normalize_assistant_message(message)
                if normalized:
                    return normalized
        if result.stdout:
            parsed = self._try_parse_json(result.stdout)
            if isinstance(parsed, dict):
                message = parsed.get("message")
                if isinstance(message, str):
                    normalized = self._normalize_assistant_message(message)
                    if normalized:
                        return normalized
        return self._clean_terminal_output(result.stdout)

    def _normalize_assistant_message(self, message: str) -> str:
        text = message.strip()
        if not text:
            return ""
        direct = self._extract_message_from_nested_json(text)
        if direct:
            return direct
        repaired = text.replace("\\\"", "\"")
        direct = self._extract_message_from_nested_json(repaired)
        if direct:
            return direct
        return text

    def _extract_message_from_nested_json(self, text: str) -> str | None:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            inner = parsed.get("message")
            if isinstance(inner, str):
                nested = self._extract_message_from_nested_json(inner)
                return nested or inner.strip()
            if parsed.get("type") == "final" and isinstance(parsed.get("message"), str):
                return str(parsed["message"]).strip()
        marker = '"message"'
        final_marker = '"type": "final"'
        if marker in text:
            idx = text.find(marker)
            snippet = text[idx:]
            colon = snippet.find(":")
            if colon != -1:
                value = snippet[colon + 1 :].lstrip()
                if value.startswith('"'):
                    chars: list[str] = []
                    escaped = False
                    for ch in value[1:]:
                        if escaped:
                            chars.append(ch)
                            escaped = False
                            continue
                        if ch == "\\":
                            escaped = True
                            continue
                        if ch == '"':
                            break
                        chars.append(ch)
                    extracted = "".join(chars).strip()
                    if extracted:
                        return extracted
        if final_marker in text and marker in text:
            extracted = self._extract_message_from_nested_json(text.replace('\\"', '"'))
            if extracted:
                return extracted
        return None

    def _stream_command_output(
        self,
        proc: subprocess.Popen[bytes],
        request_text: str,
        on_event: Callable[[BridgeEvent], None] | None,
    ) -> tuple[str, str]:
        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        stream_state = {
            "buffer": "",
            "last_status": "",
            "tool_log": "",
        }

        def read_stdout() -> None:
            assert proc.stdout is not None
            while True:
                chunk = proc.stdout.read(512)
                if not chunk:
                    break
                text = chunk.decode("utf-8", errors="replace")
                stdout_parts.append(text)
                if on_event is not None:
                    self._emit_stream_events(request_text, text, on_event, stream_state)

        def read_stderr() -> None:
            assert proc.stderr is not None
            while True:
                chunk = proc.stderr.read(512)
                if not chunk:
                    break
                stderr_parts.append(chunk.decode("utf-8", errors="replace"))

        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stdout_thread.start()
        stderr_thread.start()
        proc.wait()
        stdout_thread.join()
        stderr_thread.join()
        if on_event is not None and stream_state["buffer"].strip():
            self._emit_stream_line(
                request_text,
                stream_state["buffer"],
                on_event,
                stream_state,
            )
        return "".join(stdout_parts).strip(), "".join(stderr_parts).strip()

    def _emit_stream_events(
        self,
        request_text: str,
        chunk: str,
        on_event: Callable[[BridgeEvent], None],
        stream_state: dict[str, str],
    ) -> None:
        cleaned = self._strip_terminal_controls(chunk).replace("\r", "\n")
        if not cleaned:
            return
        stream_state["buffer"] += cleaned
        while "\n" in stream_state["buffer"]:
            line, stream_state["buffer"] = stream_state["buffer"].split("\n", 1)
            self._emit_stream_line(request_text, line, on_event, stream_state)

    def _emit_stream_line(
        self,
        request_text: str,
        line: str,
        on_event: Callable[[BridgeEvent], None],
        stream_state: dict[str, str],
    ) -> None:
        text = line.strip()
        if not text:
            return
        if "Thinking..." in text:
            text = "🦀 Thinking..."
        elif "✔ ✨ Done" in text:
            text = "✔ ✨ Done"
        elif "✘ " in text and not text.startswith("✘ "):
            text = text[text.find("✘ ") :]
        if self._is_progress_line(text):
            if text != stream_state["last_status"]:
                stream_state["last_status"] = text
                on_event(
                    BridgeEvent(
                        request_text=request_text,
                        kind="status",
                        text=text,
                        created_at=time.time(),
                    )
                )
            return
        tool_line = self._normalize_tool_line(text)
        if tool_line:
            current = stream_state["tool_log"].splitlines()
            if tool_line not in current:
                stream_state["tool_log"] = "\n".join([*current, tool_line]).strip()
                on_event(
                    BridgeEvent(
                        request_text=request_text,
                        kind="tool",
                        text=stream_state["tool_log"],
                        created_at=time.time(),
                    )
                )

    @staticmethod
    def _strip_terminal_controls(text: str) -> str:
        ansi = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi.sub("", text).replace("\x1b7", "").replace("\x1b8", "")

    @staticmethod
    def _is_progress_line(text: str) -> bool:
        return (
            "Thinking..." in text
            or text.startswith("🧭 ")
            or text.startswith("… ")
            or text.startswith("✔ ")
            or text.startswith("✘ ")
            or text.endswith("Done")
        )

    @staticmethod
    def _normalize_tool_line(text: str) -> str:
        if text.startswith("╭") or text.startswith("╰"):
            return ""
        if text.startswith("$ "):
            return text
        if text.startswith("│") and "$ " in text:
            return text[text.find("$ ") :].strip()
        if text.startswith("✓ ") or text.startswith("✗ "):
            return text
        return ""

    def _clean_terminal_output(self, stdout: str) -> str:
        cleaned = self._strip_terminal_controls(stdout).replace("\r", "\n")
        cleaned = re.sub(r"[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏] 🦀 Thinking\.\.\.", "\n", cleaned)
        cleaned = cleaned.replace("🦀 Thinking...", "\n")
        cleaned = cleaned.replace("✔ ✨ Done", "")
        cleaned = cleaned.replace("✘ Failed", "")
        raw_lines = [line.rstrip() for line in cleaned.splitlines()]
        lines: list[str] = []
        for line in raw_lines:
            stripped = line.strip()
            if not stripped:
                if lines and lines[-1] != "":
                    lines.append("")
                continue
            if self._is_progress_line(stripped):
                continue
            if stripped.startswith("╭") or stripped.startswith("╰"):
                continue
            if stripped.startswith("$ "):
                continue
            if stripped.startswith("│") and "$ " in stripped:
                continue
            if stripped.startswith("✓ ") or stripped.startswith("✗ "):
                continue
            lines.append(stripped)
        compacted: list[str] = []
        for line in lines:
            if line and compacted and compacted[-1] == line:
                continue
            if line == "" and (not compacted or compacted[-1] == ""):
                continue
            compacted.append(line)
        return "\n".join(compacted).strip()

    @staticmethod
    def _try_parse_json(stdout: str | None) -> object | None:
        if not stdout:
            return None
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return None
