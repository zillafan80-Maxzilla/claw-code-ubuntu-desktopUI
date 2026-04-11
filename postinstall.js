const { runPostinstall } = require("./lib/install");

runPostinstall().catch((error) => {
  console.warn(`[claw-code-ubuntu-desktopui] postinstall skipped: ${error.message}`);
});
