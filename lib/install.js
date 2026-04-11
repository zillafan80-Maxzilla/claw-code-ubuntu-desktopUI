"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const readline = require("readline");
const http = require("http");
const https = require("https");

const PACKAGE_ROOT = path.resolve(__dirname, "..");
const PAYLOAD_ROOT = path.join(PACKAGE_ROOT, "payload", "claw-code");
const TEMPLATE_DESKTOP = path.join(PACKAGE_ROOT, "templates", "claw-code.desktop");
const DEFAULT_LOCAL_INSTALL_ROOT = path.join(os.homedir(), "claw-code-local", "claw-code");
const SETTINGS_HOME = path.join(os.homedir(), ".config", "claw-code-desktop");
const SETTINGS_PATH = path.join(SETTINGS_HOME, "settings.json");

async function runCli(argv) {
  const options = parseArgs(argv);
  const result = await installPackage({
    interactive: true,
    allowPrompt: true,
    ...options,
  });
  printSummary(result);
  return result;
}

async function runPostinstall() {
  if (process.env.CLAW_CODE_UI_SKIP_POSTINSTALL === "1") {
    return null;
  }
  if (!process.stdout.isTTY || process.env.CI === "true") {
    console.log(
      "[claw-code-ubuntu-desktopui] 已安装包文件。需要交互式安装时，请运行 `claw-code-ubuntu-desktopui-install`。"
    );
    return null;
  }
  return installPackage({
    interactive: true,
    allowPrompt: true,
  });
}

function parseArgs(argv) {
  const options = {
    yes: false,
    targetRoot: null,
    desktopDir: null,
    skipShortcut: false,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--yes" || arg === "-y") {
      options.yes = true;
    } else if (arg === "--skip-shortcut") {
      options.skipShortcut = true;
    } else if (arg === "--target") {
      options.targetRoot = mustReadValue(argv, ++index, "--target");
    } else if (arg === "--desktop-dir") {
      options.desktopDir = mustReadValue(argv, ++index, "--desktop-dir");
    } else {
      throw new Error(`未知参数: ${arg}`);
    }
  }
  return options;
}

function mustReadValue(argv, index, flag) {
  const value = argv[index];
  if (!value) {
    throw new Error(`${flag} 缺少值`);
  }
  return value;
}

async function installPackage(options) {
  const targetRoot = options.targetRoot
    ? path.resolve(options.targetRoot)
    : detectInstalledClawRoot();

  let root = targetRoot;
  let installedLocalVersion = false;
  if (!root) {
    if (!options.allowPrompt) {
      throw new Error("本地未找到 claw-code。");
    }
    console.log("本地未安装 claw code。");
    const shouldInstall = options.yes
      ? true
      : await askYesNo("是否安装 claw code (local) 版本？ [y/N] ");
    if (!shouldInstall) {
      throw new Error("用户取消安装。");
    }
    root = DEFAULT_LOCAL_INSTALL_ROOT;
    installLocalClawBundle(root);
    installedLocalVersion = true;
  } else {
    ensureDirectory(root);
  }

  installDesktopUi(root);
  const modelConfig = await detectModelConfig(root);
  writeEnvFile(root, modelConfig);
  persistSettings(modelConfig);

  const desktopDir =
    options.desktopDir && options.desktopDir.trim()
      ? path.resolve(options.desktopDir)
      : detectDesktopDir();
  let shortcutPath = null;
  if (!options.skipShortcut) {
    shortcutPath = createDesktopShortcut(root, desktopDir);
  }

  return {
    root,
    installedLocalVersion,
    modelConfig,
    shortcutPath,
  };
}

function detectInstalledClawRoot() {
  const home = os.homedir();
  const candidates = [
    process.env.CLAW_CODE_ROOT,
    path.join(process.cwd(), "claw-code"),
    process.cwd(),
    "/root/llm-server/tools/claw-code",
    path.join(home, "claw-code"),
    path.join(home, "tools", "claw-code"),
    path.join(home, "claw-code-local", "claw-code"),
    path.join(home, "llm-server", "tools", "claw-code"),
  ].filter(Boolean);

  for (const candidate of candidates) {
    const resolved = path.resolve(candidate);
    if (isClawRoot(resolved)) {
      return resolved;
    }
  }
  return null;
}

function isClawRoot(root) {
  return (
    fs.existsSync(path.join(root, "bin", "claw")) &&
    fs.existsSync(path.join(root, "desktop-ui", "main.py"))
  );
}

function installLocalClawBundle(root) {
  ensureDirectory(path.dirname(root));
  copyRecursive(PAYLOAD_ROOT, root);
  fs.chmodSync(path.join(root, "bin", "claw"), 0o755);
  fs.chmodSync(path.join(root, "desktop-ui", "scripts", "launcher.sh"), 0o755);
}

function installDesktopUi(root) {
  const sourceUi = path.join(PAYLOAD_ROOT, "desktop-ui");
  const targetUi = path.join(root, "desktop-ui");
  copyRecursive(sourceUi, targetUi);
  copyRecursive(
    path.join(PAYLOAD_ROOT, "assets"),
    path.join(root, "assets")
  );
  if (!fs.existsSync(path.join(root, "bin", "claw"))) {
    ensureDirectory(path.join(root, "bin"));
    fs.copyFileSync(
      path.join(PAYLOAD_ROOT, "bin", "claw"),
      path.join(root, "bin", "claw")
    );
    fs.chmodSync(path.join(root, "bin", "claw"), 0o755);
  }
  fs.chmodSync(path.join(root, "desktop-ui", "scripts", "launcher.sh"), 0o755);
}

async function detectModelConfig(root) {
  const persisted = readJsonIfExists(SETTINGS_PATH);
  const envFromUi = parseEnvFile(path.join(root, "desktop-ui", ".env.desktop"));

  const baseConfig = {
    model:
      process.env.CLAW_DESKTOP_MODEL ||
      envFromUi.CLAW_DESKTOP_MODEL ||
      persisted.model ||
      "openai/gemma-4-31b-it-q8-prod",
    base_url:
      process.env.OPENAI_BASE_URL ||
      envFromUi.OPENAI_BASE_URL ||
      persisted.base_url ||
      "http://127.0.0.1:8001/v1",
    api_key:
      process.env.OPENAI_API_KEY ||
      envFromUi.OPENAI_API_KEY ||
      persisted.api_key ||
      "local-dev-token",
    tool_call_style:
      process.env.CLAW_TOOL_CALL_STYLE ||
      envFromUi.CLAW_TOOL_CALL_STYLE ||
      persisted.tool_call_style ||
      "auto",
  };

  const probes = [
    { type: "openai", baseUrl: baseConfig.base_url },
    { type: "openai", baseUrl: "http://127.0.0.1:8001/v1" },
    { type: "openai", baseUrl: "http://127.0.0.1:8000/v1" },
    { type: "ollama", baseUrl: "http://127.0.0.1:11434" },
  ];

  for (const probe of probes) {
    try {
      const discovered = await probeModelEndpoint(probe);
      if (discovered) {
        return normalizeModelConfig({
          model: discovered.model,
          base_url: discovered.baseUrl,
          api_key: discovered.apiKey,
          tool_call_style: inferredToolCallStyle(discovered.model),
        });
      }
    } catch (_error) {
      // keep probing
    }
  }

  return normalizeModelConfig(baseConfig);
}

async function probeModelEndpoint(probe) {
  if (probe.type === "openai") {
    const url = new URL("/models", probe.baseUrl.endsWith("/") ? probe.baseUrl : `${probe.baseUrl}/`);
    const payload = await requestJson(url);
    const model =
      payload?.data?.[0]?.id ||
      payload?.data?.[0]?.name ||
      payload?.models?.[0]?.model ||
      payload?.models?.[0]?.name;
    if (!model) {
      return null;
    }
    return {
      model: model.startsWith("openai/") ? model : `openai/${model}`,
      baseUrl: probe.baseUrl,
      apiKey: "local-dev-token",
    };
  }

  if (probe.type === "ollama") {
    const url = new URL("/api/tags", probe.baseUrl);
    const payload = await requestJson(url);
    const model = payload?.models?.[0]?.name;
    if (!model) {
      return null;
    }
    return {
      model: model.startsWith("openai/") ? model : model,
      baseUrl: "http://127.0.0.1:11434/v1",
      apiKey: "ollama",
    };
  }

  return null;
}

function normalizeModelConfig(config) {
  const normalized = {
    model: String(config.model || "openai/gemma-4-31b-it-q8-prod").trim(),
    base_url: String(config.base_url || "http://127.0.0.1:8001/v1").trim(),
    api_key: String(config.api_key || "local-dev-token").trim(),
    tool_call_style: String(config.tool_call_style || "auto").trim(),
  };
  if (!normalized.tool_call_style) {
    normalized.tool_call_style = "auto";
  }
  return normalized;
}

function inferredToolCallStyle(model) {
  return String(model).toLowerCase().includes("gemma") ? "auto" : "native";
}

function writeEnvFile(root, config) {
  const envPath = path.join(root, "desktop-ui", ".env.desktop");
  const content = [
    "# Generated by claw-code-ubuntu-desktopui installer",
    `export OPENAI_BASE_URL="${escapeShell(config.base_url)}"`,
    `export OPENAI_API_KEY="${escapeShell(config.api_key)}"`,
    `export CLAW_DESKTOP_MODEL="${escapeShell(config.model)}"`,
    `export CLAW_TOOL_CALL_STYLE="${escapeShell(config.tool_call_style)}"`,
    "",
  ].join("\n");
  fs.writeFileSync(envPath, content, "utf8");
}

function persistSettings(config) {
  ensureDirectory(SETTINGS_HOME);
  fs.writeFileSync(`${SETTINGS_PATH}`, JSON.stringify(config, null, 2), "utf8");
}

function detectDesktopDir() {
  const candidate = path.join(os.homedir(), "Desktop");
  ensureDirectory(candidate);
  return candidate;
}

function createDesktopShortcut(root, desktopDir) {
  ensureDirectory(desktopDir);
  const template = fs.readFileSync(TEMPLATE_DESKTOP, "utf8");
  const launcher = path.join(root, "desktop-ui", "scripts", "launcher.sh");
  const icon = path.join(root, "assets", "claw-hero.jpeg");
  const rendered = template
    .replace(/__EXEC__/g, launcher)
    .replace(/__ICON__/g, icon)
    .replace(/__ROOT__/g, root);
  const shortcutPath = path.join(desktopDir, "claw-code.desktop");
  fs.writeFileSync(shortcutPath, rendered, "utf8");
  fs.chmodSync(shortcutPath, 0o755);
  return shortcutPath;
}

function copyRecursive(source, target) {
  const stat = fs.statSync(source);
  if (stat.isDirectory()) {
    ensureDirectory(target);
    for (const entry of fs.readdirSync(source)) {
      copyRecursive(path.join(source, entry), path.join(target, entry));
    }
    return;
  }
  ensureDirectory(path.dirname(target));
  fs.copyFileSync(source, target);
}

function ensureDirectory(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function readJsonIfExists(filePath) {
  try {
    if (!fs.existsSync(filePath)) {
      return {};
    }
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (_error) {
    return {};
  }
}

function parseEnvFile(filePath) {
  if (!fs.existsSync(filePath)) {
    return {};
  }
  const result = {};
  const lines = fs.readFileSync(filePath, "utf8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }
    const normalized = trimmed.replace(/^export\s+/, "");
    const index = normalized.indexOf("=");
    if (index === -1) {
      continue;
    }
    const key = normalized.slice(0, index).trim();
    let value = normalized.slice(index + 1).trim();
    value = value.replace(/^"/, "").replace(/"$/, "");
    result[key] = value;
  }
  return result;
}

function escapeShell(value) {
  return String(value).replace(/"/g, '\\"');
}

function askYesNo(prompt) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
    });
    rl.question(prompt, (answer) => {
      rl.close();
      const normalized = String(answer || "").trim().toLowerCase();
      resolve(normalized === "y" || normalized === "yes");
    });
  });
}

function requestJson(url) {
  const client = url.protocol === "https:" ? https : http;
  return new Promise((resolve, reject) => {
    const request = client.get(
      url,
      {
        headers: {
          Accept: "application/json",
        },
        timeout: 1500,
      },
      (response) => {
        if ((response.statusCode || 500) >= 400) {
          response.resume();
          reject(new Error(`HTTP ${response.statusCode}`));
          return;
        }
        let body = "";
        response.setEncoding("utf8");
        response.on("data", (chunk) => {
          body += chunk;
        });
        response.on("end", () => {
          try {
            resolve(JSON.parse(body));
          } catch (error) {
            reject(error);
          }
        });
      }
    );
    request.on("timeout", () => {
      request.destroy(new Error("timeout"));
    });
    request.on("error", reject);
  });
}

function printSummary(result) {
  console.log("");
  console.log("安装完成。");
  console.log(`claw-code 根目录: ${result.root}`);
  console.log(`模型: ${result.modelConfig.model}`);
  console.log(`接口: ${result.modelConfig.base_url}`);
  console.log(`工具适配: ${result.modelConfig.tool_call_style}`);
  if (result.shortcutPath) {
    console.log(`桌面快捷方式: ${result.shortcutPath}`);
  }
  if (result.installedLocalVersion) {
    console.log("已安装本地 claw-code 运行时。");
  }
}

module.exports = {
  installPackage,
  runCli,
  runPostinstall,
};
