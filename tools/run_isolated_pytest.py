from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.run_release_acceptance import _run_pytest_selection


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()
    result = _run_pytest_selection(args.root.resolve(), [args.selection], timeout_seconds=args.timeout)
    result["selection"] = args.selection
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
