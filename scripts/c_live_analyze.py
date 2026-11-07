#!/usr/bin/env python3
"""
c_live teszt kiertekelese, pontosan az elozetesen regisztralt szabaly szerint.

Hasznalat: python scripts/c_live_analyze.py measurement_raw/c_live/<kampany>

Elsodleges teszt: blokkonkenti kulonbseg d = c_F - c_N, egyoldalu paros t-teszt (H1: atlag d > 0).
H1 TAMOGATOTT, ha MINDHAROM teljesul:
  1. atlag d >= 0.003
  2. egyoldalu p < 0.01
  3. az elso es a masodik fel kulon-kulon is pozitiv atlagu d-t ad (replikacio a kampanyon belul)
Minden mas eset: H1 NEM tamogatott (a tankonyvi joslat, d = 0, all).
"""

import json
import math
import sys
from pathlib import Path

DELTA_MIN = 0.003
ALPHA = 0.01


def t_sf(t, df):
    try:
        from scipy import stats
        return float(stats.t.sf(t, df))
    except Exception:
        return 0.5 * math.erfc(t / math.sqrt(2))  # normalis kozelites


def main():
    if len(sys.argv) < 2:
        sys.exit("Add meg a kampany mappajat.")
    d = Path(sys.argv[1])
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("iter*.json"))]
    meta = json.loads((d / "campaign.json").read_text(encoding="utf-8"))

    blocks = {}
    for r in recs:
        shots = sum(r["counts_bell"].values())
        c = (r["counts_bell"].get("00", 0) + r["counts_bell"].get("11", 0)) / shots  # ujraszamolva a countsbol
        blocks.setdefault(r["block"], {})[r["arm"]] = c

    complete = sorted(b for b, v in blocks.items() if "F" in v and "N" in v)
    diffs = [blocks[b]["F"] - blocks[b]["N"] for b in complete]
    n = len(diffs)
    if n < 3:
        sys.exit(f"Keves teljes blokk ({n}).")

    mean = sum(diffs) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in diffs) / (n - 1))
    se = sd / math.sqrt(n)
    t = mean / se if se > 0 else float("inf")
    p = t_sf(t, n - 1)
    half = n // 2
    m1 = sum(diffs[:half]) / max(1, half)
    m2 = sum(diffs[half:]) / max(1, n - half)
    cF = [blocks[b]["F"] for b in complete]
    cN = [blocks[b]["N"] for b in complete]

    ok1, ok2, ok3 = mean >= DELTA_MIN, p < ALPHA, (m1 > 0 and m2 > 0)
    verdict = "H1 TAMOGATOTT" if (ok1 and ok2 and ok3) else "H1 NEM TAMOGATOTT (a tankonyvi d = 0 all)"

    out = {
        "campaign": meta["campaign"], "backend": meta["backend"], "dry_run": meta["dry_run"],
        "bell_layout": meta["bell_layout"], "complete_blocks": n,
        "mean_c_F": sum(cF) / n, "mean_c_N": sum(cN) / n,
        "mean_diff": mean, "sd_diff": sd, "t": t, "p_one_sided": p,
        "first_half_mean_diff": m1, "second_half_mean_diff": m2,
        "criteria": {"delta>=0.003": ok1, "p<0.01": ok2, "both_halves_positive": ok3},
        "verdict": verdict,
    }
    (d / "analysis.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
