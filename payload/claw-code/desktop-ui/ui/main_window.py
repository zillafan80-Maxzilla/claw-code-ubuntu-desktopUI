from __future__ import annotations

import queue
import tkinter as tk
import time
from pathlib import Path
from tkinter import messagebox, ttk

from core.bridge import ClawBridge, CommandResult
from core.lifecycle import LifecycleManager
from core.settings import DesktopSettings, DesktopSettingsStore
from ui.chat_widget import ChatWidget


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
    "magenta": "#d33682",
}


class MainWindow(tk.Tk):
    def __init__(self, project_root: Path, lifecycle: LifecycleManager):
        super().__init__()
        self.project_root = Path(project_root)
        self.lifecycle = lifecycle
        self.settings_store = DesktopSettingsStore()
        self.bridge = ClawBridge(self.project_root, lifecycle, self.settings_store)
        self.results: queue.Queue[CommandResult] = queue.Queue()
        self.pending_messages: dict[str, list[dict[str, object]]] = {}

        self.title("Claw Code 桌面控制台")
        self.geometry("1520x980")
        self.minsize(520, 360)
        self.configure(background=PALETTE["base3"])
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.status_var = tk.StringVar(value="就绪")
        self.active_var = tk.StringVar(value="0 个运行中")
        self.model_summary_var = tk.StringVar()
        self.endpoint_var = tk.StringVar()
        self.tool_mode_var = tk.StringVar()
        self.autopilot_var = tk.BooleanVar(value=False)

        self.model_entry_var = tk.StringVar()
        self.base_url_entry_var = tk.StringVar()
        self.api_key_entry_var = tk.StringVar()
        self.tool_style_entry_var = tk.StringVar()

        self._build_style()
        self._build_menu()
        self._build_layout()
        self._load_settings_into_form()
        self._seed_welcome()
        self.after(120, self._drain_results)
        self.after(800, self._refresh_process_list)

    def _build_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Shell.TFrame", background=PALETTE["base3"])
        style.configure("Sidebar.TFrame", background=PALETTE["base2"])
        style.configure("Panel.TLabelframe", background=PALETTE["base2"], foreground=PALETTE["base01"])
        style.configure("Panel.TLabelframe.Label", background=PALETTE["base2"], foreground=PALETTE["base01"], font=("Noto Sans CJK SC", 9, "bold"))
        style.configure("Composer.TFrame", background=PALETTE["base2"])
        style.configure("SidebarTitle.TLabel", background=PALETTE["base2"], foreground=PALETTE["base01"], font=("Noto Sans CJK SC", 11, "bold"))
        style.configure("Muted.TLabel", background=PALETTE["base2"], foreground=PALETTE["base00"], font=("Noto Sans CJK SC", 8))
        style.configure("Value.TLabel", background=PALETTE["base2"], foreground=PALETTE["base01"], font=("Noto Sans CJK SC", 8, "bold"))
        style.configure("Accent.TButton", font=("Noto Sans CJK SC", 8, "bold"))
        style.configure("TButton", background=PALETTE["base2"], foreground=PALETTE["base01"])
        style.map(
            "TButton",
            background=[("active", "#e4ddc8")],
            foreground=[("active", PALETTE["base01"])],
        )

    def _build_menu(self) -> None:
        menu_font = ("Noto Sans CJK SC", 8)
        menubar = tk.Menu(self, tearoff=False, background=PALETTE["base2"], foreground=PALETTE["base01"], font=menu_font)

        session_menu = tk.Menu(menubar, tearoff=False, background=PALETTE["base2"], foreground=PALETTE["base01"], font=menu_font)
        session_menu.add_command(label="清空对话", command=self._clear_chat)
        session_menu.add_separator()
        session_menu.add_command(label="退出系统", command=self._on_close)
        menubar.add_cascade(label="会话", menu=session_menu)

        model_menu = tk.Menu(menubar, tearoff=False, background=PALETTE["base2"], foreground=PALETTE["base01"], font=menu_font)
        model_menu.add_command(label="保存并应用模型配置", command=self._save_settings)
        model_menu.add_command(label="重新载入当前配置", command=self._load_settings_into_form)
        model_menu.add_separator()
        model_menu.add_command(label="切换为自动工具适配", command=lambda: self._set_tool_style("auto"))
        model_menu.add_command(label="切换为原生工具协议", command=lambda: self._set_tool_style("native"))
        model_menu.add_command(label="切换为 Gemma JSON 适配", command=lambda: self._set_tool_style("gemma-json"))
        menubar.add_cascade(label="模型与接口", menu=model_menu)

        run_menu = tk.Menu(menubar, tearoff=False, background=PALETTE["base2"], foreground=PALETTE["base01"], font=menu_font)
        run_menu.add_command(label="运行状态", command=lambda: self._submit_request("/status"))
        run_menu.add_command(label="环境体检", command=lambda: self._submit_request("/doctor"))
        run_menu.add_command(label="沙箱状态", command=lambda: self._submit_request("/sandbox"))
        run_menu.add_command(label="版本信息", command=lambda: self._submit_request("/version"))
        run_menu.add_command(label="智能体清单", command=lambda: self._submit_request("/agents"))
        run_menu.add_command(label="MCP 清单", command=lambda: self._submit_request("/mcp"))
        run_menu.add_command(label="技能清单", command=lambda: self._submit_request("/skills"))
        menubar.add_cascade(label="运行", menu=run_menu)

        view_menu = tk.Menu(menubar, tearoff=False, background=PALETTE["base2"], foreground=PALETTE["base01"], font=menu_font)
        view_menu.add_command(label="刷新进程视图", command=self._refresh_process_list)
        view_menu.add_command(label="刷新执行日志", command=self._refresh_log)
        menubar.add_cascade(label="视图", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=False, background=PALETTE["base2"], foreground=PALETTE["base01"], font=menu_font)
        help_menu.add_command(label="命令帮助", command=lambda: self._submit_request("/help"))
        help_menu.add_command(label="关于工具调用适配", command=self._show_tool_help)
        menubar.add_cascade(label="帮助", menu=help_menu)
        self.config(menu=menubar)

    def _build_layout(self) -> None:
        root = ttk.Frame(self, style="Shell.TFrame", padding=18)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=5)
        root.columnconfigure(1, weight=2)
        root.rowconfigure(0, weight=1)

        left = ttk.Frame(root, style="Shell.TFrame")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        left.rowconfigure(2, weight=1)
        left.columnconfigure(0, weight=1)

        masthead = ttk.Frame(left, style="Shell.TFrame")
        masthead.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(
            masthead,
            text="Claw Code 桌面控制台",
            background=PALETTE["base3"],
            foreground=PALETTE["base01"],
            font=("Noto Sans CJK SC", 20, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            masthead,
            text="Solarized Light 中文界面，统一承载模型配置、命令面板、进程托管与安全清理。",
            background=PALETTE["base3"],
            foreground=PALETTE["base00"],
            font=("Noto Sans CJK SC", 9),
        ).pack(anchor="w", pady=(4, 0))

        summary = tk.Frame(left, background=PALETTE["base2"], highlightthickness=1, highlightbackground=PALETTE["base1"], padx=14, pady=12)
        summary.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        summary.grid_columnconfigure(1, weight=1)
        self._summary_row(summary, 0, "当前模型", self.model_summary_var)
        self._summary_row(summary, 1, "接口地址", self.endpoint_var)
        self._summary_row(summary, 2, "工具适配", self.tool_mode_var)

        self.chat = ChatWidget(left)
        self.chat.grid(row=2, column=0, sticky="nsew")
        self.chat.set_submit_callback(self._submit_request)

        sidebar_shell = ttk.Frame(root, style="Sidebar.TFrame")
        sidebar_shell.grid(row=0, column=1, sticky="nsew")
        sidebar_shell.columnconfigure(0, weight=1)
        sidebar_shell.rowconfigure(0, weight=1)

        self.sidebar_canvas = tk.Canvas(
            sidebar_shell,
            background=PALETTE["base2"],
            highlightthickness=0,
            borderwidth=0,
        )
        self.sidebar_canvas.grid(row=0, column=0, sticky="nsew")
        sidebar_scrollbar = ttk.Scrollbar(
            sidebar_shell,
            orient="vertical",
            command=self.sidebar_canvas.yview,
        )
        sidebar_scrollbar.grid(row=0, column=1, sticky="ns")
        self.sidebar_canvas.configure(yscrollcommand=sidebar_scrollbar.set)

        sidebar = ttk.Frame(self.sidebar_canvas, style="Sidebar.TFrame", padding=18)
        sidebar.columnconfigure(0, weight=1)
        sidebar.rowconfigure(5, weight=1)
        self.sidebar_window = self.sidebar_canvas.create_window(
            (0, 0), window=sidebar, anchor="nw"
        )
        sidebar.bind("<Configure>", self._on_sidebar_configure)
        self.sidebar_canvas.bind("<Configure>", self._on_sidebar_canvas_configure)
        self.sidebar_canvas.bind_all("<MouseWheel>", self._on_mousewheel, add="+")

        ttk.Label(sidebar, text="运行概览", style="SidebarTitle.TLabel").grid(row=0, column=0, sticky="w")

        runtime_panel = ttk.LabelFrame(sidebar, text="状态与执行", style="Panel.TLabelframe", padding=12)
        runtime_panel.grid(row=1, column=0, sticky="ew", pady=(12, 10))
        runtime_panel.columnconfigure(0, weight=1)
        ttk.Label(runtime_panel, text="系统状态", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(runtime_panel, textvariable=self.status_var, style="Value.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 8))
        ttk.Label(runtime_panel, text="托管进程", style="Muted.TLabel").grid(row=2, column=0, sticky="w")
        ttk.Label(runtime_panel, textvariable=self.active_var, style="Value.TLabel").grid(row=3, column=0, sticky="w")
        ttk.Checkbutton(
            runtime_panel,
            text="启用高权限自动执行（danger-full-access）",
            variable=self.autopilot_var,
            command=self._toggle_autopilot,
        ).grid(row=4, column=0, sticky="w", pady=(10, 0))

        config_panel = ttk.LabelFrame(sidebar, text="模型与接口配置", style="Panel.TLabelframe", padding=12)
        config_panel.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        config_panel.columnconfigure(1, weight=1)
        self._config_row(config_panel, 0, "模型名称", self.model_entry_var)
        self._config_row(config_panel, 1, "接口基址", self.base_url_entry_var)
        self._config_row(config_panel, 2, "API 密钥", self.api_key_entry_var, show="*")
        ttk.Label(config_panel, text="工具适配", style="Muted.TLabel").grid(row=3, column=0, sticky="w", pady=(8, 0))
        tool_style = ttk.Combobox(
            config_panel,
            textvariable=self.tool_style_entry_var,
            state="readonly",
            values=["auto", "native", "gemma-json"],
        )
        tool_style.grid(row=3, column=1, sticky="ew", pady=(8, 0))
        ttk.Button(config_panel, text="保存并立即应用", command=self._save_settings, style="Accent.TButton").grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        quick_panel = ttk.LabelFrame(sidebar, text="快捷命令", style="Panel.TLabelframe", padding=12)
        quick_panel.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        quick_panel.columnconfigure((0, 1), weight=1)
        buttons = [
            ("状态", "/status"),
            ("体检", "/doctor"),
            ("沙箱", "/sandbox"),
            ("版本", "/version"),
            ("智能体", "/agents"),
            ("MCP", "/mcp"),
            ("技能", "/skills"),
            ("帮助", "/help"),
        ]
        for index, (label, command) in enumerate(buttons):
            ttk.Button(
                quick_panel,
                text=label,
                command=lambda value=command: self._submit_request(value),
                style="Accent.TButton",
            ).grid(row=index // 2, column=index % 2, sticky="ew", padx=4, pady=4)

        lists_panel = ttk.Frame(sidebar, style="Sidebar.TFrame")
        lists_panel.grid(row=5, column=0, sticky="nsew")
        lists_panel.columnconfigure(0, weight=1)
        lists_panel.rowconfigure(1, weight=1)
        lists_panel.rowconfigure(3, weight=1)

        ttk.Label(lists_panel, text="进程列表", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.process_list = tk.Listbox(
            lists_panel,
            height=7,
            background=PALETTE["base3"],
            foreground=PALETTE["base01"],
            borderwidth=1,
            highlightthickness=0,
            selectbackground=PALETTE["blue"],
            selectforeground=PALETTE["base3"],
            font=("DejaVu Sans Mono", 10),
        )
        self.process_list.grid(row=1, column=0, sticky="nsew", pady=(6, 12))

        ttk.Label(lists_panel, text="执行日志", style="Muted.TLabel").grid(row=2, column=0, sticky="w")
        self.log_list = tk.Listbox(
            lists_panel,
            height=12,
            background=PALETTE["base3"],
            foreground=PALETTE["base01"],
            borderwidth=1,
            highlightthickness=0,
            selectbackground=PALETTE["cyan"],
            selectforeground=PALETTE["base3"],
            font=("DejaVu Sans Mono", 10),
        )
        self.log_list.grid(row=3, column=0, sticky="nsew", pady=(6, 0))

        footer = ttk.Frame(sidebar, style="Sidebar.TFrame")
        footer.grid(row=6, column=0, sticky="ew", pady=(12, 0))
        footer.columnconfigure((0, 1), weight=1)
        ttk.Button(footer, text="清空对话", command=self._clear_chat).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(footer, text="刷新配置", command=self._load_settings_into_form).grid(row=0, column=1, sticky="ew")

    def _summary_row(self, parent: tk.Misc, row: int, label: str, variable: tk.StringVar) -> None:
        tk.Label(
            parent,
            text=label,
            background=PALETTE["base2"],
            foreground=PALETTE["base00"],
            font=("Noto Sans CJK SC", 8),
            anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=3)
        tk.Label(
            parent,
            textvariable=variable,
            background=PALETTE["base2"],
            foreground=PALETTE["base01"],
            font=("Noto Sans CJK SC", 8, "bold"),
            anchor="w",
        ).grid(row=row, column=1, sticky="w", pady=3)

    def _config_row(
        self,
        parent: tk.Misc,
        row: int,
        label: str,
        variable: tk.StringVar,
        show: str | None = None,
    ) -> None:
        ttk.Label(parent, text=label, style="Muted.TLabel").grid(row=row, column=0, sticky="w", pady=(8 if row else 0, 0))
        entry = ttk.Entry(parent, textvariable=variable, show=show or "")
        entry.grid(row=row, column=1, sticky="ew", pady=(8 if row else 0, 0))

    def _seed_welcome(self) -> None:
        self.chat.add_message(
            "桌面界面已启动。右侧可直接配置模型、接口地址和工具适配方式，左侧对话区会持续显示当前模型摘要。",
            role="system",
            title="启动器",
        )
        self.chat.add_message(
            "Gemma 类模型默认走“自动适配”，当后端不稳定支持原生 tools 时，CLI 会切到 Gemma JSON 提示适配层。",
            role="assistant",
            title="模型适配说明",
        )

    def _load_settings_into_form(self) -> None:
        settings = self.settings_store.load()
        self.model_entry_var.set(settings.model)
        self.base_url_entry_var.set(settings.base_url)
        self.api_key_entry_var.set(settings.api_key)
        self.tool_style_entry_var.set(settings.tool_call_style)
        self._refresh_model_summary(settings)
        self.status_var.set("配置已载入")

    def _refresh_model_summary(self, settings: DesktopSettings | None = None) -> None:
        current = settings or self.settings_store.load()
        self.model_summary_var.set(f"{current.model} · {current.provider_label()}")
        self.endpoint_var.set(current.base_url)
        self.tool_mode_var.set(current.tool_style_label())

    def _save_settings(self) -> None:
        model = self.model_entry_var.get().strip()
        base_url = self.base_url_entry_var.get().strip()
        api_key = self.api_key_entry_var.get().strip()
        tool_style = self.tool_style_entry_var.get().strip()

        if not model:
            messagebox.showerror("配置错误", "模型名称不能为空。")
            return
        if not (base_url.startswith("http://") or base_url.startswith("https://")):
            messagebox.showerror("配置错误", "接口基址必须以 http:// 或 https:// 开头。")
            return
        if tool_style not in {"auto", "native", "gemma-json"}:
            messagebox.showerror("配置错误", "工具适配模式只能是 auto、native 或 gemma-json。")
            return

        settings = DesktopSettings(
            model=model,
            base_url=base_url,
            api_key=api_key,
            tool_call_style=tool_style,
        )
        self.settings_store.save(settings)
        self._refresh_model_summary(settings)
        self.chat.add_message(
            f"模型配置已保存。\n模型：{settings.model}\n接口：{settings.base_url}\n工具适配：{settings.tool_style_label()}",
            role="system",
            title="配置已应用",
        )
        self.status_var.set("模型配置已更新")

    def _set_tool_style(self, style: str) -> None:
        self.tool_style_entry_var.set(style)
        self._save_settings()

    def _show_tool_help(self) -> None:
        messagebox.showinfo(
            "工具调用适配说明",
            "自动适配：Gemma + OpenAI 兼容后端时，优先启用 Gemma JSON 提示适配；其他模型保留原生 tools。\n\n"
            "原生工具协议：直接使用 provider-native tools/tool_calls。\n\n"
            "Gemma JSON 提示适配：把工具定义注入系统提示词，要求模型返回 JSON 对象，再由 CLI 回解析并执行工具。",
        )

    def _submit_request(self, text: str) -> None:
        request = text.strip()
        if not request:
            return
        if request in {"/clear", "/清空"}:
            self._clear_chat()
            return
        self.chat.add_message(request, role="user", title="用户请求")
        self.status_var.set("命令执行中")
        try:
            pending_id = self.chat.add_message(
                "正在生成回复…",
                role="assistant",
                title="模型处理中",
            )
            self.pending_messages.setdefault(request, []).append({
                "message_id": pending_id,
                "started_at": time.time(),
            })
            self._tick_pending_message(request)
            self.bridge.submit(request, self.results.put)
            self._refresh_log()
            self._refresh_process_list()
        except Exception as exc:
            self._clear_pending_message(request)
            self.chat.add_message(str(exc), role="error", title="桌面校验")
            self.status_var.set("请求被拒绝")

    def _toggle_autopilot(self) -> None:
        state = self.bridge.set_autopilot(self.autopilot_var.get())
        self.status_var.set(state)
        self.chat.add_message(state, role="system", title="权限模式")

    def _clear_chat(self) -> None:
        self.chat.clear()
        self._seed_welcome()
        self.status_var.set("对话区已清空")

    def _drain_results(self) -> None:
        try:
            while True:
                result = self.results.get_nowait()
                self._handle_result(result)
        except queue.Empty:
            pass
        finally:
            self.after(120, self._drain_results)

    def _handle_result(self, result: CommandResult) -> None:
        summary = f"退出码 {result.exit_code} · {result.duration_seconds:.2f}s"
        self.status_var.set(summary)
        pending_queue = self.pending_messages.get(result.request_text, [])
        pending = pending_queue.pop(0) if pending_queue else None
        if not pending_queue and result.request_text in self.pending_messages:
            self.pending_messages.pop(result.request_text, None)

        if result.stdout:
            payload = self._render_stdout(result)
            if pending and payload:
                self.chat.update_message(
                    int(pending["message_id"]),
                    payload,
                    title="模型回复",
                )
            elif payload:
                self.chat.add_message(payload, role="assistant", title="模型回复")
            elif pending:
                self.chat.remove_message(int(pending["message_id"]))
        if result.stderr:
            self.chat.add_message(result.stderr, role="error", title="标准错误")
        if not result.stdout and not result.stderr:
            if pending:
                self.chat.update_message(
                    int(pending["message_id"]),
                    "命令已完成，但没有输出内容。",
                    title="CLI",
                )
            else:
                self.chat.add_message("命令已完成，但没有输出内容。", role="tool", title="CLI")

        self._refresh_log()
        self._refresh_process_list()

    def _render_stdout(self, result: CommandResult) -> str:
        if isinstance(result.parsed_stdout, dict):
            message = result.parsed_stdout.get("message")
            if isinstance(message, str):
                return message.strip()
        return result.stdout

    def _tick_pending_message(self, request: str) -> None:
        pending_queue = self.pending_messages.get(request)
        if not pending_queue:
            return
        pending = pending_queue[0]
        elapsed = max(time.time() - float(pending["started_at"]), 0.0)
        self.chat.update_message(
            int(pending["message_id"]),
            f"正在生成回复…\n已等待 {elapsed:.1f} 秒",
            title="模型处理中",
        )
        self.after(400, lambda: self._tick_pending_message(request))

    def _clear_pending_message(self, request: str) -> None:
        pending_queue = self.pending_messages.get(request, [])
        pending = pending_queue.pop() if pending_queue else None
        if not pending_queue and request in self.pending_messages:
            self.pending_messages.pop(request, None)
        if pending is None:
            return
        self.chat.remove_message(int(pending["message_id"]))

    def _refresh_log(self) -> None:
        self.log_list.delete(0, "end")
        for row in self.bridge.history[-100:]:
            self.log_list.insert("end", row)
        if self.log_list.size():
            self.log_list.yview_moveto(1.0)

    def _refresh_process_list(self) -> None:
        rows = self.bridge.active_process_rows()
        self.process_list.delete(0, "end")
        for row in rows or ["空闲"]:
            self.process_list.insert("end", row)
        self.active_var.set(f"{self.bridge.active_process_count()} 个运行中")
        self.after(800, self._refresh_process_list)

    def _on_sidebar_configure(self, _event) -> None:
        self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all"))

    def _on_sidebar_canvas_configure(self, event) -> None:
        self.sidebar_canvas.itemconfigure(self.sidebar_window, width=event.width)

    def _on_mousewheel(self, event) -> None:
        if self.sidebar_canvas.winfo_exists():
            self.sidebar_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_close(self) -> None:
        try:
            self.status_var.set("正在停止托管进程")
            self.bridge.shutdown()
            self.lifecycle.shutdown()
        except Exception as exc:
            if not messagebox.askyesno("清理异常", f"清理进程时发生异常：\n{exc}\n\n仍要关闭吗？"):
                return
        self.destroy()
