#!/usr/bin/env node

const { runCli } = require("../lib/install");

runCli(process.argv.slice(2)).catch((error) => {
  console.error(`[claw-code-ubuntu-desktopui] 安装失败: ${error.message}`);
  process.exit(1);
});
