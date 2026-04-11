from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.lifecycle import LifecycleManager, cleanup_runtime
from ui.main_window import MainWindow


def main() -> int:
    if "--cleanup-only" in sys.argv:
        cleanup_runtime()
        return 0

    lifecycle = LifecycleManager(ROOT)
    lifecycle.prepare_launch()
    app = MainWindow(ROOT, lifecycle)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
