"""Compatibility entry point for active-viewport PCG screenshot visual QA.

The implementation lives in run_pcg_bookmark_visual_qa.py for existing callers,
but this filename matches the current validation route: active viewport first,
optional existing bookmark slots only when requested.
"""

from __future__ import annotations

import json

from run_pcg_bookmark_visual_qa import parse_args, run


if __name__ == "__main__":
    try:
        result = run(parse_args())
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False))
        raise
    print(json.dumps(result, ensure_ascii=False))
