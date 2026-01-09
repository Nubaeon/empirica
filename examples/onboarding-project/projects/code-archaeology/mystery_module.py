"""
Legacy module - original author unavailable
Last modified: Unknown
Purpose: "Handles data processing" (that's all the docs say)
"""

import json
from collections import defaultdict
from typing import Any


def proc_x(d: list[dict]) -> dict:
    """Process input."""
    r = defaultdict(list)
    for i in d:
        k = i.get("cat", "unk")
        v = i.get("val", 0)
        r[k].append(v)
    return dict(r)


def agg_y(d: dict, m: str = "sum") -> dict:
    """Aggregate values."""
    o = {}
    for k, vs in d.items():
        if m == "sum":
            o[k] = sum(vs)
        elif m == "avg":
            o[k] = sum(vs) / len(vs) if vs else 0
        elif m == "cnt":
            o[k] = len(vs)
        elif m == "max":
            o[k] = max(vs) if vs else 0
        elif m == "min":
            o[k] = min(vs) if vs else 0
    return o


def flt_z(d: list[dict], p: dict) -> list[dict]:
    """Filter records."""
    r = []
    for i in d:
        m = True
        for pk, pv in p.items():
            if pk.startswith("gt_"):
                f = pk[3:]
                if i.get(f, 0) <= pv:
                    m = False
            elif pk.startswith("lt_"):
                f = pk[3:]
                if i.get(f, 0) >= pv:
                    m = False
            elif pk.startswith("eq_"):
                f = pk[3:]
                if i.get(f) != pv:
                    m = False
            elif pk.startswith("in_"):
                f = pk[3:]
                if i.get(f) not in pv:
                    m = False
        if m:
            r.append(i)
    return r


def xform_w(d: list[dict], ops: list[tuple]) -> list[dict]:
    """Transform data."""
    r = []
    for i in d:
        n = dict(i)
        for op in ops:
            if op[0] == "rename" and len(op) == 3:
                if op[1] in n:
                    n[op[2]] = n.pop(op[1])
            elif op[0] == "drop" and len(op) == 2:
                n.pop(op[1], None)
            elif op[0] == "calc" and len(op) == 4:
                a, b = n.get(op[2], 0), n.get(op[3], 0)
                if op[1] == "+":
                    n["_calc"] = a + b
                elif op[1] == "-":
                    n["_calc"] = a - b
                elif op[1] == "*":
                    n["_calc"] = a * b
                elif op[1] == "/":
                    n["_calc"] = a / b if b != 0 else 0
        r.append(n)
    return r


def pipe_main(src: str, cfg: dict) -> Any:
    """Main pipeline entry."""
    with open(src) as f:
        d = json.load(f)

    if "filter" in cfg:
        d = flt_z(d, cfg["filter"])

    if "transform" in cfg:
        d = xform_w(d, cfg["transform"])

    if "group" in cfg:
        d = proc_x(d)
        if "agg" in cfg:
            d = agg_y(d, cfg["agg"])

    return d


# Entry point
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python mystery_module.py <input.json> [config.json]")
        sys.exit(1)

    src = sys.argv[1]
    cfg = {}
    if len(sys.argv) > 2:
        with open(sys.argv[2]) as f:
            cfg = json.load(f)

    result = pipe_main(src, cfg)
    print(json.dumps(result, indent=2))
