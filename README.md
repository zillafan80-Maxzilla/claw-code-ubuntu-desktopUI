# claw-code-ubuntu-desktopUI

当前发布版本 / Current release: `v2.1`

## 中文说明

### 项目简介

`claw-code-ubuntu-desktopUI` 是一个面向 Ubuntu 桌面的 npm 安装包，用来为 `claw-code` 自动部署桌面 UI、模型环境配置和桌面快捷方式。

它解决三类问题：

1. 自动发现本机已有的 `claw-code` 根目录，并把桌面 UI 安装到正确位置。
2. 自动探测本机可用模型接口，并把模型、接口地址、API Key、工具调用适配模式写入 UI 环境文件。
3. 如果本机没有安装 `claw-code`，安装器会交互式询问是否安装 `claw-code (local)` 版本；输入 `y` 或 `yes` 后，会把本地运行时、桌面 UI 和快捷方式一起安装完成。

当前 UI 特性包括：

- 英文、日文、韩文、中文四语言界面
- Solarized Light 主题
- Cursor 风格的增强对话面板
- 更大的多行输入区与快捷操作区
- 支持停止生成、重试上一轮、复制最后回复
- 会话连续上下文，支持持续多轮任务推进
- 普通对话现在按 CLI 文本流实时渲染，不再只等待最终 JSON
- 会显示思考状态、工具执行状态和完成状态，更贴近 CLI 终端体验
- 新增 UI 原生历史会话模块，支持自动保存、查看、加载、压缩和删除
- 历史会话保存到桌面 UI 配置目录，不依赖 CLI 会话管理入口
- 对话消息现在支持正文选择复制、右键复制和消息级一键复制
- 执行控制拆分为“系统级高权限”和“自动执行”两个独立选项
- 系统级高权限映射到真实 `danger-full-access` 权限模式，自动执行负责无确认地持续完成任务
- 桌面桥接新增失败自动兜底执行，避免把伪 tool_call 半成品写入历史会话
- 模型摘要与模型配置面板
- 右侧控制栏可滚动
- 自动进程托管与退出清理
- Gemma 类模型的宽口径工具调用适配
- 回复内容自动抽取自然语言正文，不显示底层 JSON 标签噪音
- 桌面对话链路已补齐工具执行与任务连续工作能力
- 帮助菜单内置“更新桌面组件”入口
- 默认语言为英文，可在“语言”菜单中即时切换
- 启动时自动检查 npm 最新版本，旧版用户可看到更新提示并直接升级
- 等待计时与运行状态只显示在状态区域，不再每秒写入对话正文污染上下文
- WebSearch 增加搜索后端降级路径，不再只依赖单一 DuckDuckGo HTML 入口

### 安装方式

#### 方式一：本地目录安装

```bash
cd claw-code-ubuntu-desktopUI
npm install
```

安装完成后，如需重新运行交互式安装器：

```bash
npx claw-code-ubuntu-desktopui-install
```

#### 方式二：全局安装

```bash
npm install -g claw-code-ubuntu-desktopui
claw-code-ubuntu-desktopui-install
```

### 安装器行为

安装器会按以下顺序执行：

1. 搜索常见路径中的 `claw-code` 根目录。
2. 若已找到，则把桌面 UI 和图标复制到该根目录。
3. 读取已有 UI 配置、系统环境变量与本地模型接口。
4. 探测本地 OpenAI 兼容或 Ollama 接口。
5. 自动写入 `desktop-ui/.env.desktop`。
6. 自动写入 `~/.config/claw-code-desktop/settings.json`。
7. 自动创建 `~/Desktop/claw-code.desktop` 快捷方式。
8. 若未找到 `claw-code`，则提示是否安装本地版本。
9. 已安装后，可在桌面窗口中使用“帮助 > 更新桌面组件”直接拉取最新发布版并重新部署。
10. 自 `1.2` 起的用户打开桌面窗口后，会自动检查是否存在更新；如发现 `2.1` 或更高版本，会弹出更新提示并可直接执行升级。

### 默认探测的模型接口

安装器会优先检查：

- `OPENAI_BASE_URL`
- 目标根目录下已有的 `desktop-ui/.env.desktop`
- `~/.config/claw-code-desktop/settings.json`
- `http://127.0.0.1:8001/v1/models`
- `http://127.0.0.1:8000/v1/models`
- `http://127.0.0.1:11434/api/tags`

### Gemma 工具调用适配

这个安装包不是把模型写死成某一种 provider-native tools 协议。

对于 Gemma 类模型：

- 默认使用 `auto`
- 在需要时自动切到 `gemma-json`
- UI 配置面板可以切换 `auto / native / gemma-json`

### 常用命令

```bash
claw-code-ubuntu-desktopui-install --yes
claw-code-ubuntu-desktopui-install --target ~/claw-code
claw-code-ubuntu-desktopui-install --desktop-dir ~/Desktop
claw-code-ubuntu-desktopui-install --skip-shortcut
```

### 目录结构

```text
claw-code-ubuntu-desktopUI/
├── bin/
├── lib/
├── payload/
│   └── claw-code/
├── templates/
├── package.json
└── README.md
```

### 安装后结果

安装器完成后，你会得到：

- 一个可运行的 `claw-code` 桌面 UI
- 自动生成的 UI 环境文件
- 自动生成的桌面快捷方式
- 可持久化的模型配置

---

## English

### Overview

`claw-code-ubuntu-desktopUI` is an npm installer package for Ubuntu desktop environments. It deploys the `claw-code` desktop UI, prepares model/runtime configuration, and creates a desktop shortcut automatically.

It covers three installation paths:

1. Detect an existing `claw-code` root and install the desktop UI into the correct location.
2. Discover available local model endpoints and write model/base URL/API key/tool-call mode into the UI environment file.
3. If `claw-code` is missing, ask whether to install a local bundled version; replying `y` or `yes` installs the local runtime, desktop UI, and shortcut together.

Current UI capabilities include:

- Full multilingual UI in English, Japanese, Korean, and Chinese
- Solarized Light theme
- Cursor-style enhanced chat panel
- Larger multiline composer with quick action prompts
- Stop generation, retry last turn, and copy latest reply actions
- Continuous conversation context for longer task execution
- Regular prompts now render from the live CLI text stream instead of waiting only for a final JSON payload
- Thinking state, tool execution state, and completion state are shown during the run to stay closer to the CLI experience
- Added a UI-native session history module with automatic save, browse, load, compact, and delete actions
- Session history is stored in the desktop UI configuration area and does not depend on the CLI session management entry points
- Chat messages now support text selection, right-click copy, and one-click copy per message
- Execution control is split into independent System-Level High Privilege and Autonomous Execution options
- System-Level High Privilege maps to the real `danger-full-access` permission mode, while Autonomous Execution controls no-confirmation task completion
- The desktop bridge now retries with a structured fallback path to avoid persisting raw pseudo tool-call stubs
- Model summary and model configuration panel
- Scrollable right control sidebar
- Managed process lifecycle and cleanup on exit
- Broad tool-calling compatibility for Gemma-family models
- Automatic extraction of natural-language reply content instead of raw JSON metadata noise
- Desktop-side fixes for tool execution and sustained multi-step task flow
- Built-in `Help > Update Desktop Components` action
- English as the default language with live switching through the `Language` menu
- Startup npm version checks so older installs can see an update prompt and upgrade directly
- Waiting timers and silent-running indicators now stay in the status area instead of rewriting chat transcript content every second
- WebSearch now has backend fallback behavior instead of depending only on a single DuckDuckGo HTML endpoint

### Installation

#### Option 1: Install from local directory

```bash
cd claw-code-ubuntu-desktopUI
npm install
```

To rerun the interactive installer manually:

```bash
npx claw-code-ubuntu-desktopui-install
```

#### Option 2: Global install

```bash
npm install -g claw-code-ubuntu-desktopui
claw-code-ubuntu-desktopui-install
```

### Installer behavior

The installer performs the following steps:

1. Search common paths for an existing `claw-code` root.
2. If found, copy the desktop UI and icon assets into that root.
3. Read existing UI settings, environment variables, and local model endpoints.
4. Probe local OpenAI-compatible or Ollama endpoints.
5. Write `desktop-ui/.env.desktop`.
6. Write `~/.config/claw-code-desktop/settings.json`.
7. Create `~/Desktop/claw-code.desktop`.
8. If `claw-code` is not found, prompt to install a local bundled version.
9. After installation, the desktop window can self-update through `Help > Update Desktop Components`.
10. Users coming from `1.2` will see an upgrade prompt on startup when `2.1` or newer is available, and can update in place.

### Probed model endpoints

The installer checks, in order:

- `OPENAI_BASE_URL`
- Existing `desktop-ui/.env.desktop`
- `~/.config/claw-code-desktop/settings.json`
- `http://127.0.0.1:8001/v1/models`
- `http://127.0.0.1:8000/v1/models`
- `http://127.0.0.1:11434/api/tags`

### Gemma tool-calling strategy

This package does not hard-code the UI to a single native tools protocol.

For Gemma-family models:

- the default mode is `auto`
- the runtime can fall back to `gemma-json`
- the UI exposes `auto / native / gemma-json` as configurable options

### Common commands

```bash
claw-code-ubuntu-desktopui-install --yes
claw-code-ubuntu-desktopui-install --target ~/claw-code
claw-code-ubuntu-desktopui-install --desktop-dir ~/Desktop
claw-code-ubuntu-desktopui-install --skip-shortcut
```

### Repository layout

```text
claw-code-ubuntu-desktopUI/
├── bin/
├── lib/
├── payload/
│   └── claw-code/
├── templates/
├── package.json
└── README.md
```

### Installed output

After installation, you get:

- a runnable `claw-code` desktop UI
- an auto-generated UI environment file
- an auto-generated desktop shortcut
- persistent model configuration
