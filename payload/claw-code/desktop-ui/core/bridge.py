from __future__ import annotations

import json
import os
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

    def submit(
        self,
        request_text: str,
        on_complete: Callable[[CommandResult], None],
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
            args=(request_text, argv, env, started_at, on_complete),
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

        argv = [
            str(self.claw_bin),
            "--model",
            settings.model,
            "--output-format",
            "json",
        ]
        if self.is_autopilot:
            argv.append("--dangerously-skip-permissions")
        argv.extend(["prompt", text])
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
    ) -> None:
        proc: subprocess.Popen[str] | None = None
        try:
            proc = subprocess.Popen(
                argv,
                cwd=self.project_root.parent,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            with self._lock:
                self._active[proc.pid] = proc
            self.lifecycle.register_process("claw-cli", proc.pid, argv, self.project_root.parent)
            stdout, stderr = proc.communicate()
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

    @staticmethod
    def _try_parse_json(stdout: str | None) -> object | None:
        if not stdout:
            return None
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return None
