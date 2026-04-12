from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path


def _now_ms() -> int:
    return int(time.time() * 1000)


def _looks_like_raw_tool_stub(text: str) -> bool:
    lowered = text.strip().lower()
    if not lowered:
        return False
    return (
        lowered.startswith('{"type: tool_call')
        or lowered.startswith('{"type":"tool_call"')
        or lowered.startswith("{“type")
        or '\nname: bash' in lowered
        or '\nname: websearch' in lowered
        or '"name": "bash"' in lowered
        or '"name": "websearch"' in lowered
    )


@dataclass
class SessionMessage:
    role: str
    text: str


@dataclass
class DesktopSession:
    session_id: str
    path: Path
    created_at_ms: int
    updated_at_ms: int
    messages: list[SessionMessage] = field(default_factory=list)
    compaction_summary: str | None = None


@dataclass
class SessionSummary:
    session_id: str
    path: Path
    created_at_ms: int
    updated_at_ms: int
    message_count: int
    preview: str
    compaction_summary: str | None = None


class DesktopSessionStore:
    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        scope = hashlib.sha1(str(self.project_root.parent).encode("utf-8")).hexdigest()[:16]
        config_home = os.environ.get("XDG_CONFIG_HOME")
        base = Path(config_home) if config_home else Path.home() / ".config"
        self.sessions_root = base / "claw-code-desktop" / "sessions" / scope
        self.sessions_root.mkdir(parents=True, exist_ok=True)

    def create_session(self) -> DesktopSession:
        now = _now_ms()
        session_id = f"session-{now}-desktop"
        path = self.sessions_root / f"{session_id}.jsonl"
        session = DesktopSession(
            session_id=session_id,
            path=path,
            created_at_ms=now,
            updated_at_ms=now,
            messages=[],
        )
        self.save_session(session)
        return session

    def list_sessions(self) -> list[SessionSummary]:
        rows: list[SessionSummary] = []
        for path in sorted(
            self.sessions_root.glob("*.jsonl"),
            key=lambda item: item.stat().st_mtime if item.exists() else 0.0,
            reverse=True,
        ):
            try:
                summary = self.summarize_session(path)
            except Exception:
                continue
            rows.append(summary)
        return rows

    def summarize_session(self, path: Path) -> SessionSummary:
        session_id = path.stem
        created_at_ms = _now_ms()
        updated_at_ms = created_at_ms
        message_count = 0
        preview = ""
        compaction_summary: str | None = None

        for row in path.read_text(encoding="utf-8").splitlines():
            if not row.strip():
                continue
            payload = json.loads(row)
            record_type = str(payload.get("type") or "")
            if record_type == "session_meta":
                session_id = str(payload.get("session_id") or session_id)
                created_at_ms = int(payload.get("created_at_ms") or created_at_ms)
                updated_at_ms = int(payload.get("updated_at_ms") or updated_at_ms)
                continue
            if record_type == "compaction":
                summary = payload.get("summary")
                if isinstance(summary, str) and summary.strip():
                    compaction_summary = summary.strip()
                continue
            if record_type != "message":
                continue
            message = payload.get("message")
            if not isinstance(message, dict):
                continue
            role = str(message.get("role") or "")
            blocks = message.get("blocks")
            if not isinstance(blocks, list):
                continue
            text_parts: list[str] = []
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                block_type = str(block.get("type") or "")
                if block_type == "text":
                    text_value = block.get("text")
                    if isinstance(text_value, str) and text_value.strip():
                        text_parts.append(text_value.strip())
                elif block_type == "tool_result":
                    output = block.get("output")
                    if isinstance(output, str) and output.strip():
                        text_parts.append(output.strip())
            if not text_parts:
                continue
            combined = "\n\n".join(text_parts).strip()
            if role == "assistant" and _looks_like_raw_tool_stub(combined):
                continue
            message_count += 1
            if not preview and role == "user" and combined:
                preview = combined.splitlines()[0][:80]

        return SessionSummary(
            session_id=session_id,
            path=path,
            created_at_ms=created_at_ms,
            updated_at_ms=updated_at_ms,
            message_count=message_count,
            preview=preview or session_id,
            compaction_summary=compaction_summary,
        )

    def load_session(self, path: Path) -> DesktopSession:
        records = path.read_text(encoding="utf-8").splitlines()
        session_id = path.stem
        created_at_ms = _now_ms()
        updated_at_ms = created_at_ms
        messages: list[SessionMessage] = []
        compaction_summary: str | None = None
        for row in records:
            if not row.strip():
                continue
            payload = json.loads(row)
            record_type = str(payload.get("type") or "")
            if record_type == "session_meta":
                session_id = str(payload.get("session_id") or session_id)
                created_at_ms = int(payload.get("created_at_ms") or created_at_ms)
                updated_at_ms = int(payload.get("updated_at_ms") or updated_at_ms)
                continue
            if record_type == "compaction":
                summary = payload.get("summary")
                if isinstance(summary, str) and summary.strip():
                    compaction_summary = summary.strip()
                continue
            if record_type != "message":
                continue
            message = payload.get("message")
            if not isinstance(message, dict):
                continue
            role = str(message.get("role") or "")
            blocks = message.get("blocks")
            if not isinstance(blocks, list):
                continue
            text_parts: list[str] = []
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                block_type = str(block.get("type") or "")
                if block_type == "text":
                    text_value = block.get("text")
                    if isinstance(text_value, str) and text_value.strip():
                        text_parts.append(text_value.strip())
                elif block_type == "tool_result":
                    output = block.get("output")
                    if isinstance(output, str) and output.strip():
                        text_parts.append(output.strip())
            if text_parts:
                combined = "\n\n".join(text_parts).strip()
                if role == "assistant" and _looks_like_raw_tool_stub(combined):
                    continue
                messages.append(SessionMessage(role=role, text=combined))
        return DesktopSession(
            session_id=session_id,
            path=path,
            created_at_ms=created_at_ms,
            updated_at_ms=updated_at_ms,
            messages=messages,
            compaction_summary=compaction_summary,
        )

    def save_session(self, session: DesktopSession) -> None:
        session.path.parent.mkdir(parents=True, exist_ok=True)
        session.updated_at_ms = _now_ms()
        lines = [
            json.dumps(
                {
                    "type": "session_meta",
                    "version": 1,
                    "session_id": session.session_id,
                    "created_at_ms": session.created_at_ms,
                    "updated_at_ms": session.updated_at_ms,
                    "workspace_root": str(self.project_root.parent),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        ]
        if session.compaction_summary:
            lines.append(
                json.dumps(
                    {
                        "type": "compaction",
                        "count": 1,
                        "removed_message_count": 0,
                        "summary": session.compaction_summary,
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
        for message in session.messages:
            if message.role == "assistant" and _looks_like_raw_tool_stub(message.text):
                continue
            lines.append(
                json.dumps(
                    {
                        "type": "message",
                        "message": {
                            "role": message.role,
                            "blocks": [{"type": "text", "text": message.text}],
                        },
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
        session.path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def append_turn(self, session: DesktopSession, user_text: str, assistant_text: str) -> DesktopSession:
        if user_text.strip():
            session.messages.append(SessionMessage(role="user", text=user_text.strip()))
        if assistant_text.strip():
            session.messages.append(SessionMessage(role="assistant", text=assistant_text.strip()))
        self.save_session(session)
        return session

    def replace_with_messages(
        self,
        session: DesktopSession,
        messages: list[SessionMessage],
        *,
        compaction_summary: str | None = None,
    ) -> DesktopSession:
        session.messages = list(messages)
        session.compaction_summary = compaction_summary
        self.save_session(session)
        return session

    def delete_session(self, path: Path) -> None:
        if path.exists():
            path.unlink()

    def compact_session(self, session: DesktopSession) -> tuple[DesktopSession, str]:
        if len(session.messages) <= 8:
            detail = f"Skipped compaction. Messages kept: {len(session.messages)}."
            return session, detail
        removed = session.messages[:-6]
        kept = session.messages[-6:]
        preview_parts: list[str] = []
        for message in removed[-6:]:
            if message.text.strip():
                preview_parts.append(f"{message.role}: {message.text.strip().splitlines()[0]}")
        summary = " | ".join(preview_parts)[:320] or "Earlier messages were compacted."
        compacted = SessionMessage(
            role="assistant",
            text=f"[Compacted {len(removed)} earlier messages]\n{summary}",
        )
        session.messages = [compacted, *kept]
        session.compaction_summary = compacted.text
        self.save_session(session)
        detail = f"Compacted {len(removed)} messages. Messages kept: {len(session.messages)}."
        return session, detail
