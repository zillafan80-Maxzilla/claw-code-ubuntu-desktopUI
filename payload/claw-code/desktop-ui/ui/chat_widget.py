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
        self._message_widgets: dict[int, tuple[tk.Frame, tk.Label | None, tk.Text, tk.Label | None, tk.Button | None]] = {}
        self._send_button: ttk.Button | None = None
        self._retry_button: ttk.Button | None = None
        self._copy_button: ttk.Button | None = None
        self._stop_button: ttk.Button | None = None
        self._clear_button: ttk.Button | None = None
        self._title_label: ttk.Label | None = None
        self._subtitle_label: ttk.Label | None = None
        self._hint_label: ttk.Label | None = None
        self._composer_title: ttk.Label | None = None
        self._chip_buttons: list[ttk.Button] = []
        self._chip_values: list[str] = []

        header = ttk.Frame(self, style="Shell.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)

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

        toolbar = ttk.Frame(header, style="Shell.TFrame")
        toolbar.grid(row=0, column=1, sticky="e")
        self._retry_button = ttk.Button(toolbar, text="Retry", command=self._on_retry)
        self._retry_button.grid(row=0, column=0, padx=(0, 6))
        self._copy_button = ttk.Button(toolbar, text="Copy Reply", command=self._on_copy)
        self._copy_button.grid(row=0, column=1, padx=(0, 6))
        self._stop_button = ttk.Button(toolbar, text="Stop", command=self._on_stop)
        self._stop_button.grid(row=0, column=2, padx=(0, 6))
        self._clear_button = ttk.Button(toolbar, text="Clear", command=self._on_clear)
        self._clear_button.grid(row=0, column=3)

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
        transcript_shell.grid_columnconfigure(0, weight=0)
        transcript_shell.grid_columnconfigure(1, weight=1)

        left_track = tk.Frame(
            transcript_shell,
            background=PALETTE["base1"],
            highlightthickness=1,
            highlightbackground=PALETTE["base00"],
            width=20,
        )
        left_track.grid(row=0, column=0, sticky="ns", padx=(0, 6))
        left_track.grid_propagate(False)
        left_track.rowconfigure(0, weight=1)
        left_track.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            transcript_shell,
            background=PALETTE["base3"],
            highlightthickness=0,
            borderwidth=0,
        )
        self.scrollbar = tk.Scrollbar(
            left_track,
            orient="vertical",
            command=self.canvas.yview,
            width=18,
            background=PALETTE["yellow"],
            troughcolor=PALETTE["base2"],
            activebackground=PALETTE["orange"],
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=0, sticky="ns")
        self.canvas.grid(row=0, column=1, sticky="nsew")

        self.transcript = ttk.Frame(self.canvas, style="Shell.TFrame")
        self.transcript.columnconfigure(0, weight=1)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.transcript, anchor="nw")
        self.transcript.bind("<Configure>", self._on_transcript_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

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
        self._send_button = ttk.Button(footer, text="Send", command=self.submit, style="Accent.TButton")
        self._send_button.grid(row=0, column=1, sticky="e")

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
            self._copy_button.configure(text=str(labels.get("copy", "Copy Reply")))
        if self._stop_button is not None:
            self._stop_button.configure(text=str(labels.get("stop", "Stop")))
        if self._clear_button is not None:
            self._clear_button.configure(text=str(labels.get("clear", "Clear")))
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
        palette = {
            "user": (PALETTE["blue"], PALETTE["base3"], "e"),
            "assistant": (PALETTE["base2"], PALETTE["base01"], "w"),
            "tool": ("#fdf0c2", PALETTE["base01"], "w"),
            "error": ("#fde9e7", PALETTE["red"], "w"),
            "system": ("#e8f5e7", PALETTE["green"], "w"),
        }
        background, foreground, sticky = palette.get(role, (PALETTE["base2"], PALETTE["base01"], "w"))

        outer = ttk.Frame(self.transcript, style="Shell.TFrame")
        outer.grid(sticky="ew", pady=8, padx=10)
        outer.columnconfigure(0, weight=1)

        card = tk.Frame(
            outer,
            background=background,
            highlightthickness=1,
            highlightbackground=PALETTE["base1"],
            padx=16,
            pady=12,
        )
        card.grid(sticky=sticky)

        header_widget = None
        meta_widget = None
        copy_button = None
        if title:
            header_row = tk.Frame(card, background=background)
            header_row.pack(fill="x", anchor="w")
        else:
            header_row = None
        if title:
            header_widget = tk.Label(
                header_row,
                text=title,
                background=background,
                foreground=foreground,
                font=("Noto Sans CJK SC", 8, "bold"),
                anchor="w",
            )
            header_widget.pack(side="left", anchor="w")
            copy_button = tk.Button(
                header_row,
                text="Copy",
                command=lambda value=text: self._copy_message_text(value),
                background=background,
                foreground=PALETTE["base00"],
                activebackground=background,
                activeforeground=foreground,
                borderwidth=0,
                highlightthickness=0,
                padx=6,
                pady=0,
                font=("DejaVu Sans Mono", 7),
                cursor="hand2",
            )
            copy_button.pack(side="right", anchor="e")
            meta_widget = tk.Label(
                card,
                text=time.strftime("%H:%M:%S"),
                background=background,
                foreground=PALETTE["base00"],
                font=("DejaVu Sans Mono", 7),
                anchor="w",
            )
            meta_widget.pack(anchor="w", pady=(2, 6))

        body = tk.Text(
            card,
            background=background,
            foreground=foreground,
            wrap="word",
            font=("Noto Sans CJK SC", 10),
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            padx=0,
            pady=0,
            height=max(1, min(text.count("\n") + 1, 20)),
            cursor="xterm",
            insertbackground=foreground,
        )
        body.insert("1.0", text)
        body.configure(state="disabled")
        body.pack(anchor="w", fill="x")
        body.bind("<Control-c>", lambda _event, widget=body: self._copy_from_text_widget(widget))
        body.bind("<Button-3>", lambda event, value=text: self._show_copy_menu(event, value))

        self._message_seq += 1
        self._message_widgets[self._message_seq] = (outer, header_widget, body, meta_widget, copy_button)
        self.after_idle(self._scroll_to_bottom)
        return self._message_seq

    def update_message(self, message_id: int, text: str, title: str | None = None) -> None:
        widgets = self._message_widgets.get(message_id)
        if widgets is None:
            return
        _outer, header, body, meta, copy_button = widgets
        body.configure(state="normal")
        body.delete("1.0", "end")
        body.insert("1.0", text)
        body.configure(height=max(1, min(text.count("\n") + 1, 20)))
        body.configure(state="disabled")
        if header is not None and title is not None:
            header.configure(text=title)
        if meta is not None:
            meta.configure(text=time.strftime("%H:%M:%S"))
        if copy_button is not None:
            copy_button.configure(command=lambda value=text: self._copy_message_text(value))
        self.after_idle(self._scroll_to_bottom)

    def remove_message(self, message_id: int) -> None:
        widgets = self._message_widgets.pop(message_id, None)
        if widgets is None:
            return
        outer, _header, _body, _meta, _copy = widgets
        outer.destroy()

    def clear(self) -> None:
        for child in self.transcript.winfo_children():
            child.destroy()
        self._message_widgets.clear()

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

    def _on_transcript_configure(self, _event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def _scroll_to_bottom(self) -> None:
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def _copy_message_text(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    def _copy_from_text_widget(self, widget: tk.Text) -> str:
        try:
            selected = widget.get("sel.first", "sel.last")
        except tk.TclError:
            selected = widget.get("1.0", "end").strip()
        if selected:
            self._copy_message_text(selected)
        return "break"

    def _show_copy_menu(self, event, text: str) -> str:
        menu = tk.Menu(self, tearoff=False)
        menu.add_command(label="Copy", command=lambda value=text: self._copy_message_text(value))
        menu.tk_popup(event.x_root, event.y_root)
        menu.grab_release()
        return "break"
