#!/usr/bin/env python3
"""
c_live_simultaneous kiertekelese: szimultan 5-qubites blokkonkenti d = c_F - c_N.
Amendment 1: Teljes elmeleti es szamitasi konzisztencia az eloregisztracioval.
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
        return 0.5 * math.erfc(t / math.sqrt(2))


def main():
    if len(sys.argv) < 2:
        sys.exit("Add meg a kampany mappajat.")
    d = Path(sys.argv[1])
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("iter*.json"))]
    meta = json.loads((d / "campaign.json").read_text(encoding="utf-8"))

    blocks = {}
    for r in recs:
        counts = r["counts"]
        shots = sum(counts.values())
        n_00 = sum(v for k, v in counts.items() if k[0] == "0" and k[1] == "0")
        n_11 = sum(v for k, v in counts.items() if k[0] == "1" and k[1] == "1")
        c = (n_00 + n_11) / shots
        blocks.setdefault(r["block"], {})[r["arm"]] = c

    complete = sorted(b for b, v in blocks.items() if "F" in v and "N" in v)
    diffs = [blocks[b]["F"] - blocks[b]["N"] for b in complete]
    n = len(diffs)
    if n < 3:
        sys.exit(f"Keves teljes blokk ({n}).")

    mean = sum(diffs) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in diffs) / (n - 1)) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n > 0 else 0.0
    
    if se > 0:
        t = mean / se
        p_one_sided = t_sf(t, n - 1)
        p_two_sided = 2.0 * t_sf(abs(t), n - 1)
    else:
        t = 0.0
        p_one_sided = 1.0 if mean <= 0 else 0.0
        p_two_sided = 1.0 if mean == 0 else 0.0

    half = n // 2
    m1 = sum(diffs[:half]) / max(1, half)
    m2 = sum(diffs[half:]) / max(1, n - half)
    cF = [blocks[b]["F"] for b in complete]
    cN = [blocks[b]["N"] for b in complete]

    # Dontesi szabaly (eloregisztralt egyoldalu H1: a GPE-hurok noveli vagy vedi a Bell-korrelaciot):
    ok1 = mean >= DELTA_MIN
    ok2 = p_one_sided < ALPHA
    ok3 = (m1 > 0 and m2 > 0)
    verdict = "H1 TAMOGATOTT" if (ok1 and ok2 and ok3) else "H1 NEM TAMOGATOTT (a tankonyvi d = 0 all)"

    out = {
        "campaign": meta["campaign"], "backend": meta["backend"], "dry_run": meta["dry_run"],
        "layout": meta["layout"], "complete_blocks": n,
        "mean_c_F": sum(cF) / n, "mean_c_N": sum(cN) / n,
        "mean_diff": mean, "sd_diff": sd, "t": t,
        "p_one_sided": p_one_sided, "p_two_sided": p_two_sided,
        "first_half_mean_diff": m1, "second_half_mean_diff": m2,
        "criteria": {"delta>=0.003": ok1, "p<0.01": ok2, "both_halves_positive": ok3},
        "verdict": verdict,
    }
    (d / "analysis.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
