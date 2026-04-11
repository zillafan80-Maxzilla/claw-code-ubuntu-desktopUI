from __future__ import annotations

import json
import os
import signal
import time
from pathlib import Path


class LifecycleManager:
    def __init__(self, root: Path):
        self.root = Path(root)
        runtime_base = os.environ.get("CLAW_DESKTOP_RUNTIME_DIR", "/tmp/claw-code-desktop")
        self.runtime_dir = Path(runtime_base)
        self.registry_path = self.runtime_dir / "processes.json"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

    def prepare_launch(self) -> None:
        self.terminate_registered()
        self._write_registry({})

    def register_process(self, name: str, pid: int, argv: list[str], cwd: Path) -> None:
        registry = self._read_registry()
        registry[str(pid)] = {
            "name": name,
            "pid": pid,
            "argv": argv,
            "cwd": str(cwd),
            "started_at": time.time(),
        }
        self._write_registry(registry)

    def unregister_process(self, pid: int) -> None:
        registry = self._read_registry()
        registry.pop(str(pid), None)
        self._write_registry(registry)

    def describe_processes(self) -> list[str]:
        rows = []
        for record in self._read_registry().values():
            argv = " ".join(record.get("argv", [])[:4])
            rows.append(f"{record['pid']} {record['name']} {argv}".strip())
        return rows

    def terminate_registered(self) -> None:
        registry = self._read_registry()
        if not registry:
            return
        for record in registry.values():
            pid = int(record["pid"])
            self._terminate_pid(pid, signal.SIGTERM)
        time.sleep(0.4)
        for record in registry.values():
            pid = int(record["pid"])
            if self._is_alive(pid):
                self._terminate_pid(pid, signal.SIGKILL)
        self._write_registry({})

    def shutdown(self) -> None:
        self.terminate_registered()

    def _terminate_pid(self, pid: int, sig: signal.Signals) -> None:
        try:
            os.killpg(pid, sig)
        except ProcessLookupError:
            return
        except OSError:
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                return

    @staticmethod
    def _is_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def _read_registry(self) -> dict[str, dict]:
        if not self.registry_path.exists():
            return {}
        try:
            return json.loads(self.registry_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write_registry(self, payload: dict[str, dict]) -> None:
        self.registry_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )


def cleanup_runtime() -> None:
    manager = LifecycleManager(Path(__file__).resolve().parents[1])
    manager.shutdown()
