"""Check Browser document synchronization without a browser or network request."""

import json
import runpy
from collections.abc import Callable
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]


def check(root: Path) -> dict[str, object]:
    folder = root / "docs/marketing"
    module = runpy.run_path(str(folder / "browser_mirror.py"))
    verify = cast(Callable[[Path], dict[str, object]], module["verify_browser_mirror"])
    return verify(folder)


if __name__ == "__main__":
    try:
        result = check(ROOT)
    except (OSError, ValueError, KeyError, TypeError, SyntaxError):
        print(
            json.dumps(
                {
                    "source_id": "SRC-009",
                    "status": "failed",
                    "runtime_acceptance": "not_run",
                },
                sort_keys=True,
            )
        )
        raise SystemExit(1) from None
    print(json.dumps(result, sort_keys=True))
