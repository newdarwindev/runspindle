"""Check presentation scope and source/PDF separation without executing TeX."""

import json
import runpy
from collections.abc import Callable
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]


def check(root: Path) -> dict[str, object]:
    folder = root / "docs/marketing"
    module = runpy.run_path(str(folder / "presentation_source.py"))
    verify = cast(
        Callable[[Path], dict[str, object]], module["verify_presentation_source"]
    )
    return verify(folder)


if __name__ == "__main__":
    print(json.dumps(check(ROOT), sort_keys=True))
