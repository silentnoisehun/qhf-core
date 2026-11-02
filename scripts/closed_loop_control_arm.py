#!/usr/bin/env python3
"""
Classical Control Arm for Closed-Loop GPE Feedback Benchmark.
============================================================
Runs the identical split-step Fourier GPE fluid simulation (50 iterations x 50 steps)
using two rigorous classical control conditions to arbitrate the hardware QPU findings:

  1. 'classical_sim': Ideal unitary simulation + binomial shot noise (1024 shots).
  2. 'random_control': Randomized/shuffled feedback control to test null hypothesis.

Saves structured JSON datasets in measurement_raw/ for direct statistical comparison
against the IBM Heron hardware run.
"""

import argparse
import json
import math
import sys
import time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
RAW_DIR = REPO / "measurement_raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(HERE))

from fluid_sim import FluidSim

def simulate_circuit_counts(a_fluid, f_fluid, phi_fluid, shots=1024, rng=None):
    """Analytically evaluates the 3-qubit entangled circuit with binomial shot noise."""
    if rng is None:
        rng = np.random.default_rng()

    # Analytical probabilities for independent qubit marginals:
    p0 = math.sin(a_fluid / 2.0) ** 2
    theta_1 = 2.0 * math.pi * (f_fluid / 15.0)
    p1 = math.sin(theta_1 / 2.0) ** 2
    theta_2 = phi_fluid * math.pi
    p2 = math.sin(theta_2 / 2.0) ** 2

    # Clip to valid probability bounds [0, 1]
    p0 = min(max(p0, 0.0), 1.0)
    p1 = min(max(p1, 0.0), 1.0)
    p2 = min(max(p2, 0.0), 1.0)

    # Binomial shot sampling
    k0 = rng.binomial(shots, p0)
    k1 = rng.binomial(shots, p1)
    k2 = rng.binomial(shots, p2)

    p_meas_0 = k0 / shots
    p_meas_1 = k1 / shots
    p_meas_2 = k2 / shots

    # Decoding logic identical to closed_loop_gpe_qpu.py
    a_q = 2.0 * math.asin(math.sqrt(min(max(p_meas_0, 0.0), 1.0)))
    f_q = math.asin(math.sqrt(min(max(p_meas_1, 0.0), 1.0))) / math.pi * 15.0
    phi_q = 2.0 * math.asin(math.sqrt(min(max(p_meas_2, 0.0), 1.0))) / math.pi

    return a_q, f_q, phi_q, {"p0": p_meas_0, "p1": p_meas_1, "p2": p_meas_2}

def main():
    parser = argparse.ArgumentParser(description="Classical Control Arm for GPE Closed Loop")
    parser.add_argument("--mode", choices=["classical_sim", "random_control"], default="classical_sim",
                        help="Control arm mode: classical_sim (ideal simulation) or random_control (scrambled feedback)")
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--gpe-steps", type=int, default=50)
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=20261026)
    args = parser.parse_args()

    print("=" * 78)
    print("QOI-CORE :: CLASSICAL CONTROL ARM BENCHMARK")
    print(f"  Mode        : {args.mode}")
    print(f"  Iterations  : {args.iterations}")
    print(f"  GPE Steps   : {args.gpe_steps} / iteration")
    print(f"  Shots       : {args.shots}")
    print(f"  Seed        : {args.seed}")
    print("=" * 78)

    rng = np.random.default_rng(args.seed)
    fluid = FluidSim(seed=args.seed)
    tag = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + f"_{args.mode}"

    log = []
    mode_history = []
    f_q_trajectory = []
    a_q_trajectory = []

    t_start = time.time()
    for it in range(args.iterations):
        t0 = time.time()

        # 1. GPE split-step Fourier propagation
        for _ in range(args.gpe_steps):
            fluid.gpe_step()

        # 2. Extract fluid mode parameters
        mode_argmax, a_fluid, f_fluid, phi_fluid, energies = fluid.extract_modal_parameters()
        mode_history.append(mode_argmax)

        # 3. Control arm execution
        if args.mode == "classical_sim":
            a_q, f_q, phi_q, meta = simulate_circuit_counts(a_fluid, f_fluid, phi_fluid, shots=args.shots, rng=rng)
        elif args.mode == "random_control":
            # Scrambled feedback: random draw from uniform priors
            a_q = float(rng.uniform(0.1, 1.5))
            f_q = float(rng.uniform(0.0, 15.0))
            phi_q = float(rng.uniform(0.0, 1.0))
            meta = {"randomized": True}

        f_q_trajectory.append(f_q)
        a_q_trajectory.append(a_q)

        # 4. Feedback excitation into fluid
        fluid.excite(a_q, f_q, phi_q)
        wall = time.time() - t0

        entry = {
            "iteration": it,
            "mode": args.mode,
            "mode_argmax": mode_argmax,
            "fluid_parameters": {"A": a_fluid, "f": f_fluid, "phi": phi_fluid},
            "control_decoded": {"A": a_q, "f": f_q, "phi": phi_q},
            "wall_seconds": wall,
            "meta": meta
        }
        log.append(entry)
        print(f"[{it+1:02d}/{args.iterations}] Mode #{mode_argmax:02d} | f_fluid={f_fluid:.2f} -> f_ctrl={f_q:.2f} ({wall:.2f}s)")

    total_time = time.time() - t_start
    f_mean = float(np.mean(f_q_trajectory))
    f_std = float(np.std(f_q_trajectory))
    a_mean = float(np.mean(a_q_trajectory))
    a_std = float(np.std(a_q_trajectory))

    summary = {
        "tag": tag,
        "mode": args.mode,
        "iterations": args.iterations,
        "gpe_steps_per_iter": args.gpe_steps,
        "shots": args.shots,
        "total_seconds": total_time,
        "f_q_mean": f_mean,
        "f_q_std": f_std,
        "a_q_mean": a_mean,
        "a_q_std": a_std,
        "mode_sequence": mode_history,
        "log": log
    }

    out_file = RAW_DIR / f"control_arm_summary_{tag}.json"
    with open(out_file, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    print("\n" + "=" * 78)
    print("CONTROL ARM RUN COMPLETED")
    print(f"  Summary saved to : {out_file}")
    print(f"  f_ctrl statistics: mean = {f_mean:.4f} +/- {f_std:.4f}")
    print(f"  A_ctrl statistics: mean = {a_mean:.4f} +/- {a_std:.4f}")
    print(f"  Total runtime    : {total_time:.2f}s")
    print("=" * 78)

if __name__ == "__main__":
    main()
