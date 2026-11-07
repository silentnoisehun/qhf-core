#!/usr/bin/env python3
"""
qpu_vs_rng_analyze.py — Statistical analysis according to PREREGISTRATION-qpu_vs_rng.md

Author: Máté Róbert (ORCID 0009-0003-3986-6039)
Repository: https://github.com/silentnoisehun/qhf-bell-spectator
"""

import argparse
import glob
import json
import math
import sys
from pathlib import Path
import numpy as np

def circular_std(phi_list):
    """Compute circular standard deviation for angles in [0, 1) mapped to [0, 2*pi)."""
    angles = np.array(phi_list) * 2.0 * math.pi
    C = np.mean(np.cos(angles))
    S = np.mean(np.sin(angles))
    R = math.hypot(C, S)
    if R < 1e-12:
        return math.pi / math.sqrt(3)  # Uniform circular std
    R = min(1.0, R)
    return math.sqrt(max(0.0, -2.0 * math.log(R)))

def lag1_autocorr(series):
    """Compute lag-1 sample autocorrelation."""
    x = np.array(series, dtype=float)
    if len(x) < 3:
        return 0.0
    x_centered = x - np.mean(x)
    var = np.sum(x_centered ** 2)
    if var < 1e-15:
        return 0.0
    autocov = np.sum(x_centered[:-1] * x_centered[1:])
    return float(autocov / var)

def exact_sign_flip_p_value(diffs):
    """
    Exact two-sided sign-flip permutation test for 2^N sign assignments.
    diffs: array of length N (e.g. N = 20 -> 1,048,576 combinations).
    """
    d = np.array(diffs, dtype=float)
    N = len(d)
    obs_mean = abs(np.mean(d))
    if obs_mean < 1e-14:
        return 1.0

    # Fast subset-sum sign flips via vectorized binary combinations
    # d is 20 elements. 2^20 = 1,048,576
    # Instead of full matrix in RAM, sum in chunks of 2^10 = 1024
    signs_half1 = np.array([[1 if (i & (1 << j)) else -1 for j in range(10)] for i in range(1024)], dtype=float)
    signs_half2 = np.array([[1 if (i & (1 << j)) else -1 for j in range(N - 10)] for i in range(1 << (N - 10))], dtype=float)

    sums1 = signs_half1 @ d[:10]  # shape (1024,)
    sums2 = signs_half2 @ d[10:]  # shape (1024,)

    # Outer sum: all 2^20 totals
    all_sums = (sums1[:, None] + sums2[None, :]).ravel()
    all_means = all_sums / N

    extreme_count = np.sum(np.abs(all_means) >= (obs_mean - 1e-12))
    p_val = float(extreme_count / (2 ** N))
    return p_val

def main():
    parser = argparse.ArgumentParser(description="Analyze QPU vs RNG Campaign")
    parser.add_argument("campaign_dir", type=str, help="Path to campaign directory")
    parser.add_argument("--burn-in", type=int, default=10, help="Burn-in iterations to discard (default 10)")
    args = parser.parse_args()

    campaign_path = Path(args.campaign_dir)
    campaign_file = campaign_path / "campaign.json"

    if not campaign_file.exists():
        print(f"Error: {campaign_file} not found.")
        sys.exit(1)

    with open(campaign_file, encoding="utf-8") as f:
        meta = json.load(f)

    iter_files = sorted(campaign_path.glob("iter*.json"))
    num_iters = len(iter_files)
    if num_iters < 13:
        print(f"Error: Only {num_iters} iterations found (minimum 13 required).")
        sys.exit(1)

    print("=" * 78)
    print("QPU vs NOISE-MATCHED RNG STATISTICAL ANALYSIS")
    print(f"  Campaign        : {meta.get('tag')}")
    print(f"  Backend         : {meta.get('backend')}")
    print(f"  Iterations found: {num_iters} (burn-in: {args.burn_in})")
    print(f"  Calibration start: {meta.get('calibration_start')}")
    print(f"  Calibration end  : {meta.get('calibration_end')}")
    print("=" * 78)

    # Load all iterations
    data_by_iter = []
    for fpath in iter_files:
        with open(fpath, encoding="utf-8") as f:
            data_by_iter.append(json.load(f))

    # Evaluate window: iterations burn_in to end
    eval_iters = [d for d in data_by_iter if d["iteration"] >= args.burn_in]
    num_eval = len(eval_iters)
    print(f"Evaluating {num_eval} iterations (iters {args.burn_in} to {data_by_iter[-1]['iteration']})")

    num_replicates = meta.get("replicates", 20)

    # Accumulate per replicate: time series of f, A, phi
    f_Q = {r: [] for r in range(num_replicates)}
    f_C = {r: [] for r in range(num_replicates)}
    A_Q = {r: [] for r in range(num_replicates)}
    A_C = {r: [] for r in range(num_replicates)}
    phi_Q = {r: [] for r in range(num_replicates)}
    phi_C = {r: [] for r in range(num_replicates)}

    for entry in eval_iters:
        for rep in entry["replicates"]:
            r = rep["replicate"]
            f_Q[r].append(rep["arm_Q"]["fluid_params"]["f"])
            f_C[r].append(rep["arm_C"]["fluid_params"]["f"])
            A_Q[r].append(rep["arm_Q"]["fluid_params"]["A"])
            A_C[r].append(rep["arm_C"]["fluid_params"]["A"])
            phi_Q[r].append(rep["arm_Q"]["fluid_params"]["phi"])
            phi_C[r].append(rep["arm_C"]["fluid_params"]["phi"])

    # 1. PRIMARY METRIC: D_r = mean(f_Q) - mean(f_C)
    D_f = np.array([np.mean(f_Q[r]) - np.mean(f_C[r]) for r in range(num_replicates)])
    mean_D_f = float(np.mean(D_f))
    sd_D_f = float(np.std(D_f, ddof=1))

    # Halves check: replicates 0..9 and 10..19
    half1_mean = float(np.mean(D_f[:10]))
    half2_mean = float(np.mean(D_f[10:]))
    same_sign = (half1_mean * half2_mean > 0)

    # Exact sign-flip permutation test
    p_perm_f = exact_sign_flip_p_value(D_f)

    # Decision rule
    h1_supported = (p_perm_f < 0.01) and same_sign

    # 2. SECONDARY METRICS
    # A) Mean amplitude A
    D_A = np.array([np.mean(A_Q[r]) - np.mean(A_C[r]) for r in range(num_replicates)])
    mean_D_A = float(np.mean(D_A))
    p_perm_A = exact_sign_flip_p_value(D_A)

    # B) Circular standard deviation of phi
    D_phi = np.array([circular_std(phi_Q[r]) - circular_std(phi_C[r]) for r in range(num_replicates)])
    mean_D_phi = float(np.mean(D_phi))
    p_perm_phi = exact_sign_flip_p_value(D_phi)

    # C) Lag-1 autocorrelation of f
    D_autocorr = np.array([lag1_autocorr(f_Q[r]) - lag1_autocorr(f_C[r]) for r in range(num_replicates)])
    mean_D_autocorr = float(np.mean(D_autocorr))
    p_perm_autocorr = exact_sign_flip_p_value(D_autocorr)

    print("\nPRIMARY ANALYSIS (Metric: Mode centroid f)")
    print(f"  Mean D(f)           : {mean_D_f:+.5f}")
    print(f"  SD D(f)             : {sd_D_f:.5f}")
    print(f"  Half 1 (rep 0..9)   : {half1_mean:+.5f}")
    print(f"  Half 2 (rep 10..19) : {half2_mean:+.5f}")
    print(f"  Halves sign match   : {same_sign}")
    print(f"  Permutation p-value : {p_perm_f:.6f} (threshold: < 0.01)")
    print(f"  DECISION            : {'H1 SUPPORTED' if h1_supported else 'H1 NOT SUPPORTED (Standard QM Textbook Holds)'}")

    print("\nSECONDARY ANALYSES (Reported, non-decisive)")
    print(f"  Mean D(A)           : {mean_D_A:+.5f} (p = {p_perm_A:.4f})")
    print(f"  Mean D(circ_sd_phi) : {mean_D_phi:+.5f} (p = {p_perm_phi:.4f})")
    print(f"  Mean D(autocorr_f)  : {mean_D_autocorr:+.5f} (p = {p_perm_autocorr:.4f})")

    analysis_result = {
        "preregistration": "docs/PREREGISTRATION-qpu_vs_rng.md",
        "campaign_dir": str(campaign_path),
        "total_iterations": num_iters,
        "evaluated_iterations": num_eval,
        "burn_in": args.burn_in,
        "num_replicates": num_replicates,
        "primary": {
            "metric": "centroid_frequency_f",
            "mean_D": mean_D_f,
            "sd_D": sd_D_f,
            "replicate_diffs": D_f.tolist(),
            "half1_mean_rep0_9": half1_mean,
            "half2_mean_rep10_19": half2_mean,
            "same_sign_halves": bool(same_sign),
            "exact_permutation_p": p_perm_f,
            "h1_supported": bool(h1_supported)
        },
        "secondary": {
            "amplitude_A": {
                "mean_D": mean_D_A,
                "permutation_p": p_perm_A
            },
            "circular_std_phi": {
                "mean_D": mean_D_phi,
                "permutation_p": p_perm_phi
            },
            "autocorr_lag1_f": {
                "mean_D": mean_D_autocorr,
                "permutation_p": p_perm_autocorr
            }
        },
        "conclusion": "H1 SUPPORTED" if h1_supported else "H1 NOT SUPPORTED: No statistically significant difference between QPU-fed and noise-matched classical RNG-fed Gross-Pitaevskii fluids beyond textbook shot noise and readout error."
    }

    out_file = campaign_path / "analysis.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, indent=2)
    print(f"\nAnalysis saved to {out_file}")

if __name__ == "__main__":
    main()
