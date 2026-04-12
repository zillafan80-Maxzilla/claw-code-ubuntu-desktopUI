from __future__ import annotations

import queue
import shutil
import subprocess
import threading
import tkinter as tk
import time
from pathlib import Path
from tkinter import messagebox, ttk

from core.bridge import BridgeEvent, ClawBridge, CommandResult
from core.lifecycle import LifecycleManager
from core.session_store import DesktopSession, DesktopSessionStore, SessionMessage, SessionSummary
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

APP_VERSION = "2.0"
APP_VERSION_NPM = "2.0.0"
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
        "session_new": "New Session",
        "session_save": "Save Session Now",
        "session_open": "Open Selected Session",
        "session_compact": "Compact Selected Session",
        "session_delete": "Delete Selected Session",
        "session_refresh": "Refresh Session List",
        "session_panel": "Session History",
        "session_current": "Current Session",
        "session_none": "No saved sessions yet",
        "session_saved": "Session saved",
        "session_loaded": "Session loaded",
        "session_deleted": "Session deleted",
        "session_compacted": "Session compacted",
        "session_save_failed": "Session save failed",
        "session_load_failed": "Unable to load the selected session.",
        "session_delete_confirm_title": "Delete Session",
        "session_delete_confirm_body": "Delete the selected saved session file?\n\n{path}",
        "session_compact_failed": "Session compaction failed",
        "title": "Claw Code Desktop Console",
        "subtitle": "Solarized Light desktop shell for model setup, command routing, process supervision, and safe cleanup. Release {version}.",
        "summary_model": "Current Model",
        "summary_endpoint": "Endpoint",
        "summary_tool_mode": "Tool Adapter",
        "sidebar_title": "Runtime Overview",
        "runtime_panel": "Status And Execution",
        "status_label": "System Status",
        "process_count_label": "Managed Processes",
        "high_privilege": "Allow System Permissions",
        "autonomous_execution": "Enable Autonomous Execution",
        "runstate_running": "Running",
        "runstate_stopped": "Stopped",
        "runstate_ended": "Ended",
        "run_detail_title": "Run Details",
        "run_detail_exit": "Exit code: {code}\nDuration: {seconds:.2f}s",
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
        "copy_chat_done": "Copied full conversation",
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
        "pending_silent": "CLI is still running and waiting for model or tool output...",
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
        "settings_saved_message": "Model settings saved.\nModel: {model}\nEndpoint: {base_url}\nTool adapter: {tool_style}\nLanguage: {language}\nHigh privilege: {high_privilege}\nAutonomous execution: {autonomous_execution}",
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
        "session_new": "新しいセッション",
        "session_save": "今のセッションを保存",
        "session_open": "選択中のセッションを開く",
        "session_compact": "選択中のセッションを圧縮",
        "session_delete": "選択中のセッションを削除",
        "session_refresh": "セッション一覧を更新",
        "session_panel": "セッション履歴",
        "session_current": "現在のセッション",
        "session_none": "保存済みセッションはまだありません",
        "session_saved": "セッションを保存しました",
        "session_loaded": "セッションを読み込みました",
        "session_deleted": "セッションを削除しました",
        "session_compacted": "セッションを圧縮しました",
        "session_save_failed": "セッション保存に失敗しました",
        "session_load_failed": "選択中のセッションを読み込めませんでした。",
        "session_delete_confirm_title": "セッション削除",
        "session_delete_confirm_body": "選択した保存済みセッションを削除しますか？\n\n{path}",
        "session_compact_failed": "セッション圧縮に失敗しました",
        "title": "Claw Code デスクトップコンソール",
        "subtitle": "Solarized Light ベースのデスクトップ UI。モデル設定、コマンド中継、プロセス管理、安全な終了処理を統合します。リリース {version}。",
        "summary_model": "現在のモデル",
        "summary_endpoint": "エンドポイント",
        "summary_tool_mode": "ツール適応",
        "sidebar_title": "実行概要",
        "runtime_panel": "状態と実行",
        "status_label": "システム状態",
        "process_count_label": "管理中プロセス",
        "high_privilege": "システム権限を許可",
        "autonomous_execution": "自律実行を有効化",
        "runstate_running": "実行中",
        "runstate_stopped": "停止",
        "runstate_ended": "終了",
        "run_detail_title": "実行詳細",
        "run_detail_exit": "終了コード: {code}\n所要時間: {seconds:.2f}秒",
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
        "copy_chat_done": "会話全体をコピーしました",
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
        "pending_silent": "CLI は実行中です。モデルまたはツール出力を待っています...",
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
        "settings_saved_message": "モデル設定を保存しました。\nモデル: {model}\nエンドポイント: {base_url}\nツール適応: {tool_style}\n言語: {language}\n高権限: {high_privilege}\n自律実行: {autonomous_execution}",
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
        "session_new": "새 세션",
        "session_save": "현재 세션 저장",
        "session_open": "선택한 세션 열기",
        "session_compact": "선택한 세션 압축",
        "session_delete": "선택한 세션 삭제",
        "session_refresh": "세션 목록 새로고침",
        "session_panel": "세션 기록",
        "session_current": "현재 세션",
        "session_none": "저장된 세션이 아직 없습니다",
        "session_saved": "세션이 저장되었습니다",
        "session_loaded": "세션을 불러왔습니다",
        "session_deleted": "세션을 삭제했습니다",
        "session_compacted": "세션을 압축했습니다",
        "session_save_failed": "세션 저장에 실패했습니다",
        "session_load_failed": "선택한 세션을 불러오지 못했습니다.",
        "session_delete_confirm_title": "세션 삭제",
        "session_delete_confirm_body": "선택한 저장 세션 파일을 삭제하시겠습니까?\n\n{path}",
        "session_compact_failed": "세션 압축에 실패했습니다",
        "title": "Claw Code 데스크톱 콘솔",
        "subtitle": "Solarized Light 기반 데스크톱 UI로 모델 설정, 명령 라우팅, 프로세스 감독, 안전한 정리를 통합합니다. 릴리스 {version}.",
        "summary_model": "현재 모델",
        "summary_endpoint": "엔드포인트",
        "summary_tool_mode": "도구 적응",
        "sidebar_title": "실행 개요",
        "runtime_panel": "상태 및 실행",
        "status_label": "시스템 상태",
        "process_count_label": "관리 중인 프로세스",
        "high_privilege": "시스템 권한 허용",
        "autonomous_execution": "자율 실행 활성화",
        "runstate_running": "실행 중",
        "runstate_stopped": "중지",
        "runstate_ended": "종료됨",
        "run_detail_title": "실행 상세",
        "run_detail_exit": "종료 코드: {code}\n소요 시간: {seconds:.2f}초",
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
        "copy_chat_done": "전체 대화를 복사했습니다",
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
        "pending_silent": "CLI가 계속 실행 중이며 모델 또는 도구 출력을 기다리고 있습니다...",
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
        "settings_saved_message": "모델 설정이 저장되었습니다.\n모델: {model}\n엔드포인트: {base_url}\n도구 적응: {tool_style}\n언어: {language}\n고권한: {high_privilege}\n자율 실행: {autonomous_execution}",
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
        "session_new": "新建会话",
        "session_save": "立即保存当前会话",
        "session_open": "打开所选会话",
        "session_compact": "压缩所选会话",
        "session_delete": "删除所选会话",
        "session_refresh": "刷新会话列表",
        "session_panel": "历史会话",
        "session_current": "当前会话",
        "session_none": "还没有已保存会话",
        "session_saved": "会话已保存",
        "session_loaded": "会话已加载",
        "session_deleted": "会话已删除",
        "session_compacted": "会话已压缩",
        "session_save_failed": "会话保存失败",
        "session_load_failed": "无法加载所选会话。",
        "session_delete_confirm_title": "删除会话",
        "session_delete_confirm_body": "确定删除所选会话文件吗？\n\n{path}",
        "session_compact_failed": "会话压缩失败",
        "title": "Claw Code 桌面控制台",
        "subtitle": "Solarized Light 中文界面，统一承载模型配置、命令面板、进程托管与安全清理。当前发布版 {version}。",
        "summary_model": "当前模型",
        "summary_endpoint": "接口地址",
        "summary_tool_mode": "工具适配",
        "sidebar_title": "运行概览",
        "runtime_panel": "状态与执行",
        "status_label": "系统状态",
        "process_count_label": "托管进程",
        "high_privilege": "允许系统权限",
        "autonomous_execution": "启用自动执行",
        "runstate_running": "正在执行",
        "runstate_stopped": "已停止",
        "runstate_ended": "已结束",
        "run_detail_title": "执行详情",
        "run_detail_exit": "退出码：{code}\n耗时：{seconds:.2f} 秒",
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
        "copy_chat_done": "已复制整个对话",
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
        "pending_silent": "CLI 仍在运行，正在等待模型或工具输出…",
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
        "settings_saved_message": "模型配置已保存。\n模型：{model}\n接口：{base_url}\n工具适配：{tool_style}\n语言：{language}\n高权限：{high_privilege}\n自动执行：{autonomous_execution}",
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
        self.session_store = DesktopSessionStore(self.project_root)
        self.bridge = ClawBridge(self.project_root, lifecycle, self.settings_store)
        self.results: queue.Queue[CommandResult | BridgeEvent] = queue.Queue()
        self.message_log: list[dict[str, object]] = []
        self.pending_messages: dict[str, list[dict[str, object]]] = {}
        self.current_session: DesktopSession = self.session_store.create_session()
        self.session_rows: list[SessionSummary] = []
        self.latest_known_version: str | None = None
        self._update_prompted = False
        self._last_user_request: str | None = None
        self._last_assistant_reply: str | None = None

        current_settings = self.settings_store.load()
        self.current_locale = self._normalize_locale(current_settings.locale)

        self.status_var = tk.StringVar(value=self._t("status_ready"))
        self.active_var = tk.StringVar(value=self._t("busy_count", count=0))
        self.model_summary_var = tk.StringVar()
        self.endpoint_var = tk.StringVar()
        self.tool_mode_var = tk.StringVar()
        self.session_var = tk.StringVar()
        self.high_privilege_var = tk.BooleanVar(value=False)
        self.autonomous_execution_var = tk.BooleanVar(value=False)
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
        self._refresh_session_list()
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
        session_menu.add_command(label=self._t("session_new"), command=self._start_new_session)
        session_menu.add_command(label=self._t("session_save"), command=self._save_current_session)
        session_menu.add_command(label=self._t("session_open"), command=self._load_selected_session)
        session_menu.add_command(label=self._t("session_compact"), command=self._compact_selected_session)
        session_menu.add_command(label=self._t("session_delete"), command=self._delete_selected_session)
        session_menu.add_command(label=self._t("session_refresh"), command=self._refresh_session_list)
        session_menu.add_separator()
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

        left_shell = ttk.Frame(root, style="Shell.TFrame")
        left_shell.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        left_shell.columnconfigure(0, weight=0, minsize=24)
        left_shell.columnconfigure(1, weight=1)
        left_shell.rowconfigure(0, weight=1)

        left_track = tk.Frame(
            left_shell,
            background=PALETTE["base1"],
            highlightthickness=1,
            highlightbackground=PALETTE["base00"],
            width=20,
        )
        left_track.grid(row=0, column=0, sticky="ns", padx=(0, 6))
        left_track.grid_propagate(False)
        left_track.rowconfigure(0, weight=1)
        left_track.columnconfigure(0, weight=1)

        self.left_canvas = tk.Canvas(
            left_shell,
            background=PALETTE["base3"],
            highlightthickness=0,
            borderwidth=0,
        )
        self.left_canvas.grid(row=0, column=1, sticky="nsew")
        self.left_scrollbar = tk.Scrollbar(
            left_track,
            orient="vertical",
            command=self.left_canvas.yview,
            width=18,
            background=PALETTE["yellow"],
            troughcolor=PALETTE["base2"],
            activebackground=PALETTE["orange"],
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.left_scrollbar.grid(row=0, column=0, sticky="ns")
        self.left_canvas.configure(yscrollcommand=self.left_scrollbar.set)

        left = ttk.Frame(self.left_canvas, style="Shell.TFrame")
        left.rowconfigure(2, weight=1)
        left.columnconfigure(0, weight=1)
        self.left_window = self.left_canvas.create_window((0, 0), window=left, anchor="nw")
        left.bind("<Configure>", self._on_left_configure)
        self.left_canvas.bind("<Configure>", self._on_left_canvas_configure)

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
        self._summary_row(summary, 3, self._t("session_current"), self.session_var)

        self.chat = ChatWidget(left)
        self.chat.grid(row=2, column=0, sticky="nsew")
        self.chat.set_callbacks(
            on_submit=self._submit_request,
            on_retry=self._retry_last_request,
            on_copy=self._copy_full_conversation,
            on_stop=self._stop_active_request,
            on_clear=self._clear_chat,
            on_chip=self._insert_quick_prompt,
        )
        self.chat.set_ui_labels(self._chat_ui_labels())
        self.chat.set_runtime_state("ended", self._t("runstate_ended"))

        sidebar_shell = ttk.Frame(root, style="Sidebar.TFrame")
        sidebar_shell.grid(row=0, column=1, sticky="nsew")
        sidebar_shell.columnconfigure(0, weight=1)
        sidebar_shell.columnconfigure(1, weight=0, minsize=24)
        sidebar_shell.rowconfigure(0, weight=1)

        self.sidebar_canvas = tk.Canvas(
            sidebar_shell,
            background=PALETTE["base2"],
            highlightthickness=0,
            borderwidth=0,
        )
        self.sidebar_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar_track = tk.Frame(
            sidebar_shell,
            background=PALETTE["base1"],
            highlightthickness=1,
            highlightbackground=PALETTE["base00"],
            width=20,
        )
        scrollbar_track.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        scrollbar_track.grid_propagate(False)
        scrollbar_track.rowconfigure(0, weight=1)
        scrollbar_track.columnconfigure(0, weight=1)

        self.sidebar_scrollbar = tk.Scrollbar(
            scrollbar_track,
            orient="vertical",
            command=self.sidebar_canvas.yview,
            width=18,
            background=PALETTE["yellow"],
            troughcolor=PALETTE["base2"],
            activebackground=PALETTE["orange"],
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.sidebar_scrollbar.grid(row=0, column=0, sticky="ns")
        self.sidebar_canvas.configure(yscrollcommand=self.sidebar_scrollbar.set)

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
            text=self._t("high_privilege"),
            variable=self.high_privilege_var,
            command=self._toggle_execution_controls,
        ).grid(row=4, column=0, sticky="w", pady=(10, 0))
        ttk.Checkbutton(
            runtime_panel,
            text=self._t("autonomous_execution"),
            variable=self.autonomous_execution_var,
            command=self._toggle_execution_controls,
        ).grid(row=5, column=0, sticky="w", pady=(6, 0))

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
        lists_panel.rowconfigure(5, weight=1)

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

        ttk.Label(lists_panel, text=self._t("session_panel"), style="Muted.TLabel").grid(row=4, column=0, sticky="w", pady=(12, 0))
        session_shell = ttk.Frame(lists_panel, style="Sidebar.TFrame")
        session_shell.grid(row=5, column=0, sticky="nsew", pady=(6, 0))
        session_shell.columnconfigure(0, weight=1)
        session_shell.rowconfigure(0, weight=1)
        self.session_list = tk.Listbox(
            session_shell,
            height=10,
            background=PALETTE["base3"],
            foreground=PALETTE["base01"],
            borderwidth=1,
            highlightthickness=0,
            selectbackground=PALETTE["yellow"],
            selectforeground=PALETTE["base3"],
            font=("DejaVu Sans Mono", 10),
        )
        self.session_list.grid(row=0, column=0, sticky="nsew")
        self.session_list.bind("<Double-Button-1>", lambda _event: self._load_selected_session())
        session_buttons = ttk.Frame(session_shell, style="Sidebar.TFrame")
        session_buttons.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        session_buttons.columnconfigure((0, 1), weight=1)
        ttk.Button(session_buttons, text=self._t("session_open"), command=self._load_selected_session).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(session_buttons, text=self._t("session_compact"), command=self._compact_selected_session).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ttk.Button(session_buttons, text=self._t("session_delete"), command=self._delete_selected_session).grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=(8, 0))
        ttk.Button(session_buttons, text=self._t("session_refresh"), command=self._refresh_session_list).grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=(8, 0))

        footer = ttk.Frame(sidebar, style="Sidebar.TFrame")
        footer.grid(row=6, column=0, sticky="ew", pady=(12, 0))
        footer.columnconfigure((0, 1), weight=1)
        ttk.Button(footer, text=self._t("session_new"), command=self._start_new_session).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(footer, text=self._t("footer_reload"), command=self._load_settings_into_form).grid(row=0, column=1, sticky="ew")

    def _send_label(self) -> str:
        return {
            "en": "Send",
            "ja": "送信",
            "ko": "보내기",
            "zh": "发送",
        }.get(self.current_locale, "Send")

    def _chat_ui_labels(self) -> dict[str, object]:
        localized = {
            "en": {
                "title": "Conversation",
                "subtitle": "Cursor-style chat with quick actions, retries, and persistent task continuity.",
                "composer_title": "Message Composer",
                "hint": "Enter sends, Shift+Enter inserts a newline, Stop cancels the current run.",
                "send": "Send",
                "retry": "Retry",
                "copy": "Copy Chat",
                "stop": "Stop",
                "clear": "Clear",
                "running": "Running",
                "stopped": "Stopped",
                "ended": "Ended",
                "chip_labels": ["Explain", "Continue", "Review", "Fix", "Status", "Doctor"],
                "chip_values": [
                    "Explain the current issue clearly and propose the next concrete step.",
                    "Continue the current task from the last completed step and keep going until it is done.",
                    "Review the current workspace changes and list the highest-risk issues first.",
                    "Fix the current problem end-to-end and explain only what changed.",
                    "/status",
                    "/doctor",
                ],
            },
            "ja": {
                "title": "会話",
                "subtitle": "Cursor 風のチャット。クイック操作、再試行、継続タスクに対応。",
                "composer_title": "メッセージ入力",
                "hint": "Enter で送信、Shift+Enter で改行、停止で現在の実行を中断します。",
                "send": "送信",
                "retry": "再試行",
                "copy": "会話をコピー",
                "stop": "停止",
                "clear": "クリア",
                "running": "実行中",
                "stopped": "停止",
                "ended": "終了",
                "chip_labels": ["説明", "続行", "レビュー", "修正", "状態", "診断"],
                "chip_values": [
                    "現在の問題を明確に説明し、次の具体的な一手を示してください。",
                    "現在のタスクを直前の完了地点から継続し、完了まで進めてください。",
                    "現在のワークスペース変更をレビューし、最も重大なリスクから列挙してください。",
                    "現在の問題をエンドツーエンドで修正し、変更点だけを簡潔に説明してください。",
                    "/status",
                    "/doctor",
                ],
            },
            "ko": {
                "title": "대화",
                "subtitle": "Cursor 스타일 채팅. 빠른 작업, 재시도, 연속 작업 흐름을 지원합니다.",
                "composer_title": "메시지 작성",
                "hint": "Enter 전송, Shift+Enter 줄바꿈, 중지는 현재 실행을 취소합니다.",
                "send": "보내기",
                "retry": "다시 시도",
                "copy": "대화 복사",
                "stop": "중지",
                "clear": "지우기",
                "running": "실행 중",
                "stopped": "중지",
                "ended": "종료됨",
                "chip_labels": ["설명", "계속", "리뷰", "수정", "상태", "진단"],
                "chip_values": [
                    "현재 문제를 명확히 설명하고 다음 구체적인 단계를 제안해 주세요.",
                    "현재 작업을 마지막 완료 지점부터 이어서 끝날 때까지 계속 진행해 주세요.",
                    "현재 워크스페이스 변경사항을 리뷰하고 가장 위험한 문제부터 정리해 주세요.",
                    "현재 문제를 처음부터 끝까지 수정하고 변경점만 간단히 설명해 주세요.",
                    "/status",
                    "/doctor",
                ],
            },
            "zh": {
                "title": "对话",
                "subtitle": "更接近 Cursor 的对话面板，支持快捷动作、重试、停止和连续任务。",
                "composer_title": "消息输入区",
                "hint": "Enter 发送，Shift+Enter 换行，停止会取消当前运行。",
                "send": "发送",
                "retry": "重试",
                "copy": "复制对话",
                "stop": "停止",
                "clear": "清空",
                "running": "正在执行",
                "stopped": "已停止",
                "ended": "已结束",
                "chip_labels": ["解释", "继续", "评审", "修复", "状态", "体检"],
                "chip_values": [
                    "清楚解释当前问题，并给出下一步最具体的动作。",
                    "从上一个完成点继续当前任务，并持续工作直到完成。",
                    "评审当前工作区变更，并优先列出最高风险问题。",
                    "端到端修复当前问题，只简明说明改动内容。",
                    "/status",
                    "/doctor",
                ],
            },
        }
        return localized.get(self.current_locale, localized["en"])

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
        if role == "user":
            self._last_user_request = text
        elif role == "assistant":
            self._last_assistant_reply = text
        return message_id

    def _chat_update(self, message_id: int, text: str, title: str | None = None) -> None:
        self.chat.update_message(message_id, text, title=title)
        for row in self.message_log:
            if row.get("message_id") == message_id:
                row["text"] = text
                if title is not None:
                    row["title"] = title
                break
        for row in self.message_log:
            if row.get("message_id") == message_id:
                role = row.get("role")
                if role == "assistant":
                    self._last_assistant_reply = text
                elif role == "user":
                    self._last_user_request = text
                break

    def _chat_remove(self, message_id: int) -> None:
        self.chat.remove_message(message_id)
        self.message_log = [row for row in self.message_log if row.get("message_id") != message_id]

    def _seed_welcome(self) -> None:
        self._chat_add(self._t("welcome_message"), role="system", title=self._t("welcome_title"))
        self._chat_add(self._t("adapter_message"), role="assistant", title=self._t("adapter_title"))

    def _format_session_label(self, session: DesktopSession | SessionSummary) -> str:
        stamp = time.strftime("%m-%d %H:%M", time.localtime(session.updated_at_ms / 1000))
        return f"{stamp} · {session.session_id}"

    def _session_preview_line(self, row: SessionSummary) -> str:
        return f"{self._format_session_label(row)} · {row.preview}"

    def _refresh_session_summary(self) -> None:
        self.session_var.set(self._format_session_label(self.current_session))

    def _refresh_session_list(self) -> None:
        self.session_rows = self.session_store.list_sessions()
        if not hasattr(self, "session_list"):
            return
        self.session_list.delete(0, "end")
        if not self.session_rows:
            self.session_list.insert("end", self._t("session_none"))
            return
        for row in self.session_rows:
            self.session_list.insert("end", self._session_preview_line(row))
        selected_index = next(
            (index for index, row in enumerate(self.session_rows) if row.path == self.current_session.path),
            0,
        )
        self.session_list.selection_clear(0, "end")
        self.session_list.selection_set(selected_index)

    def _selected_session_summary(self) -> SessionSummary | None:
        if not self.session_rows:
            return None
        selection = self.session_list.curselection() if hasattr(self, "session_list") else ()
        index = int(selection[0]) if selection else 0
        if 0 <= index < len(self.session_rows):
            return self.session_rows[index]
        return None

    def _messages_for_persistence(self) -> list[SessionMessage]:
        rows: list[SessionMessage] = []
        for entry in self.message_log:
            role = str(entry.get("role") or "")
            text = str(entry.get("text") or "").strip()
            title = str(entry.get("title") or "")
            if not text:
                continue
            if title in {self._t("welcome_title"), self._t("adapter_title")}:
                continue
            if role not in {"user", "assistant", "tool", "error"}:
                continue
            mapped_role = "assistant" if role in {"assistant", "error"} else role
            rows.append(SessionMessage(role=mapped_role, text=text))
        return rows

    def _save_current_session(self, *, silent: bool = False) -> None:
        try:
            self.current_session = self.session_store.replace_with_messages(
                self.current_session,
                self._messages_for_persistence(),
                compaction_summary=self.current_session.compaction_summary,
            )
            self._refresh_session_summary()
            self._refresh_session_list()
            if not silent:
                self.status_var.set(self._t("session_saved"))
        except Exception:
            if not silent:
                self.status_var.set(self._t("session_save_failed"))

    def _load_session_into_ui(self, session: DesktopSession) -> None:
        self.current_session = session
        self.chat.clear()
        self.message_log.clear()
        self._last_user_request = None
        self._last_assistant_reply = None
        conversation_turns: list[tuple[str, str]] = []
        if not session.messages:
            self._seed_welcome()
        else:
            for message in session.messages:
                if message.role == "user":
                    self._chat_add(message.text, role="user", title=self._t("user_request_title"))
                    conversation_turns.append(("user", message.text))
                elif message.role == "assistant":
                    self._chat_add(message.text, role="assistant", title=self._t("reply_title"))
                    conversation_turns.append(("assistant", message.text))
                elif message.role == "tool":
                    self._chat_add(message.text, role="tool", title=self._t("cli_title"))
        self.bridge.set_conversation(conversation_turns)
        self._refresh_session_summary()
        self._refresh_session_list()
        self.status_var.set(self._t("session_loaded"))
        self.chat.focus_input()

    def _load_selected_session(self) -> None:
        row = self._selected_session_summary()
        if row is None or not row.path.exists():
            self.status_var.set(self._t("session_load_failed"))
            return
        try:
            self._load_session_into_ui(self.session_store.load_session(row.path))
        except Exception:
            self.status_var.set(self._t("session_load_failed"))

    def _start_new_session(self) -> None:
        self.current_session = self.session_store.create_session()
        self.bridge.reset_conversation()
        self.chat.clear()
        self.message_log.clear()
        self.pending_messages.clear()
        self._last_user_request = None
        self._last_assistant_reply = None
        self._seed_welcome()
        self._refresh_session_summary()
        self._refresh_session_list()
        self.status_var.set(self._t("status_cleared"))
        self.chat.focus_input()

    def _compact_selected_session(self) -> None:
        row = self._selected_session_summary()
        if row is None or not row.path.exists():
            self.status_var.set(self._t("session_compact_failed"))
            return
        try:
            session = self.session_store.load_session(row.path)
            session, detail = self.session_store.compact_session(session)
            self._chat_add(detail, role="system", title=self._t("session_compacted"))
            if session.path == self.current_session.path:
                self._load_session_into_ui(session)
            else:
                self._refresh_session_list()
            self.status_var.set(self._t("session_compacted"))
        except Exception as exc:
            self._chat_add(str(exc), role="error", title=self._t("session_compact_failed"))
            self.status_var.set(self._t("session_compact_failed"))

    def _delete_selected_session(self) -> None:
        row = self._selected_session_summary()
        if row is None or not row.path.exists():
            return
        if not messagebox.askyesno(
            self._t("session_delete_confirm_title"),
            self._t("session_delete_confirm_body", path=str(row.path)),
        ):
            return
        self.session_store.delete_session(row.path)
        if row.path == self.current_session.path:
            self._start_new_session()
        else:
            self._refresh_session_list()
            self.status_var.set(self._t("session_deleted"))

    def _load_settings_into_form(self) -> None:
        settings = self.settings_store.load()
        self.current_locale = self._normalize_locale(settings.locale)
        self.model_entry_var.set(settings.model)
        self.base_url_entry_var.set(settings.base_url)
        self.api_key_entry_var.set(settings.api_key)
        self.tool_style_entry_var.set(settings.tool_call_style)
        self.high_privilege_var.set(settings.high_privilege)
        self.autonomous_execution_var.set(settings.autonomous_execution)
        self._refresh_model_summary(settings)
        self._refresh_session_summary()
        self.active_var.set(self._t("busy_count", count=self.bridge.active_process_count()))
        self.status_var.set(self._t("status_loaded"))
        self.chat.set_runtime_state("ended", self._t("runstate_ended"))

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
            high_privilege=self.high_privilege_var.get(),
            autonomous_execution=self.autonomous_execution_var.get(),
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
            high_privilege=self.high_privilege_var.get(),
            autonomous_execution=self.autonomous_execution_var.get(),
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
                high_privilege="on" if settings.high_privilege else "off",
                autonomous_execution="on" if settings.autonomous_execution else "off",
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

    def _retry_last_request(self) -> None:
        if not self._last_user_request:
            return
        self.chat.insert_prompt(self._last_user_request, replace=True)
        self._submit_request(self._last_user_request)

    def _copy_full_conversation(self) -> None:
        rows: list[str] = []
        for entry in self.message_log:
            text = str(entry.get("text") or "").strip()
            if not text:
                continue
            title = str(entry.get("title") or "").strip()
            if title:
                rows.append(f"[{title}]\n{text}")
            else:
                rows.append(text)
        payload = "\n\n".join(rows).strip()
        if not payload:
            return
        self.clipboard_clear()
        self.clipboard_append(payload)
        self.status_var.set(self._t("copy_chat_done"))

    def _stop_active_request(self) -> None:
        cancelled = self.bridge.cancel_active()
        if cancelled:
            self.chat.set_runtime_state("stopped", self._t("runstate_stopped"))
            self.status_var.set("request cancelled" if self.current_locale == "en" else ("请求已取消" if self.current_locale == "zh" else ("リクエストを中止しました" if self.current_locale == "ja" else "요청을 중지했습니다")))
            self._chat_add(
                "Current desktop request cancelled." if self.current_locale == "en" else ("当前桌面请求已取消。" if self.current_locale == "zh" else ("現在のデスクトップ要求を中止しました。" if self.current_locale == "ja" else "현재 데스크톱 요청을 중지했습니다.")),
                role="system",
                title=self._t("cli_title"),
            )

    def _insert_quick_prompt(self, prompt: str) -> None:
        self.chat.insert_prompt(prompt, replace=False)

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
        self.chat.set_runtime_state("running", self._t("runstate_running"))
        try:
            pending_id = self._chat_add(
                self._t("pending_body", seconds=0.0),
                role="assistant",
                title=self._t("cli_title"),
            )
            self.pending_messages.setdefault(request, []).append(
                {
                    "message_id": pending_id,
                    "started_at": time.time(),
                    "status_text": "",
                    "tool_message_id": None,
                    "cli_text": "",
                }
            )
            self._tick_pending_message(request)
            self.bridge.submit(request, self.results.put, self.results.put)
            self._refresh_log()
            self._refresh_process_list()
        except Exception as exc:
            self._clear_pending_message(request)
            self._chat_add(str(exc), role="error", title=self._t("validation_title"))
            self.status_var.set(self._t("status_denied"))

    def _toggle_execution_controls(self) -> None:
        settings = self._current_form_settings()
        self.settings_store.save(settings)
        state = self.bridge.set_execution_controls(
            self.high_privilege_var.get(),
            self.autonomous_execution_var.get(),
        )
        self.status_var.set(state)
        self._chat_add(state, role="system", title=self._t("permission_mode_title"))

    def _clear_chat(self) -> None:
        self._start_new_session()

    def _drain_results(self) -> None:
        try:
            while True:
                result = self.results.get_nowait()
                if isinstance(result, BridgeEvent):
                    self._handle_bridge_event(result)
                else:
                    self._handle_result(result)
        except queue.Empty:
            pass
        finally:
            self.after(120, self._drain_results)

    def _handle_bridge_event(self, event: BridgeEvent) -> None:
        pending_queue = self.pending_messages.get(event.request_text, [])
        pending = pending_queue[0] if pending_queue else None
        if pending is None:
            return
        if event.kind == "status":
            pending["status_text"] = event.text
            self.status_var.set(event.text)
            return
        if event.kind == "cli":
            pending["cli_text"] = event.text
            self._chat_update(int(pending["message_id"]), event.text, title=self._t("cli_title"))
            return
        if event.kind == "tool":
            pending["status_text"] = event.text.splitlines()[-1]
            self.status_var.set(pending["status_text"])
            return

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
        self.chat.set_runtime_state(
            "ended" if result.exit_code == 0 else "stopped",
            self._t("runstate_ended") if result.exit_code == 0 else self._t("runstate_stopped"),
        )

        pending_queue = self.pending_messages.get(result.request_text, [])
        pending = pending_queue.pop(0) if pending_queue else None
        if not pending_queue and result.request_text in self.pending_messages:
            self.pending_messages.pop(result.request_text, None)

        cli_payload = self.bridge.render_cli_transcript(result).strip()
        if result.stdout:
            payload = cli_payload or self._render_stdout(result)
            if pending and payload:
                self._chat_update(int(pending["message_id"]), payload, title=self._t("cli_title"))
            elif payload:
                self._chat_add(payload, role="assistant", title=self._t("cli_title"))
            elif pending:
                self._chat_remove(int(pending["message_id"]))
        if result.stderr:
            self._chat_add(result.stderr, role="error", title=self._t("stderr_title"))
        if result.exit_code != 0 or result.stderr:
            self._chat_add(
                self._t("run_detail_exit", code=result.exit_code, seconds=result.duration_seconds),
                role="system" if result.exit_code == 0 else "error",
                title=self._t("run_detail_title"),
            )
        if not result.stdout and not result.stderr:
            if pending:
                self._chat_update(int(pending["message_id"]), self._t("no_output"), title=self._t("cli_title"))
            else:
                self._chat_add(self._t("no_output"), role="tool", title=self._t("cli_title"))

        if not result.request_text.startswith("/") and not result.request_text.startswith("__"):
            self._save_current_session(silent=True)

        self._refresh_log()
        self._refresh_process_list()

    def _render_stdout(self, result: CommandResult) -> str:
        text = self.bridge.normalize_result_text(result).strip()
        if text:
            return text
        if isinstance(result.parsed_stdout, dict):
            tool_results = result.parsed_stdout.get("tool_results")
            if isinstance(tool_results, list) and tool_results:
                last = tool_results[-1]
                if isinstance(last, dict):
                    output = last.get("output")
                    if isinstance(output, str) and output.strip():
                        return output.strip()
        return result.stdout.strip()

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
        status_text = str(pending.get("status_text") or "").strip()
        body = self._t("pending_body", seconds=elapsed)
        if status_text:
            body = f"{body}\n\n{status_text}"
        elif elapsed >= 3.0:
            body = f"{body}\n\n{self._t('pending_silent')}"
        self._chat_update(
            int(pending["message_id"]),
            body,
            title=self._t("cli_title"),
        )
        self.after(400, lambda: self._tick_pending_message(request))

    def _clear_pending_message(self, request: str) -> None:
        pending_queue = self.pending_messages.get(request, [])
        pending = pending_queue.pop() if pending_queue else None
        if not pending_queue and request in self.pending_messages:
            self.pending_messages.pop(request, None)
        if pending is None:
            return
        tool_message_id = pending.get("tool_message_id")
        if tool_message_id is not None:
            self._chat_remove(int(tool_message_id))
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

    def _on_left_configure(self, _event) -> None:
        self.left_canvas.configure(scrollregion=self.left_canvas.bbox("all"))

    def _on_left_canvas_configure(self, event) -> None:
        self.left_canvas.itemconfigure(self.left_window, width=event.width)

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
