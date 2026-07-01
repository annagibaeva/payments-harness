from __future__ import annotations

import json
from pathlib import Path

from .types import Response


def key(task_id: str, run: int, config_hash: str) -> str:
    return f"{config_hash}:{task_id}:{run}"


def load(path: Path, config_hash: str) -> dict[str, Response]:
    """Return recorded responses for this config_hash, keyed by `key`."""
    out: dict[str, Response] = {}
    if not Path(path).exists():
        return out
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("config_hash") != config_hash:
                continue
            resp = Response(**{k: v for k, v in row.items() if k != "config_hash"})
            out[key(resp.task_id, resp.run, config_hash)] = resp
    return out


def append(path: Path, response: Response, config_hash: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    row = response.model_dump()
    row["config_hash"] = config_hash
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
