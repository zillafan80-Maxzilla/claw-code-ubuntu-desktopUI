from __future__ import annotations

import time
import tkinter as tk
from tkinter import ttk


PALETTE = {
    "base3": "#fdf6e3",
    "base2": "#eee8d5",
    "base1": "#93a1a1",
    "base00": "#657b83",
    "base01": "#586e75",
    "blue": "#268bd2",
    "cyan": "#2aa198",
    "green": "#859900",
    "yellow": "#b58900",
    "orange": "#cb4b16",
    "red": "#dc322f",
}


class ChatWidget(ttk.Frame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, style="Shell.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._submit_callback = None
        self._retry_callback = None
        self._copy_callback = None
        self._stop_callback = None
        self._clear_callback = None
        self._chip_callback = None
        self._message_seq = 0
        self._message_widgets: dict[int, tuple[str, str, str]] = {}
        self._send_button: ttk.Button | None = None
        self._retry_button: ttk.Button | None = None
        self._copy_button: ttk.Button | None = None
        self._stop_button: ttk.Button | None = None
        self._clear_button: ttk.Button | None = None
        self._runtime_badge: tk.Label | None = None
        self._title_label: ttk.Label | None = None
        self._subtitle_label: ttk.Label | None = None
        self._hint_label: ttk.Label | None = None
        self._composer_title: ttk.Label | None = None
        self._chip_buttons: list[ttk.Button] = []
        self._chip_values: list[str] = []
        self._transcript_menu: tk.Menu | None = None

        header = ttk.Frame(self, style="Shell.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)

        title_box = ttk.Frame(header, style="Shell.TFrame")
        title_box.grid(row=0, column=0, sticky="w")
        self._title_label = ttk.Label(
            title_box,
            text="Conversation",
            background=PALETTE["base3"],
            foreground=PALETTE["base01"],
            font=("Noto Sans CJK SC", 13, "bold"),
        )
        self._title_label.pack(anchor="w")
        self._subtitle_label = ttk.Label(
            title_box,
            text="Persistent context, tools, and quick actions.",
            background=PALETTE["base3"],
            foreground=PALETTE["base00"],
            font=("Noto Sans CJK SC", 8),
        )
        self._subtitle_label.pack(anchor="w", pady=(3, 0))

        chips = ttk.Frame(self, style="Shell.TFrame")
        chips.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        chips.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        default_chip_values = [
            "Explain the current issue clearly.",
            "Continue the current task from the last step.",
            "Review changed files and list risks.",
            "Fix the current error end-to-end.",
            "/status",
            "/doctor",
        ]
        for index, value in enumerate(default_chip_values):
            button = ttk.Button(
                chips,
                text=value,
                command=lambda idx=index: self._on_chip(idx),
                style="Accent.TButton",
            )
            button.grid(row=0, column=index, sticky="ew", padx=3)
            self._chip_buttons.append(button)
            self._chip_values.append(value)

        transcript_shell = tk.Frame(
            self,
            background=PALETTE["base2"],
            highlightthickness=1,
            highlightbackground=PALETTE["base1"],
            padx=0,
            pady=0,
        )
        transcript_shell.grid(row=2, column=0, sticky="nsew", pady=(0, 12))
        transcript_shell.grid_rowconfigure(0, weight=1)
        transcript_shell.grid_columnconfigure(0, weight=1)
        transcript_shell.grid_columnconfigure(1, weight=0)

        self.transcript_text = tk.Text(
            transcript_shell,
            background=PALETTE["base3"],
            foreground=PALETTE["base01"],
            wrap="word",
            font=("Noto Sans CJK SC", 10),
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=16,
            pady=14,
            cursor="xterm",
            insertbackground=PALETTE["base01"],
        )
        self.scrollbar = tk.Scrollbar(
            transcript_shell,
            orient="vertical",
            command=self.transcript_text.yview,
            width=18,
            background=PALETTE["yellow"],
            troughcolor=PALETTE["base2"],
            activebackground=PALETTE["orange"],
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.transcript_text.configure(yscrollcommand=self.scrollbar.set)
        self.transcript_text.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        self.transcript_text.bind("<Control-a>", self._select_all)
        self.transcript_text.bind("<Control-A>", self._select_all)
        self.transcript_text.bind("<Control-c>", self._copy_selected_or_all)
        self.transcript_text.bind("<Button-3>", self._show_transcript_menu)
        self.transcript_text.bind("<Button-1>", self._dismiss_transcript_menu, add="+")
        self.transcript_text.configure(state="disabled")
        self._configure_transcript_tags()

        composer_shell = tk.Frame(
            self,
            background=PALETTE["base2"],
            highlightthickness=1,
            highlightbackground=PALETTE["base1"],
            padx=14,
            pady=12,
        )
        composer_shell.grid(row=3, column=0, sticky="ew")
        composer_shell.grid_columnconfigure(0, weight=1)

        composer_header = ttk.Frame(composer_shell, style="Composer.TFrame")
        composer_header.grid(row=0, column=0, sticky="ew")
        composer_header.columnconfigure(0, weight=1)
        self._composer_title = ttk.Label(
            composer_header,
            text="Prompt Composer",
            background=PALETTE["base2"],
            foreground=PALETTE["base01"],
            font=("Noto Sans CJK SC", 9, "bold"),
        )
        self._composer_title.grid(row=0, column=0, sticky="w")
        self._hint_label = ttk.Label(
            composer_header,
            text="Enter sends, Shift+Enter inserts a newline.",
            background=PALETTE["base2"],
            foreground=PALETTE["base00"],
            font=("Noto Sans CJK SC", 8),
        )
        self._hint_label.grid(row=0, column=1, sticky="e")

        self.input = tk.Text(
            composer_shell,
            height=6,
            wrap="word",
            background=PALETTE["base3"],
            foreground=PALETTE["base01"],
            insertbackground=PALETTE["base01"],
            relief="flat",
            borderwidth=0,
            padx=14,
            pady=12,
            font=("Noto Sans CJK SC", 10),
        )
        self.input.grid(row=1, column=0, sticky="ew", pady=(10, 8))
        self.input.bind("<Return>", self._on_enter_submit)
        self.input.bind("<KP_Enter>", self._on_enter_submit)
        self.input.bind("<Shift-Return>", self._on_insert_newline)
        self.input.bind("<Shift-KP_Enter>", self._on_insert_newline)
        self.input.bind("<Control-Return>", self._on_submit)
        self.input.bind("<Command-Return>", self._on_submit)

        footer = ttk.Frame(composer_shell, style="Composer.TFrame")
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        footer.columnconfigure(1, weight=0)
        footer.columnconfigure(2, weight=0)

        toolbar = ttk.Frame(footer, style="Composer.TFrame")
        toolbar.grid(row=0, column=0, sticky="w")
        self._retry_button = ttk.Button(toolbar, text="Retry", command=self._on_retry)
        self._retry_button.grid(row=0, column=0, padx=(0, 6))
        self._copy_button = ttk.Button(toolbar, text="Copy Chat", command=self._on_copy)
        self._copy_button.grid(row=0, column=1, padx=(0, 6))
        self._stop_button = ttk.Button(toolbar, text="Stop", command=self._on_stop)
        self._stop_button.grid(row=0, column=2, padx=(0, 6))
        self._clear_button = ttk.Button(toolbar, text="Clear", command=self._on_clear)
        self._clear_button.grid(row=0, column=3, padx=(0, 6))

        send_shell = ttk.Frame(footer, style="Composer.TFrame")
        send_shell.grid(row=0, column=1, sticky="e", padx=(12, 0))
        self._send_button = ttk.Button(send_shell, text="Send", command=self.submit, style="Accent.TButton")
        self._send_button.grid(row=0, column=0, sticky="e")

        self._runtime_badge = tk.Label(
            footer,
            text="Ended",
            background=PALETTE["base1"],
            foreground=PALETTE["base3"],
            font=("Noto Sans CJK SC", 8, "bold"),
            padx=10,
            pady=4,
        )
        self._runtime_badge.grid(row=0, column=2, sticky="e", padx=(10, 0))

    def set_ui_labels(self, labels: dict[str, object]) -> None:
        if self._title_label is not None:
            self._title_label.configure(text=str(labels.get("title", "Conversation")))
        if self._subtitle_label is not None:
            self._subtitle_label.configure(text=str(labels.get("subtitle", "")))
        if self._composer_title is not None:
            self._composer_title.configure(text=str(labels.get("composer_title", "Prompt Composer")))
        if self._hint_label is not None:
            self._hint_label.configure(text=str(labels.get("hint", "")))
        if self._send_button is not None:
            self._send_button.configure(text=str(labels.get("send", "Send")))
        if self._retry_button is not None:
            self._retry_button.configure(text=str(labels.get("retry", "Retry")))
        if self._copy_button is not None:
            self._copy_button.configure(text=str(labels.get("copy", "Copy Chat")))
        if self._stop_button is not None:
            self._stop_button.configure(text=str(labels.get("stop", "Stop")))
        if self._clear_button is not None:
            self._clear_button.configure(text=str(labels.get("clear", "Clear")))
        if self._runtime_badge is not None:
            self._runtime_badge.configure(text=str(labels.get("ended", "Ended")))
        chip_values = labels.get("chip_values")
        chip_labels = labels.get("chip_labels")
        if isinstance(chip_values, list) and isinstance(chip_labels, list):
            self._chip_values = [str(value) for value in chip_values]
            for button, label in zip(self._chip_buttons, chip_labels):
                button.configure(text=str(label))

    def set_callbacks(
        self,
        *,
        on_submit=None,
        on_retry=None,
        on_copy=None,
        on_stop=None,
        on_clear=None,
        on_chip=None,
    ) -> None:
        self._submit_callback = on_submit
        self._retry_callback = on_retry
        self._copy_callback = on_copy
        self._stop_callback = on_stop
        self._clear_callback = on_clear
        self._chip_callback = on_chip

    def focus_input(self) -> None:
        self.input.focus_set()

    def _configure_transcript_tags(self) -> None:
        self.transcript_text.tag_configure("title", foreground=PALETTE["base00"], font=("Noto Sans CJK SC", 8, "bold"))
        self.transcript_text.tag_configure("meta", foreground=PALETTE["base1"], font=("DejaVu Sans Mono", 7))
        self.transcript_text.tag_configure("user", foreground=PALETTE["blue"])
        self.transcript_text.tag_configure("assistant", foreground=PALETTE["base01"])
        self.transcript_text.tag_configure("tool", foreground=PALETTE["orange"])
        self.transcript_text.tag_configure("error", foreground=PALETTE["red"])
        self.transcript_text.tag_configure("system", foreground=PALETTE["green"])

    def set_runtime_state(self, state: str, text: str) -> None:
        if self._runtime_badge is None:
            return
        palette = {
            "running": (PALETTE["green"], PALETTE["base3"]),
            "stopped": (PALETTE["red"], PALETTE["base3"]),
            "ended": (PALETTE["base1"], PALETTE["base3"]),
        }
        background, foreground = palette.get(state, palette["ended"])
        self._runtime_badge.configure(text=text, background=background, foreground=foreground)

    def insert_prompt(self, text: str, replace: bool = False) -> None:
        if replace:
            self.input.delete("1.0", "end")
        if self.input.get("1.0", "end").strip():
            self.input.insert("end", "\n")
        self.input.insert("end", text)
        self.focus_input()

    def current_text(self) -> str:
        return self.input.get("1.0", "end").strip()

    def set_submit_callback(self, callback) -> None:
        self._submit_callback = callback

    def submit(self) -> None:
        text = self.input.get("1.0", "end").strip()
        if not text or self._submit_callback is None:
            return
        self.input.delete("1.0", "end")
        self._submit_callback(text)

    def add_message(self, text: str, role: str, title: str | None = None) -> int:
        self._message_seq += 1
        start_mark = f"msg_{self._message_seq}_start"
        end_mark = f"msg_{self._message_seq}_end"
        role_tag = role if role in {"user", "assistant", "tool", "error", "system"} else "assistant"
        block = self._format_block(text, title)
        self.transcript_text.configure(state="normal")
        self.transcript_text.mark_set(start_mark, "end-1c")
        self.transcript_text.insert("end", block)
        self.transcript_text.mark_set(end_mark, "end-1c")
        self.transcript_text.tag_add(role_tag, start_mark, end_mark)
        self._apply_header_tags(start_mark, end_mark, title)
        self.transcript_text.configure(state="disabled")
        self._message_widgets[self._message_seq] = (start_mark, end_mark, role_tag)
        self.after_idle(self._scroll_to_bottom)
        return self._message_seq

    def update_message(self, message_id: int, text: str, title: str | None = None) -> None:
        widgets = self._message_widgets.get(message_id)
        if widgets is None:
            return
        start_mark, end_mark, role_tag = widgets
        block = self._format_block(text, title)
        self.transcript_text.configure(state="normal")
        self.transcript_text.delete(start_mark, end_mark)
        self.transcript_text.insert(start_mark, block)
        self.transcript_text.mark_set(end_mark, f"{start_mark}+{len(block)}c")
        for tag in ("title", "meta", "user", "assistant", "tool", "error", "system"):
            self.transcript_text.tag_remove(tag, start_mark, end_mark)
        self.transcript_text.tag_add(role_tag, start_mark, end_mark)
        self._apply_header_tags(start_mark, end_mark, title)
        self.transcript_text.configure(state="disabled")
        self.after_idle(self._scroll_to_bottom)

    def remove_message(self, message_id: int) -> None:
        widgets = self._message_widgets.pop(message_id, None)
        if widgets is None:
            return
        start_mark, end_mark, _role_tag = widgets
        self.transcript_text.configure(state="normal")
        self.transcript_text.delete(start_mark, end_mark)
        self.transcript_text.configure(state="disabled")

    def clear(self) -> None:
        self.transcript_text.configure(state="normal")
        self.transcript_text.delete("1.0", "end")
        self.transcript_text.configure(state="disabled")
        self._message_widgets.clear()

    def _apply_header_tags(self, start_mark: str, end_mark: str, title: str | None) -> None:
        if not title:
            return
        line_end = f"{start_mark} lineend"
        self.transcript_text.tag_add("title", start_mark, line_end)
        meta_start = f"{start_mark}+{len(title) + 1}c"
        self.transcript_text.tag_add("meta", meta_start, line_end)

    def _on_retry(self) -> None:
        if self._retry_callback is not None:
            self._retry_callback()

    def _on_copy(self) -> None:
        if self._copy_callback is not None:
            self._copy_callback()

    def _on_stop(self) -> None:
        if self._stop_callback is not None:
            self._stop_callback()

    def _on_clear(self) -> None:
        if self._clear_callback is not None:
            self._clear_callback()

    def _on_chip(self, index: int) -> None:
        if self._chip_callback is None or index >= len(self._chip_values):
            return
        self._chip_callback(self._chip_values[index])

    def _on_submit(self, _event) -> str:
        self.submit()
        return "break"

    def _on_enter_submit(self, event) -> str | None:
        if bool(event.state & 0x0001):
            return None
        self.submit()
        return "break"

    def _on_insert_newline(self, _event) -> str:
        self.input.insert("insert", "\n")
        return "break"

    def _scroll_to_bottom(self) -> None:
        self.transcript_text.update_idletasks()
        self.transcript_text.yview_moveto(1.0)

    def _copy_message_text(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    def get_transcript_text(self) -> str:
        return self.transcript_text.get("1.0", "end").strip()

    def _copy_selected_or_all(self, _event=None) -> str:
        try:
            selected = self.transcript_text.get("sel.first", "sel.last")
        except tk.TclError:
            selected = self.get_transcript_text()
        if selected:
            self._copy_message_text(selected)
        return "break"

    def _select_all(self, _event=None) -> str:
        self.transcript_text.tag_add("sel", "1.0", "end-1c")
        self.transcript_text.mark_set("insert", "1.0")
        self.transcript_text.see("insert")
        return "break"

    def _show_transcript_menu(self, event) -> str:
        self._hide_transcript_menu()
        menu = tk.Menu(self, tearoff=False)
        menu.add_command(label="Copy", command=self._copy_selected_or_all)
        menu.add_command(label="Select All", command=self._select_all)
        self._transcript_menu = menu
        menu.tk_popup(event.x_root, event.y_root)
        menu.grab_release()
        return "break"

    def _dismiss_transcript_menu(self, _event=None) -> None:
        self._hide_transcript_menu()

    def _hide_transcript_menu(self) -> None:
        if self._transcript_menu is None:
            return
        try:
            self._transcript_menu.unpost()
            self._transcript_menu.destroy()
        except tk.TclError:
            pass
        self._transcript_menu = None

    @staticmethod
    def _format_block(text: str, title: str | None) -> str:
        stamp = time.strftime("%H:%M:%S")
        header = f"{title}  {stamp}\n" if title else ""
        body = text.rstrip()
        return f"{header}{body}\n\n"
