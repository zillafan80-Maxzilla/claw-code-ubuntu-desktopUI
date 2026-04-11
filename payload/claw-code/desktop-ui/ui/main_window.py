from __future__ import annotations

import queue
import shutil
import subprocess
import threading
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

APP_VERSION = "1.3"
APP_VERSION_NPM = "1.3.0"
NPM_PACKAGE_NAME = "claw-code-ubuntu-desktopui"
SUPPORTED_LOCALES = ("en", "ja", "ko", "zh")
LANGUAGE_LABELS = {
    "en": "English",
    "ja": "日本語",
    "ko": "한국어",
    "zh": "中文",
}

I18N = {
    "en": {
        "window_title": "Claw Code Desktop Console",
        "menu_session": "Session",
        "menu_model": "Model & API",
        "menu_run": "Run",
        "menu_view": "View",
        "menu_language": "Language",
        "menu_help": "Help",
        "clear_chat": "Clear Chat",
        "exit_system": "Exit",
        "save_apply_model": "Save And Apply Model Settings",
        "reload_settings": "Reload Current Settings",
        "tool_style_auto": "Switch To Automatic Adapter",
        "tool_style_native": "Switch To Native Tool Protocol",
        "tool_style_gemma": "Switch To Gemma JSON Adapter",
        "run_status": "Runtime Status",
        "run_doctor": "Environment Doctor",
        "run_sandbox": "Sandbox Status",
        "run_version": "Version",
        "run_agents": "Agents",
        "run_mcp": "MCP",
        "run_skills": "Skills",
        "view_processes": "Refresh Process View",
        "view_logs": "Refresh Execution Log",
        "help_commands": "Command Help",
        "help_update": "Update Desktop Components",
        "help_tooling": "Tool Calling Adapter Notes",
        "help_version": "Current Version {version}",
        "title": "Claw Code Desktop Console",
        "subtitle": "Solarized Light desktop shell for model setup, command routing, process supervision, and safe cleanup. Release {version}.",
        "summary_model": "Current Model",
        "summary_endpoint": "Endpoint",
        "summary_tool_mode": "Tool Adapter",
        "sidebar_title": "Runtime Overview",
        "runtime_panel": "Status And Execution",
        "status_label": "System Status",
        "process_count_label": "Managed Processes",
        "autopilot": "Enable Danger Full Access Auto Execution",
        "config_panel": "Model And API Configuration",
        "config_model": "Model Name",
        "config_base_url": "Base URL",
        "config_api_key": "API Key",
        "config_tool_style": "Tool Adapter",
        "config_save": "Save And Apply Now",
        "quick_panel": "Quick Commands",
        "quick_status": "Status",
        "quick_doctor": "Doctor",
        "quick_sandbox": "Sandbox",
        "quick_version": "Version",
        "quick_agents": "Agents",
        "quick_mcp": "MCP",
        "quick_skills": "Skills",
        "quick_help": "Help",
        "process_list": "Processes",
        "execution_log": "Execution Log",
        "footer_clear": "Clear Chat",
        "footer_reload": "Reload Settings",
        "welcome_title": "Launcher",
        "welcome_message": "The desktop interface is ready. Configure model, endpoint, API key, language, and tool mode from the right side. The left transcript always shows the active model summary.",
        "adapter_title": "Adapter Note",
        "adapter_message": "Gemma-family models default to automatic adaptation. When the backend is unstable with native tools, the CLI falls back to the Gemma JSON prompt adapter.",
        "status_ready": "Ready",
        "status_loaded": "Settings loaded",
        "status_saved": "Model settings updated",
        "status_running": "Command running",
        "status_denied": "Request rejected",
        "status_cleared": "Chat cleared",
        "status_update_running": "Update task running",
        "status_update_done": "Update completed. Restart pending",
        "status_update_failed": "Update failed",
        "status_shutdown": "Stopping managed processes",
        "busy_count": "{count} running",
        "idle_process": "Idle",
        "user_request_title": "User Request",
        "pending_title": "Model Processing",
        "pending_body": "Generating reply...\nWaited {seconds:.1f} seconds",
        "reply_title": "Model Reply",
        "stderr_title": "Standard Error",
        "validation_title": "Desktop Validation",
        "permission_mode_title": "Permission Mode",
        "cli_title": "CLI",
        "no_output": "The command completed without output.",
        "tool_help_title": "Tool Calling Adapter",
        "tool_help_message": "Automatic adaptation prefers the Gemma JSON prompt adapter for Gemma models on OpenAI-compatible backends. Other models keep native tools.\n\nNative Tool Protocol uses provider-native tool_calls.\n\nGemma JSON Prompt Adapter injects tool definitions into the prompt, asks the model for JSON, then lets the CLI parse and execute tools.",
        "version_info_title": "Version Info",
        "version_info_message": "Claw Code Ubuntu Desktop UI\nCurrent version: {version}\nUpdate channel: npm / GitHub Release",
        "update_confirm_title": "Update Desktop Components",
        "update_confirm_message": "The app will install the latest npm release and redeploy desktop components into the current claw-code root.\n\nRestarting the window after update is recommended. Continue?",
        "update_task_title": "Update Task",
        "update_task_body": "Checking for the latest published package and redeploying the current desktop components.",
        "update_success_title": "Update Completed",
        "update_success_body": "{details}\n\nClose and reopen the desktop window to load the latest version.",
        "update_error_title": "Update Failed",
        "update_error_body": "The update failed and returned no details.",
        "update_missing_npm": "npm was not found. Automatic update cannot continue.",
        "update_prompt_title": "Update Available",
        "update_prompt_body": "A newer desktop package is available.\n\nCurrent version: {current}\nLatest version: {latest}\n\nDo you want to update now?",
        "language_changed_title": "Language",
        "language_changed_body": "Language switched to {language}.",
        "config_error_title": "Configuration Error",
        "config_error_model": "Model name cannot be empty.",
        "config_error_base_url": "Base URL must start with http:// or https://.",
        "config_error_tool_style": "Tool adapter must be auto, native, or gemma-json.",
        "settings_saved_message": "Model settings saved.\nModel: {model}\nEndpoint: {base_url}\nTool adapter: {tool_style}\nLanguage: {language}",
        "settings_saved_title": "Configuration Applied",
        "cleanup_error_title": "Cleanup Error",
        "cleanup_error_body": "An error occurred while cleaning processes:\n{error}\n\nClose anyway?",
    },
    "ja": {
        "window_title": "Claw Code デスクトップコンソール",
        "menu_session": "セッション",
        "menu_model": "モデルと API",
        "menu_run": "実行",
        "menu_view": "表示",
        "menu_language": "言語",
        "menu_help": "ヘルプ",
        "clear_chat": "会話をクリア",
        "exit_system": "終了",
        "save_apply_model": "モデル設定を保存して適用",
        "reload_settings": "現在の設定を再読込",
        "tool_style_auto": "自動適応に切り替え",
        "tool_style_native": "ネイティブツールに切り替え",
        "tool_style_gemma": "Gemma JSON に切り替え",
        "run_status": "実行状態",
        "run_doctor": "環境診断",
        "run_sandbox": "サンドボックス状態",
        "run_version": "バージョン",
        "run_agents": "エージェント",
        "run_mcp": "MCP",
        "run_skills": "スキル",
        "view_processes": "プロセス表示を更新",
        "view_logs": "実行ログを更新",
        "help_commands": "コマンドヘルプ",
        "help_update": "デスクトップコンポーネントを更新",
        "help_tooling": "ツール呼び出し適応の説明",
        "help_version": "現在のバージョン {version}",
        "title": "Claw Code デスクトップコンソール",
        "subtitle": "Solarized Light ベースのデスクトップ UI。モデル設定、コマンド中継、プロセス管理、安全な終了処理を統合します。リリース {version}。",
        "summary_model": "現在のモデル",
        "summary_endpoint": "エンドポイント",
        "summary_tool_mode": "ツール適応",
        "sidebar_title": "実行概要",
        "runtime_panel": "状態と実行",
        "status_label": "システム状態",
        "process_count_label": "管理中プロセス",
        "autopilot": "危険な自動実行を有効化",
        "config_panel": "モデルと API 設定",
        "config_model": "モデル名",
        "config_base_url": "ベース URL",
        "config_api_key": "API キー",
        "config_tool_style": "ツール適応",
        "config_save": "保存してすぐ適用",
        "quick_panel": "クイックコマンド",
        "quick_status": "状態",
        "quick_doctor": "診断",
        "quick_sandbox": "サンドボックス",
        "quick_version": "バージョン",
        "quick_agents": "エージェント",
        "quick_mcp": "MCP",
        "quick_skills": "スキル",
        "quick_help": "ヘルプ",
        "process_list": "プロセス一覧",
        "execution_log": "実行ログ",
        "footer_clear": "会話をクリア",
        "footer_reload": "設定を再読込",
        "welcome_title": "ランチャー",
        "welcome_message": "デスクトップ UI が起動しました。右側でモデル、接続先、API キー、言語、ツール適応を設定できます。左側には現在のモデル概要が常に表示されます。",
        "adapter_title": "適応メモ",
        "adapter_message": "Gemma 系モデルは既定で自動適応を利用します。バックエンドがネイティブ tools に不安定な場合、CLI は Gemma JSON プロンプト適応に切り替えます。",
        "status_ready": "準備完了",
        "status_loaded": "設定を読み込みました",
        "status_saved": "モデル設定を更新しました",
        "status_running": "コマンド実行中",
        "status_denied": "リクエストは拒否されました",
        "status_cleared": "会話をクリアしました",
        "status_update_running": "更新タスクを実行中",
        "status_update_done": "更新完了。再起動待ち",
        "status_update_failed": "更新に失敗しました",
        "status_shutdown": "管理中プロセスを停止中",
        "busy_count": "{count} 件実行中",
        "idle_process": "アイドル",
        "user_request_title": "ユーザー要求",
        "pending_title": "モデル処理中",
        "pending_body": "返信を生成中...\n待機時間 {seconds:.1f} 秒",
        "reply_title": "モデル返信",
        "stderr_title": "標準エラー",
        "validation_title": "デスクトップ検証",
        "permission_mode_title": "権限モード",
        "cli_title": "CLI",
        "no_output": "コマンドは完了しましたが出力はありませんでした。",
        "tool_help_title": "ツール呼び出し適応",
        "tool_help_message": "自動適応では、OpenAI 互換バックエンド上の Gemma に対して Gemma JSON プロンプト適応を優先します。他のモデルはネイティブ tools を維持します。\n\nネイティブツールプロトコルは provider-native tool_calls を使用します。\n\nGemma JSON プロンプト適応では、ツール定義をプロンプトへ注入し、モデルに JSON を返させ、CLI がそれを解析してツールを実行します。",
        "version_info_title": "バージョン情報",
        "version_info_message": "Claw Code Ubuntu Desktop UI\n現在のバージョン: {version}\n更新チャネル: npm / GitHub Release",
        "update_confirm_title": "デスクトップコンポーネントを更新",
        "update_confirm_message": "npm の最新リリースをインストールし、現在の claw-code ルートにデスクトップコンポーネントを再配置します。\n\n更新後はウィンドウの再起動を推奨します。続行しますか？",
        "update_task_title": "更新タスク",
        "update_task_body": "最新の公開パッケージを確認し、現在のデスクトップコンポーネントを再配置しています。",
        "update_success_title": "更新完了",
        "update_success_body": "{details}\n\n最新バージョンを読み込むにはデスクトップウィンドウを閉じて再度開いてください。",
        "update_error_title": "更新失敗",
        "update_error_body": "更新に失敗しました。詳細は返されませんでした。",
        "update_missing_npm": "npm が見つかりません。自動更新を続行できません。",
        "update_prompt_title": "更新があります",
        "update_prompt_body": "新しいデスクトップパッケージが利用可能です。\n\n現在のバージョン: {current}\n最新バージョン: {latest}\n\n今すぐ更新しますか？",
        "language_changed_title": "言語",
        "language_changed_body": "{language} に切り替えました。",
        "config_error_title": "設定エラー",
        "config_error_model": "モデル名は空にできません。",
        "config_error_base_url": "ベース URL は http:// または https:// で始まる必要があります。",
        "config_error_tool_style": "ツール適応は auto、native、gemma-json のいずれかである必要があります。",
        "settings_saved_message": "モデル設定を保存しました。\nモデル: {model}\nエンドポイント: {base_url}\nツール適応: {tool_style}\n言語: {language}",
        "settings_saved_title": "設定を適用しました",
        "cleanup_error_title": "クリーンアップエラー",
        "cleanup_error_body": "プロセスのクリーンアップ中にエラーが発生しました:\n{error}\n\nそれでも閉じますか？",
    },
    "ko": {
        "window_title": "Claw Code 데스크톱 콘솔",
        "menu_session": "세션",
        "menu_model": "모델 및 API",
        "menu_run": "실행",
        "menu_view": "보기",
        "menu_language": "언어",
        "menu_help": "도움말",
        "clear_chat": "대화 지우기",
        "exit_system": "종료",
        "save_apply_model": "모델 설정 저장 및 적용",
        "reload_settings": "현재 설정 다시 불러오기",
        "tool_style_auto": "자동 적응으로 전환",
        "tool_style_native": "기본 도구 프로토콜로 전환",
        "tool_style_gemma": "Gemma JSON 어댑터로 전환",
        "run_status": "실행 상태",
        "run_doctor": "환경 진단",
        "run_sandbox": "샌드박스 상태",
        "run_version": "버전",
        "run_agents": "에이전트",
        "run_mcp": "MCP",
        "run_skills": "스킬",
        "view_processes": "프로세스 보기 새로고침",
        "view_logs": "실행 로그 새로고침",
        "help_commands": "명령 도움말",
        "help_update": "데스크톱 구성요소 업데이트",
        "help_tooling": "도구 호출 적응 안내",
        "help_version": "현재 버전 {version}",
        "title": "Claw Code 데스크톱 콘솔",
        "subtitle": "Solarized Light 기반 데스크톱 UI로 모델 설정, 명령 라우팅, 프로세스 감독, 안전한 정리를 통합합니다. 릴리스 {version}.",
        "summary_model": "현재 모델",
        "summary_endpoint": "엔드포인트",
        "summary_tool_mode": "도구 적응",
        "sidebar_title": "실행 개요",
        "runtime_panel": "상태 및 실행",
        "status_label": "시스템 상태",
        "process_count_label": "관리 중인 프로세스",
        "autopilot": "위험한 자동 실행 활성화",
        "config_panel": "모델 및 API 설정",
        "config_model": "모델 이름",
        "config_base_url": "기본 URL",
        "config_api_key": "API 키",
        "config_tool_style": "도구 적응",
        "config_save": "저장 후 즉시 적용",
        "quick_panel": "빠른 명령",
        "quick_status": "상태",
        "quick_doctor": "진단",
        "quick_sandbox": "샌드박스",
        "quick_version": "버전",
        "quick_agents": "에이전트",
        "quick_mcp": "MCP",
        "quick_skills": "스킬",
        "quick_help": "도움말",
        "process_list": "프로세스 목록",
        "execution_log": "실행 로그",
        "footer_clear": "대화 지우기",
        "footer_reload": "설정 새로고침",
        "welcome_title": "런처",
        "welcome_message": "데스크톱 UI가 시작되었습니다. 오른쪽에서 모델, 엔드포인트, API 키, 언어, 도구 적응 방식을 바로 설정할 수 있습니다. 왼쪽 대화 영역에는 현재 모델 요약이 계속 표시됩니다.",
        "adapter_title": "어댑터 메모",
        "adapter_message": "Gemma 계열 모델은 기본적으로 자동 적응을 사용합니다. 백엔드가 기본 tools에 불안정하면 CLI가 Gemma JSON 프롬프트 어댑터로 전환합니다.",
        "status_ready": "준비 완료",
        "status_loaded": "설정을 불러왔습니다",
        "status_saved": "모델 설정이 업데이트되었습니다",
        "status_running": "명령 실행 중",
        "status_denied": "요청이 거부되었습니다",
        "status_cleared": "대화 영역을 비웠습니다",
        "status_update_running": "업데이트 작업 실행 중",
        "status_update_done": "업데이트 완료, 재시작 대기",
        "status_update_failed": "업데이트 실패",
        "status_shutdown": "관리 중인 프로세스 정리 중",
        "busy_count": "{count}개 실행 중",
        "idle_process": "유휴",
        "user_request_title": "사용자 요청",
        "pending_title": "모델 처리 중",
        "pending_body": "응답 생성 중...\n대기 시간 {seconds:.1f}초",
        "reply_title": "모델 응답",
        "stderr_title": "표준 오류",
        "validation_title": "데스크톱 검증",
        "permission_mode_title": "권한 모드",
        "cli_title": "CLI",
        "no_output": "명령은 완료되었지만 출력이 없습니다.",
        "tool_help_title": "도구 호출 적응",
        "tool_help_message": "자동 적응은 OpenAI 호환 백엔드의 Gemma 모델에 대해 Gemma JSON 프롬프트 어댑터를 우선 사용합니다. 다른 모델은 기본 tools를 유지합니다.\n\n기본 도구 프로토콜은 provider-native tool_calls를 사용합니다.\n\nGemma JSON 프롬프트 어댑터는 도구 정의를 프롬프트에 주입하고 모델이 JSON을 반환하도록 한 뒤 CLI가 이를 해석해 도구를 실행합니다.",
        "version_info_title": "버전 정보",
        "version_info_message": "Claw Code Ubuntu Desktop UI\n현재 버전: {version}\n업데이트 채널: npm / GitHub Release",
        "update_confirm_title": "데스크톱 구성요소 업데이트",
        "update_confirm_message": "npm 최신 릴리스를 설치하고 현재 claw-code 루트에 데스크톱 구성요소를 다시 배포합니다.\n\n업데이트 후 창을 다시 시작하는 것이 좋습니다. 계속하시겠습니까?",
        "update_task_title": "업데이트 작업",
        "update_task_body": "최신 공개 패키지를 확인하고 현재 데스크톱 구성요소를 다시 배포하고 있습니다.",
        "update_success_title": "업데이트 완료",
        "update_success_body": "{details}\n\n최신 버전을 불러오려면 데스크톱 창을 닫았다가 다시 여십시오.",
        "update_error_title": "업데이트 실패",
        "update_error_body": "업데이트가 실패했고 상세 정보가 없습니다.",
        "update_missing_npm": "npm을 찾을 수 없습니다. 자동 업데이트를 계속할 수 없습니다.",
        "update_prompt_title": "업데이트 가능",
        "update_prompt_body": "새 데스크톱 패키지가 उपलब्ध합니다.\n\n현재 버전: {current}\n최신 버전: {latest}\n\n지금 업데이트하시겠습니까?",
        "language_changed_title": "언어",
        "language_changed_body": "{language}(으)로 전환했습니다.",
        "config_error_title": "설정 오류",
        "config_error_model": "모델 이름은 비워 둘 수 없습니다.",
        "config_error_base_url": "기본 URL은 http:// 또는 https:// 로 시작해야 합니다.",
        "config_error_tool_style": "도구 적응은 auto, native, gemma-json 중 하나여야 합니다.",
        "settings_saved_message": "모델 설정이 저장되었습니다.\n모델: {model}\n엔드포인트: {base_url}\n도구 적응: {tool_style}\n언어: {language}",
        "settings_saved_title": "설정 적용됨",
        "cleanup_error_title": "정리 오류",
        "cleanup_error_body": "프로세스 정리 중 오류가 발생했습니다:\n{error}\n\n그래도 종료하시겠습니까?",
    },
    "zh": {
        "window_title": "Claw Code 桌面控制台",
        "menu_session": "会话",
        "menu_model": "模型与接口",
        "menu_run": "运行",
        "menu_view": "视图",
        "menu_language": "语言",
        "menu_help": "帮助",
        "clear_chat": "清空对话",
        "exit_system": "退出系统",
        "save_apply_model": "保存并应用模型配置",
        "reload_settings": "重新载入当前配置",
        "tool_style_auto": "切换为自动工具适配",
        "tool_style_native": "切换为原生工具协议",
        "tool_style_gemma": "切换为 Gemma JSON 适配",
        "run_status": "运行状态",
        "run_doctor": "环境体检",
        "run_sandbox": "沙箱状态",
        "run_version": "版本信息",
        "run_agents": "智能体清单",
        "run_mcp": "MCP 清单",
        "run_skills": "技能清单",
        "view_processes": "刷新进程视图",
        "view_logs": "刷新执行日志",
        "help_commands": "命令帮助",
        "help_update": "更新桌面组件",
        "help_tooling": "关于工具调用适配",
        "help_version": "当前版本 {version}",
        "title": "Claw Code 桌面控制台",
        "subtitle": "Solarized Light 中文界面，统一承载模型配置、命令面板、进程托管与安全清理。当前发布版 {version}。",
        "summary_model": "当前模型",
        "summary_endpoint": "接口地址",
        "summary_tool_mode": "工具适配",
        "sidebar_title": "运行概览",
        "runtime_panel": "状态与执行",
        "status_label": "系统状态",
        "process_count_label": "托管进程",
        "autopilot": "启用高权限自动执行（danger-full-access）",
        "config_panel": "模型与接口配置",
        "config_model": "模型名称",
        "config_base_url": "接口基址",
        "config_api_key": "API 密钥",
        "config_tool_style": "工具适配",
        "config_save": "保存并立即应用",
        "quick_panel": "快捷命令",
        "quick_status": "状态",
        "quick_doctor": "体检",
        "quick_sandbox": "沙箱",
        "quick_version": "版本",
        "quick_agents": "智能体",
        "quick_mcp": "MCP",
        "quick_skills": "技能",
        "quick_help": "帮助",
        "process_list": "进程列表",
        "execution_log": "执行日志",
        "footer_clear": "清空对话",
        "footer_reload": "刷新配置",
        "welcome_title": "启动器",
        "welcome_message": "桌面界面已启动。右侧可直接配置模型、接口地址、API 密钥、语言和工具适配方式，左侧对话区会持续显示当前模型摘要。",
        "adapter_title": "模型适配说明",
        "adapter_message": "Gemma 类模型默认走“自动适配”，当后端不稳定支持原生 tools 时，CLI 会切到 Gemma JSON 提示适配层。",
        "status_ready": "就绪",
        "status_loaded": "配置已载入",
        "status_saved": "模型配置已更新",
        "status_running": "命令执行中",
        "status_denied": "请求被拒绝",
        "status_cleared": "对话区已清空",
        "status_update_running": "更新任务执行中",
        "status_update_done": "更新完成，等待重启",
        "status_update_failed": "更新失败",
        "status_shutdown": "正在停止托管进程",
        "busy_count": "{count} 个运行中",
        "idle_process": "空闲",
        "user_request_title": "用户请求",
        "pending_title": "模型处理中",
        "pending_body": "正在生成回复…\n已等待 {seconds:.1f} 秒",
        "reply_title": "模型回复",
        "stderr_title": "标准错误",
        "validation_title": "桌面校验",
        "permission_mode_title": "权限模式",
        "cli_title": "CLI",
        "no_output": "命令已完成，但没有输出内容。",
        "tool_help_title": "工具调用适配说明",
        "tool_help_message": "自动适配：Gemma + OpenAI 兼容后端时，优先启用 Gemma JSON 提示适配；其他模型保留原生 tools。\n\n原生工具协议：直接使用 provider-native tools/tool_calls。\n\nGemma JSON 提示适配：把工具定义注入系统提示词，要求模型返回 JSON 对象，再由 CLI 回解析并执行工具。",
        "version_info_title": "版本信息",
        "version_info_message": "Claw Code Ubuntu Desktop UI\n当前版本：{version}\n更新通道：npm / GitHub Release",
        "update_confirm_title": "更新桌面组件",
        "update_confirm_message": "将通过 npm 安装最新发布版，并把桌面组件重新部署到当前 claw-code 根目录。\n\n更新完成后建议重启桌面窗口。是否继续？",
        "update_task_title": "更新任务",
        "update_task_body": "已开始检查最新发布包，并重新部署当前桌面组件。",
        "update_success_title": "更新完成",
        "update_success_body": "{details}\n\n请关闭并重新打开桌面窗口，以加载最新版本。",
        "update_error_title": "更新失败",
        "update_error_body": "更新失败，未返回详细信息。",
        "update_missing_npm": "未找到 npm，无法执行自动更新。",
        "update_prompt_title": "发现更新",
        "update_prompt_body": "检测到新的桌面安装包。\n\n当前版本：{current}\n最新版本：{latest}\n\n是否现在更新？",
        "language_changed_title": "语言",
        "language_changed_body": "界面语言已切换为 {language}。",
        "config_error_title": "配置错误",
        "config_error_model": "模型名称不能为空。",
        "config_error_base_url": "接口基址必须以 http:// 或 https:// 开头。",
        "config_error_tool_style": "工具适配模式只能是 auto、native 或 gemma-json。",
        "settings_saved_message": "模型配置已保存。\n模型：{model}\n接口：{base_url}\n工具适配：{tool_style}\n语言：{language}",
        "settings_saved_title": "配置已应用",
        "cleanup_error_title": "清理异常",
        "cleanup_error_body": "清理进程时发生异常：\n{error}\n\n仍要关闭吗？",
    },
}


class MainWindow(tk.Tk):
    def __init__(self, project_root: Path, lifecycle: LifecycleManager):
        super().__init__()
        self.project_root = Path(project_root)
        self.lifecycle = lifecycle
        self.settings_store = DesktopSettingsStore()
        self.bridge = ClawBridge(self.project_root, lifecycle, self.settings_store)
        self.results: queue.Queue[CommandResult] = queue.Queue()
        self.message_log: list[dict[str, object]] = []
        self.pending_messages: dict[str, list[dict[str, object]]] = {}
        self.latest_known_version: str | None = None
        self._update_prompted = False

        current_settings = self.settings_store.load()
        self.current_locale = self._normalize_locale(current_settings.locale)

        self.status_var = tk.StringVar(value=self._t("status_ready"))
        self.active_var = tk.StringVar(value=self._t("busy_count", count=0))
        self.model_summary_var = tk.StringVar()
        self.endpoint_var = tk.StringVar()
        self.tool_mode_var = tk.StringVar()
        self.autopilot_var = tk.BooleanVar(value=False)
        self.model_entry_var = tk.StringVar()
        self.base_url_entry_var = tk.StringVar()
        self.api_key_entry_var = tk.StringVar()
        self.tool_style_entry_var = tk.StringVar()

        self.geometry("1520x980")
        self.minsize(520, 360)
        self.configure(background=PALETTE["base3"])
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_style()
        self._rebuild_ui(preserve_chat=False)
        self.after(120, self._drain_results)
        self.after(800, self._refresh_process_list)
        self.after(1500, self._start_update_probe)

    def _normalize_locale(self, locale: str | None) -> str:
        value = (locale or "en").strip().lower()
        return value if value in SUPPORTED_LOCALES else "en"

    def _t(self, key: str, **kwargs: object) -> str:
        template = I18N[self.current_locale].get(key, I18N["en"].get(key, key))
        return template.format(**kwargs)

    def _version_tuple(self, value: str) -> tuple[int, ...]:
        normalized = value.strip().lstrip("v")
        parts: list[int] = []
        for item in normalized.split("."):
            try:
                parts.append(int(item))
            except ValueError:
                parts.append(0)
        return tuple(parts)

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

    def _rebuild_ui(self, preserve_chat: bool) -> None:
        saved_messages = [
            {"text": str(row["text"]), "role": str(row["role"]), "title": row.get("title")}
            for row in self.message_log
        ] if preserve_chat else []
        for child in self.winfo_children():
            child.destroy()
        self.pending_messages.clear()
        self.message_log.clear()

        self.title(self._t("window_title"))
        self._build_menu()
        self._build_layout()
        self._load_settings_into_form()
        if saved_messages:
            for row in saved_messages:
                self._chat_add(row["text"], row["role"], row["title"])
        else:
            self._seed_welcome()

    def _build_menu(self) -> None:
        menu_font = ("Noto Sans CJK SC", 8)
        menubar = tk.Menu(self, tearoff=False, background=PALETTE["base2"], foreground=PALETTE["base01"], font=menu_font)

        session_menu = tk.Menu(menubar, tearoff=False, background=PALETTE["base2"], foreground=PALETTE["base01"], font=menu_font)
        session_menu.add_command(label=self._t("clear_chat"), command=self._clear_chat)
        session_menu.add_separator()
        session_menu.add_command(label=self._t("exit_system"), command=self._on_close)
        menubar.add_cascade(label=self._t("menu_session"), menu=session_menu)

        model_menu = tk.Menu(menubar, tearoff=False, background=PALETTE["base2"], foreground=PALETTE["base01"], font=menu_font)
        model_menu.add_command(label=self._t("save_apply_model"), command=self._save_settings)
        model_menu.add_command(label=self._t("reload_settings"), command=self._load_settings_into_form)
        model_menu.add_separator()
        model_menu.add_command(label=self._t("tool_style_auto"), command=lambda: self._set_tool_style("auto"))
        model_menu.add_command(label=self._t("tool_style_native"), command=lambda: self._set_tool_style("native"))
        model_menu.add_command(label=self._t("tool_style_gemma"), command=lambda: self._set_tool_style("gemma-json"))
        menubar.add_cascade(label=self._t("menu_model"), menu=model_menu)

        run_menu = tk.Menu(menubar, tearoff=False, background=PALETTE["base2"], foreground=PALETTE["base01"], font=menu_font)
        run_menu.add_command(label=self._t("run_status"), command=lambda: self._submit_request("/status"))
        run_menu.add_command(label=self._t("run_doctor"), command=lambda: self._submit_request("/doctor"))
        run_menu.add_command(label=self._t("run_sandbox"), command=lambda: self._submit_request("/sandbox"))
        run_menu.add_command(label=self._t("run_version"), command=lambda: self._submit_request("/version"))
        run_menu.add_command(label=self._t("run_agents"), command=lambda: self._submit_request("/agents"))
        run_menu.add_command(label=self._t("run_mcp"), command=lambda: self._submit_request("/mcp"))
        run_menu.add_command(label=self._t("run_skills"), command=lambda: self._submit_request("/skills"))
        menubar.add_cascade(label=self._t("menu_run"), menu=run_menu)

        view_menu = tk.Menu(menubar, tearoff=False, background=PALETTE["base2"], foreground=PALETTE["base01"], font=menu_font)
        view_menu.add_command(label=self._t("view_processes"), command=self._refresh_process_list)
        view_menu.add_command(label=self._t("view_logs"), command=self._refresh_log)
        menubar.add_cascade(label=self._t("menu_view"), menu=view_menu)

        language_menu = tk.Menu(menubar, tearoff=False, background=PALETTE["base2"], foreground=PALETTE["base01"], font=menu_font)
        for locale in SUPPORTED_LOCALES:
            language_menu.add_command(
                label=LANGUAGE_LABELS[locale],
                command=lambda value=locale: self._set_locale(value),
            )
        menubar.add_cascade(label=self._t("menu_language"), menu=language_menu)

        help_menu = tk.Menu(menubar, tearoff=False, background=PALETTE["base2"], foreground=PALETTE["base01"], font=menu_font)
        help_menu.add_command(label=self._t("help_commands"), command=lambda: self._submit_request("/help"))
        help_menu.add_command(label=self._t("help_update"), command=self._run_update)
        help_menu.add_command(label=self._t("help_tooling"), command=self._show_tool_help)
        help_menu.add_separator()
        help_menu.add_command(label=self._t("help_version", version=APP_VERSION), command=self._show_version_info)
        menubar.add_cascade(label=self._t("menu_help"), menu=help_menu)
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
            text=self._t("title"),
            background=PALETTE["base3"],
            foreground=PALETTE["base01"],
            font=("Noto Sans CJK SC", 20, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            masthead,
            text=self._t("subtitle", version=APP_VERSION),
            background=PALETTE["base3"],
            foreground=PALETTE["base00"],
            font=("Noto Sans CJK SC", 9),
        ).pack(anchor="w", pady=(4, 0))

        summary = tk.Frame(left, background=PALETTE["base2"], highlightthickness=1, highlightbackground=PALETTE["base1"], padx=14, pady=12)
        summary.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        summary.grid_columnconfigure(1, weight=1)
        self._summary_row(summary, 0, self._t("summary_model"), self.model_summary_var)
        self._summary_row(summary, 1, self._t("summary_endpoint"), self.endpoint_var)
        self._summary_row(summary, 2, self._t("summary_tool_mode"), self.tool_mode_var)

        self.chat = ChatWidget(left)
        self.chat.grid(row=2, column=0, sticky="nsew")
        self.chat.set_submit_callback(self._submit_request)
        self.chat.set_locale(self._send_label())

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
        sidebar_scrollbar = ttk.Scrollbar(sidebar_shell, orient="vertical", command=self.sidebar_canvas.yview)
        sidebar_scrollbar.grid(row=0, column=1, sticky="ns")
        self.sidebar_canvas.configure(yscrollcommand=sidebar_scrollbar.set)

        sidebar = ttk.Frame(self.sidebar_canvas, style="Sidebar.TFrame", padding=18)
        sidebar.columnconfigure(0, weight=1)
        sidebar.rowconfigure(5, weight=1)
        self.sidebar_window = self.sidebar_canvas.create_window((0, 0), window=sidebar, anchor="nw")
        sidebar.bind("<Configure>", self._on_sidebar_configure)
        self.sidebar_canvas.bind("<Configure>", self._on_sidebar_canvas_configure)
        self.sidebar_canvas.bind_all("<MouseWheel>", self._on_mousewheel, add="+")

        ttk.Label(sidebar, text=self._t("sidebar_title"), style="SidebarTitle.TLabel").grid(row=0, column=0, sticky="w")

        runtime_panel = ttk.LabelFrame(sidebar, text=self._t("runtime_panel"), style="Panel.TLabelframe", padding=12)
        runtime_panel.grid(row=1, column=0, sticky="ew", pady=(12, 10))
        runtime_panel.columnconfigure(0, weight=1)
        ttk.Label(runtime_panel, text=self._t("status_label"), style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(runtime_panel, textvariable=self.status_var, style="Value.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 8))
        ttk.Label(runtime_panel, text=self._t("process_count_label"), style="Muted.TLabel").grid(row=2, column=0, sticky="w")
        ttk.Label(runtime_panel, textvariable=self.active_var, style="Value.TLabel").grid(row=3, column=0, sticky="w")
        ttk.Checkbutton(
            runtime_panel,
            text=self._t("autopilot"),
            variable=self.autopilot_var,
            command=self._toggle_autopilot,
        ).grid(row=4, column=0, sticky="w", pady=(10, 0))

        config_panel = ttk.LabelFrame(sidebar, text=self._t("config_panel"), style="Panel.TLabelframe", padding=12)
        config_panel.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        config_panel.columnconfigure(1, weight=1)
        self._config_row(config_panel, 0, self._t("config_model"), self.model_entry_var)
        self._config_row(config_panel, 1, self._t("config_base_url"), self.base_url_entry_var)
        self._config_row(config_panel, 2, self._t("config_api_key"), self.api_key_entry_var, show="*")
        ttk.Label(config_panel, text=self._t("config_tool_style"), style="Muted.TLabel").grid(row=3, column=0, sticky="w", pady=(8, 0))
        tool_style = ttk.Combobox(config_panel, textvariable=self.tool_style_entry_var, state="readonly", values=["auto", "native", "gemma-json"])
        tool_style.grid(row=3, column=1, sticky="ew", pady=(8, 0))
        ttk.Button(config_panel, text=self._t("config_save"), command=self._save_settings, style="Accent.TButton").grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        quick_panel = ttk.LabelFrame(sidebar, text=self._t("quick_panel"), style="Panel.TLabelframe", padding=12)
        quick_panel.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        quick_panel.columnconfigure((0, 1), weight=1)
        buttons = [
            (self._t("quick_status"), "/status"),
            (self._t("quick_doctor"), "/doctor"),
            (self._t("quick_sandbox"), "/sandbox"),
            (self._t("quick_version"), "/version"),
            (self._t("quick_agents"), "/agents"),
            (self._t("quick_mcp"), "/mcp"),
            (self._t("quick_skills"), "/skills"),
            (self._t("quick_help"), "/help"),
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

        ttk.Label(lists_panel, text=self._t("process_list"), style="Muted.TLabel").grid(row=0, column=0, sticky="w")
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

        ttk.Label(lists_panel, text=self._t("execution_log"), style="Muted.TLabel").grid(row=2, column=0, sticky="w")
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
        ttk.Button(footer, text=self._t("footer_clear"), command=self._clear_chat).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(footer, text=self._t("footer_reload"), command=self._load_settings_into_form).grid(row=0, column=1, sticky="ew")

    def _send_label(self) -> str:
        return {
            "en": "Send",
            "ja": "送信",
            "ko": "보내기",
            "zh": "发送",
        }.get(self.current_locale, "Send")

    def _summary_row(self, parent: tk.Misc, row: int, label: str, variable: tk.StringVar) -> None:
        tk.Label(parent, text=label, background=PALETTE["base2"], foreground=PALETTE["base00"], font=("Noto Sans CJK SC", 8), anchor="w").grid(row=row, column=0, sticky="w", padx=(0, 12), pady=3)
        tk.Label(parent, textvariable=variable, background=PALETTE["base2"], foreground=PALETTE["base01"], font=("Noto Sans CJK SC", 8, "bold"), anchor="w").grid(row=row, column=1, sticky="w", pady=3)

    def _config_row(self, parent: tk.Misc, row: int, label: str, variable: tk.StringVar, show: str | None = None) -> None:
        ttk.Label(parent, text=label, style="Muted.TLabel").grid(row=row, column=0, sticky="w", pady=(8 if row else 0, 0))
        entry = ttk.Entry(parent, textvariable=variable, show=show or "")
        entry.grid(row=row, column=1, sticky="ew", pady=(8 if row else 0, 0))

    def _chat_add(self, text: str, role: str, title: str | None = None) -> int:
        message_id = self.chat.add_message(text, role=role, title=title)
        self.message_log.append({"message_id": message_id, "text": text, "role": role, "title": title})
        return message_id

    def _chat_update(self, message_id: int, text: str, title: str | None = None) -> None:
        self.chat.update_message(message_id, text, title=title)
        for row in self.message_log:
            if row.get("message_id") == message_id:
                row["text"] = text
                if title is not None:
                    row["title"] = title
                break

    def _chat_remove(self, message_id: int) -> None:
        self.chat.remove_message(message_id)
        self.message_log = [row for row in self.message_log if row.get("message_id") != message_id]

    def _seed_welcome(self) -> None:
        self._chat_add(self._t("welcome_message"), role="system", title=self._t("welcome_title"))
        self._chat_add(self._t("adapter_message"), role="assistant", title=self._t("adapter_title"))

    def _load_settings_into_form(self) -> None:
        settings = self.settings_store.load()
        self.current_locale = self._normalize_locale(settings.locale)
        self.model_entry_var.set(settings.model)
        self.base_url_entry_var.set(settings.base_url)
        self.api_key_entry_var.set(settings.api_key)
        self.tool_style_entry_var.set(settings.tool_call_style)
        self._refresh_model_summary(settings)
        self.active_var.set(self._t("busy_count", count=self.bridge.active_process_count()))
        self.status_var.set(self._t("status_loaded"))

    def _refresh_model_summary(self, settings: DesktopSettings | None = None) -> None:
        current = settings or self.settings_store.load()
        locale = self._normalize_locale(current.locale)
        self.model_summary_var.set(f"{current.model} · {current.provider_label(locale)}")
        self.endpoint_var.set(current.base_url)
        self.tool_mode_var.set(current.tool_style_label(locale))

    def _current_form_settings(self) -> DesktopSettings:
        stored = self.settings_store.load()
        return DesktopSettings(
            model=self.model_entry_var.get().strip() or stored.model,
            base_url=self.base_url_entry_var.get().strip() or stored.base_url,
            api_key=self.api_key_entry_var.get().strip() or stored.api_key,
            tool_call_style=self.tool_style_entry_var.get().strip() or stored.tool_call_style,
            locale=self.current_locale,
        )

    def _save_settings(self) -> None:
        model = self.model_entry_var.get().strip()
        base_url = self.base_url_entry_var.get().strip()
        api_key = self.api_key_entry_var.get().strip()
        tool_style = self.tool_style_entry_var.get().strip()

        if not model:
            messagebox.showerror(self._t("config_error_title"), self._t("config_error_model"))
            return
        if not (base_url.startswith("http://") or base_url.startswith("https://")):
            messagebox.showerror(self._t("config_error_title"), self._t("config_error_base_url"))
            return
        if tool_style not in {"auto", "native", "gemma-json"}:
            messagebox.showerror(self._t("config_error_title"), self._t("config_error_tool_style"))
            return

        settings = DesktopSettings(
            model=model,
            base_url=base_url,
            api_key=api_key,
            tool_call_style=tool_style,
            locale=self.current_locale,
        )
        self.settings_store.save(settings)
        self._refresh_model_summary(settings)
        self._chat_add(
            self._t(
                "settings_saved_message",
                model=settings.model,
                base_url=settings.base_url,
                tool_style=settings.tool_style_label(self.current_locale),
                language=LANGUAGE_LABELS[self.current_locale],
            ),
            role="system",
            title=self._t("settings_saved_title"),
        )
        self.status_var.set(self._t("status_saved"))

    def _set_tool_style(self, style: str) -> None:
        self.tool_style_entry_var.set(style)
        self._save_settings()

    def _set_locale(self, locale: str) -> None:
        normalized = self._normalize_locale(locale)
        if normalized == self.current_locale:
            return
        settings = self._current_form_settings()
        settings.locale = normalized
        self.current_locale = normalized
        self.settings_store.save(settings)
        self._rebuild_ui(preserve_chat=True)
        self._chat_add(
            self._t("language_changed_body", language=LANGUAGE_LABELS[normalized]),
            role="system",
            title=self._t("language_changed_title"),
        )

    def _show_tool_help(self) -> None:
        messagebox.showinfo(self._t("tool_help_title"), self._t("tool_help_message"))

    def _show_version_info(self) -> None:
        messagebox.showinfo(
            self._t("version_info_title"),
            self._t("version_info_message", version=APP_VERSION),
        )

    def _run_update(self) -> None:
        if not messagebox.askyesno(self._t("update_confirm_title"), self._t("update_confirm_message")):
            return
        self._chat_add(self._t("update_task_body"), role="system", title=self._t("update_task_title"))
        self.status_var.set(self._t("status_update_running"))
        threading.Thread(target=self._run_update_job, daemon=True).start()

    def _run_update_job(self) -> None:
        started_at = time.time()
        npm_bin = shutil.which("npm")
        if npm_bin is None:
            self.results.put(
                CommandResult(
                    request_text="__ui_update__",
                    argv=["npm"],
                    exit_code=127,
                    stdout="",
                    stderr=self._t("update_missing_npm"),
                    started_at=started_at,
                    finished_at=time.time(),
                )
            )
            return

        try:
            install_proc = subprocess.run(
                [npm_bin, "install", "-g", f"{NPM_PACKAGE_NAME}@latest"],
                cwd=self.project_root.parent,
                text=True,
                capture_output=True,
                check=False,
            )
            stdout_parts = [install_proc.stdout.strip()] if install_proc.stdout.strip() else []
            stderr_parts = [install_proc.stderr.strip()] if install_proc.stderr.strip() else []
            if install_proc.returncode != 0:
                self.results.put(
                    CommandResult(
                        request_text="__ui_update__",
                        argv=list(install_proc.args),
                        exit_code=install_proc.returncode,
                        stdout="\n\n".join(stdout_parts),
                        stderr="\n\n".join(stderr_parts),
                        started_at=started_at,
                        finished_at=time.time(),
                    )
                )
                return

            prefix_proc = subprocess.run(
                [npm_bin, "prefix", "-g"],
                cwd=self.project_root.parent,
                text=True,
                capture_output=True,
                check=False,
            )
            if prefix_proc.returncode != 0:
                self.results.put(
                    CommandResult(
                        request_text="__ui_update__",
                        argv=list(prefix_proc.args),
                        exit_code=prefix_proc.returncode,
                        stdout="\n\n".join(filter(None, stdout_parts)),
                        stderr=prefix_proc.stderr.strip() or self._t("update_error_body"),
                        started_at=started_at,
                        finished_at=time.time(),
                    )
                )
                return

            installer_path = Path(prefix_proc.stdout.strip()) / "bin" / "claw-code-ubuntu-desktopui-install"
            update_proc = subprocess.run(
                [str(installer_path), "--yes", "--target", str(self.project_root.parent)],
                cwd=self.project_root.parent,
                text=True,
                capture_output=True,
                check=False,
            )
            if update_proc.stdout.strip():
                stdout_parts.append(update_proc.stdout.strip())
            if update_proc.stderr.strip():
                stderr_parts.append(update_proc.stderr.strip())
            self.results.put(
                CommandResult(
                    request_text="__ui_update__",
                    argv=list(update_proc.args),
                    exit_code=update_proc.returncode,
                    stdout="\n\n".join(filter(None, stdout_parts)),
                    stderr="\n\n".join(filter(None, stderr_parts)),
                    started_at=started_at,
                    finished_at=time.time(),
                )
            )
        except Exception as exc:
            self.results.put(
                CommandResult(
                    request_text="__ui_update__",
                    argv=[NPM_PACKAGE_NAME],
                    exit_code=1,
                    stdout="",
                    stderr=str(exc),
                    started_at=started_at,
                    finished_at=time.time(),
                )
            )

    def _start_update_probe(self) -> None:
        threading.Thread(target=self._run_update_probe_job, daemon=True).start()

    def _run_update_probe_job(self) -> None:
        npm_bin = shutil.which("npm")
        if npm_bin is None:
            return
        started_at = time.time()
        try:
            probe = subprocess.run(
                [npm_bin, "view", NPM_PACKAGE_NAME, "version"],
                cwd=self.project_root.parent,
                text=True,
                capture_output=True,
                check=False,
            )
            if probe.returncode != 0:
                return
            latest = probe.stdout.strip()
            if not latest or self._version_tuple(latest) <= self._version_tuple(APP_VERSION_NPM):
                return
            self.results.put(
                CommandResult(
                    request_text="__update_probe__",
                    argv=list(probe.args),
                    exit_code=0,
                    stdout=latest,
                    stderr="",
                    started_at=started_at,
                    finished_at=time.time(),
                )
            )
        except Exception:
            return

    def _submit_request(self, text: str) -> None:
        request = text.strip()
        if not request:
            return
        if request in {"/clear", "/清空"}:
            self._clear_chat()
            return
        self._chat_add(request, role="user", title=self._t("user_request_title"))
        self.status_var.set(self._t("status_running"))
        try:
            pending_id = self._chat_add(
                self._t("pending_body", seconds=0.0),
                role="assistant",
                title=self._t("pending_title"),
            )
            self.pending_messages.setdefault(request, []).append(
                {"message_id": pending_id, "started_at": time.time()}
            )
            self._tick_pending_message(request)
            self.bridge.submit(request, self.results.put)
            self._refresh_log()
            self._refresh_process_list()
        except Exception as exc:
            self._clear_pending_message(request)
            self._chat_add(str(exc), role="error", title=self._t("validation_title"))
            self.status_var.set(self._t("status_denied"))

    def _toggle_autopilot(self) -> None:
        state = self.bridge.set_autopilot(self.autopilot_var.get())
        self.status_var.set(state)
        self._chat_add(state, role="system", title=self._t("permission_mode_title"))

    def _clear_chat(self) -> None:
        self.chat.clear()
        self.message_log.clear()
        self._seed_welcome()
        self.status_var.set(self._t("status_cleared"))

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
        if result.request_text == "__ui_update__":
            self._handle_update_result(result)
            return
        if result.request_text == "__update_probe__":
            self._handle_update_probe(result)
            return

        summary = f"exit {result.exit_code} · {result.duration_seconds:.2f}s"
        if self.current_locale == "ja":
            summary = f"終了コード {result.exit_code} · {result.duration_seconds:.2f}s"
        elif self.current_locale == "ko":
            summary = f"종료 코드 {result.exit_code} · {result.duration_seconds:.2f}s"
        elif self.current_locale == "zh":
            summary = f"退出码 {result.exit_code} · {result.duration_seconds:.2f}s"
        self.status_var.set(summary)

        pending_queue = self.pending_messages.get(result.request_text, [])
        pending = pending_queue.pop(0) if pending_queue else None
        if not pending_queue and result.request_text in self.pending_messages:
            self.pending_messages.pop(result.request_text, None)

        if result.stdout:
            payload = self._render_stdout(result)
            if pending and payload:
                self._chat_update(int(pending["message_id"]), payload, title=self._t("reply_title"))
            elif payload:
                self._chat_add(payload, role="assistant", title=self._t("reply_title"))
            elif pending:
                self._chat_remove(int(pending["message_id"]))
        if result.stderr:
            self._chat_add(result.stderr, role="error", title=self._t("stderr_title"))
        if not result.stdout and not result.stderr:
            if pending:
                self._chat_update(int(pending["message_id"]), self._t("no_output"), title=self._t("cli_title"))
            else:
                self._chat_add(self._t("no_output"), role="tool", title=self._t("cli_title"))

        self._refresh_log()
        self._refresh_process_list()

    def _render_stdout(self, result: CommandResult) -> str:
        if isinstance(result.parsed_stdout, dict):
            message = result.parsed_stdout.get("message")
            if isinstance(message, str):
                return message.strip()
        return result.stdout

    def _handle_update_result(self, result: CommandResult) -> None:
        if result.exit_code == 0:
            details = result.stdout or self._t("update_success_title")
            self._chat_add(
                self._t("update_success_body", details=details),
                role="system",
                title=self._t("update_success_title"),
            )
            self.status_var.set(self._t("status_update_done"))
            return
        self._chat_add(
            result.stderr or result.stdout or self._t("update_error_body"),
            role="error",
            title=self._t("update_error_title"),
        )
        self.status_var.set(self._t("status_update_failed"))

    def _handle_update_probe(self, result: CommandResult) -> None:
        latest = result.stdout.strip()
        if not latest or self._update_prompted:
            return
        self._update_prompted = True
        self.latest_known_version = latest
        if messagebox.askyesno(
            self._t("update_prompt_title"),
            self._t("update_prompt_body", current=APP_VERSION, latest=latest),
        ):
            self._run_update()

    def _tick_pending_message(self, request: str) -> None:
        pending_queue = self.pending_messages.get(request)
        if not pending_queue:
            return
        pending = pending_queue[0]
        elapsed = max(time.time() - float(pending["started_at"]), 0.0)
        self._chat_update(
            int(pending["message_id"]),
            self._t("pending_body", seconds=elapsed),
            title=self._t("pending_title"),
        )
        self.after(400, lambda: self._tick_pending_message(request))

    def _clear_pending_message(self, request: str) -> None:
        pending_queue = self.pending_messages.get(request, [])
        pending = pending_queue.pop() if pending_queue else None
        if not pending_queue and request in self.pending_messages:
            self.pending_messages.pop(request, None)
        if pending is None:
            return
        self._chat_remove(int(pending["message_id"]))

    def _refresh_log(self) -> None:
        self.log_list.delete(0, "end")
        for row in self.bridge.history[-100:]:
            self.log_list.insert("end", row)
        if self.log_list.size():
            self.log_list.yview_moveto(1.0)

    def _refresh_process_list(self) -> None:
        rows = self.bridge.active_process_rows()
        self.process_list.delete(0, "end")
        for row in rows or [self._t("idle_process")]:
            self.process_list.insert("end", row)
        self.active_var.set(self._t("busy_count", count=self.bridge.active_process_count()))
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
            self.status_var.set(self._t("status_shutdown"))
            self.bridge.shutdown()
            self.lifecycle.shutdown()
        except Exception as exc:
            if not messagebox.askyesno(
                self._t("cleanup_error_title"),
                self._t("cleanup_error_body", error=str(exc)),
            ):
                return
        self.destroy()
