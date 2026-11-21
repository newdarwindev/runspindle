"""One isolated invocation of the candidate Browser passive peer."""

from __future__ import annotations

import importlib
import json
import sys
from contextlib import contextmanager
from dataclasses import asdict
from typing import Any, Iterator


def main() -> None:
    sys.path.insert(0, sys.argv[1])
    request = json.load(sys.stdin)
    forbidden: list[str] = []

    def audit(event: str, args: tuple[Any, ...]) -> None:
        if (
            event.startswith(
                (
                    "socket.",
                    "subprocess.",
                    "sqlite3.connect",
                    "os.exec",
                    "os.fork",
                    "os.spawn",
                    "os.posix_spawn",
                )
            )
            or event == "os.system"
        ):
            forbidden.append(event)
            raise PermissionError(event)

    sys.addaudithook(audit)
    credentials = importlib.import_module("browser_runtime.credentials")
    passive = importlib.import_module("browser_runtime.passive_peer")
    effects = importlib.import_module("browser_runtime.effects")
    controls = importlib.import_module("browser_runtime.control_leases")

    def target(fields: dict[str, Any]) -> Any:
        binding = effects.Binding(**fields["binding"])
        return credentials.Target(**(fields | {"binding": binding}))

    selected = target(request["selection"])
    admitted = controls.PassiveStatus(selected, request["deadline"])
    physical = target(request["physical"])
    seen = request["observed_at"]
    calls: list[str] = []
    token = object()

    class Guard:
        @contextmanager
        def acquire(self) -> Iterator[Guard]:
            calls.append("acquire")
            try:
                yield self
            finally:
                calls.append("close")

        def admit(self, ticket: object) -> Any:
            calls.append("admit")
            return admitted if ticket is token else None

        def current(self, grant: object) -> bool:
            calls.append("current")
            return grant is admitted

        def observe(self) -> Any:
            calls.append("observe")
            return None if seen is None else credentials.Observation(physical, seen)

    peer = passive.PassivePeer(Guard(), clock=lambda: request["now"])
    try:
        result = asdict(peer.observe(token, expected=selected))
    except effects.Denied:
        result = {"status": "denied"}
    print(json.dumps({"result": result, "calls": calls, "forbidden": forbidden}))


if __name__ == "__main__":
    main()
