from __future__ import annotations

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
        self.rowconfigure(0, weight=1)
        self._submit_callback = None

        self.canvas = tk.Canvas(
            self,
            background=PALETTE["base3"],
            highlightthickness=0,
            borderwidth=0,
        )
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.transcript = ttk.Frame(self.canvas, style="Shell.TFrame")
        self.transcript.columnconfigure(0, weight=1)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.transcript, anchor="nw")
        self.transcript.bind("<Configure>", self._on_transcript_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        composer = ttk.Frame(self, style="Composer.TFrame", padding=(14, 12))
        composer.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        composer.columnconfigure(0, weight=1)

        self.input = tk.Text(
            composer,
            height=4,
            wrap="word",
            background=PALETTE["base2"],
            foreground=PALETTE["base01"],
            insertbackground=PALETTE["base01"],
            relief="flat",
            borderwidth=0,
            padx=12,
            pady=10,
            font=("Noto Sans CJK SC", 9),
        )
        self.input.grid(row=0, column=0, sticky="ew")
        self.input.bind("<Control-Return>", self._on_submit)
        self.input.bind("<Command-Return>", self._on_submit)

        send_button = ttk.Button(composer, text="发送", command=self.submit)
        send_button.grid(row=0, column=1, sticky="se", padx=(12, 0))

    def set_submit_callback(self, callback) -> None:
        self._submit_callback = callback

    def submit(self) -> None:
        text = self.input.get("1.0", "end").strip()
        if not text or self._submit_callback is None:
            return
        self.input.delete("1.0", "end")
        self._submit_callback(text)

    def add_message(self, text: str, role: str, title: str | None = None) -> None:
        palette = {
            "user": (PALETTE["blue"], PALETTE["base3"], "e"),
            "assistant": (PALETTE["base2"], PALETTE["base01"], "w"),
            "tool": ("#fdf0c2", PALETTE["base01"], "w"),
            "error": ("#fde9e7", PALETTE["red"], "w"),
            "system": ("#e8f5e7", PALETTE["green"], "w"),
        }
        background, foreground, sticky = palette.get(
            role, (PALETTE["base2"], PALETTE["base01"], "w")
        )

        outer = ttk.Frame(self.transcript, style="Shell.TFrame")
        outer.grid(sticky="ew", pady=7)
        outer.columnconfigure(0, weight=1)

        card = tk.Frame(
            outer,
            background=background,
            highlightthickness=1,
            highlightbackground=PALETTE["base1"],
            padx=14,
            pady=10,
        )
        card.grid(sticky=sticky)

        if title:
            header = tk.Label(
                card,
                text=title,
                background=background,
                foreground=foreground,
                font=("Noto Sans CJK SC", 7, "bold"),
                anchor="w",
            )
            header.pack(anchor="w", pady=(0, 6))

        body = tk.Label(
            card,
            text=text,
            background=background,
            foreground=foreground,
            justify="left",
            wraplength=820,
            font=("Noto Sans CJK SC", 9),
            anchor="w",
        )
        body.pack(anchor="w")
        self.after_idle(self._scroll_to_bottom)

    def clear(self) -> None:
        for child in self.transcript.winfo_children():
            child.destroy()

    def _on_submit(self, _event) -> str:
        self.submit()
        return "break"

    def _on_transcript_configure(self, _event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def _scroll_to_bottom(self) -> None:
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
