#!/usr/bin/env python3
"""
angle_calibration.py — Angle-Resolved SPAM Calibration & Coherent Over-rotation Test on Heron QPU.

Preregistration: docs/PREREGISTRATION-angle_calibration.md
Author: Máté Róbert (ORCID 0009-0003-3986-6039)
Repository: https://github.com/silentnoisehun/qhf-bell-spectator
"""

import argparse
import datetime
import json
import math
import sys
import time
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

ANGLES = [
    0.0,
    math.pi / 6.0,
    math.pi / 4.0,
    math.pi / 3.0,
    math.pi / 2.0,
    2.0 * math.pi / 3.0,
    3.0 * math.pi / 4.0,
    5.0 * math.pi / 6.0,
    math.pi
]

ANGLE_LABELS = [
    "0",
    "pi/6",
    "pi/4",
    "pi/3",
    "pi/2",
    "2pi/3",
    "3pi/4",
    "5pi/6",
    "pi"
]

def parse_args():
    parser = argparse.ArgumentParser(description="Angle-Resolved SPAM Calibration Test")
    parser.add_argument("--token-file", default=r"C:\Users\mater\Downloads\apikey (5).json")
    parser.add_argument("--backend", default="ibm_marrakesh", choices=["ibm_marrakesh", "ibm_kingston"])
    parser.add_argument("--qubits", type=int, nargs="+", default=None)
    parser.add_argument("--shots", type=int, default=4096)
    parser.add_argument("--dry-run", action="store_true", help="Local simulation without QPU hardware")
    return parser.parse_args()

def extract_p1_marginals(counts, shots):
    """
    Given Qiskit counts dictionary where bitstring is e.g. '010' (bit[2] is q0, bit[1] is q1, bit[0] is q2),
    returns [p(1)_q0, p(1)_q1, p(1)_q2].
    """
    ones = [0.0, 0.0, 0.0]
    total = 0
    for bstr, c in counts.items():
        s = bstr.replace(" ", "")
        total += c
        for q in range(3):
            bit_idx = len(s) - 1 - q
            if bit_idx >= 0 and s[bit_idx] == '1':
                ones[q] += c
    denom = total if total > 0 else shots
    return [c_val / denom for c_val in ones]

def build_circuit(mode, theta, target_q=None):
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(3, 3)
    if mode == "isolated":
        qc.ry(theta, target_q)
    elif mode == "simultaneous":
        qc.ry(theta, 0)
        qc.ry(theta, 1)
        qc.ry(theta, 2)
    qc.measure([0, 1, 2], [0, 1, 2])
    return qc

def main():
    args = parse_args()
    
    if args.qubits is None:
        if args.backend == "ibm_marrakesh":
            args.qubits = [53, 54, 55]
        else:
            args.qubits = [48, 49, 50]

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = REPO / "measurement_raw" / "angle_calibration" / f"{timestamp}_{args.backend}"
    run_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("PHASE 5: ANGLE-RESOLVED SPAM CALIBRATION & COHERENT OVER-ROTATION TEST")
    print(f"Backend: {args.backend} | Qubits: {args.qubits} | Shots: {args.shots}")
    print(f"Token file: {args.token_file} | Mode: {'DRY RUN' if args.dry_run else 'LIVE QPU'}")
    print(f"Output directory: {run_dir}")
    print("=" * 70)

    # 1. Build the 36 circuits
    circuits = []
    metadata = []
    
    # 9 angles x (3 isolated + 1 simultaneous) = 36 circuits
    for a_idx, (th, label) in enumerate(zip(ANGLES, ANGLE_LABELS)):
        for q_target in range(3):
            circuits.append(build_circuit("isolated", th, target_q=q_target))
            metadata.append({
                "mode": "isolated",
                "angle_idx": a_idx,
                "theta": th,
                "label": label,
                "target_q": q_target
            })
        circuits.append(build_circuit("simultaneous", th))
        metadata.append({
            "mode": "simultaneous",
            "angle_idx": a_idx,
            "theta": th,
            "label": label,
            "target_q": "all"
        })

    print(f"Built {len(circuits)} circuits (9 angles x [3 isolated + 1 simultaneous]).")

    # 2. Setup backend & transpile
    start_wall = time.time()
    cal_timestamp = None

    if not args.dry_run:
        with open(args.token_file, encoding="utf-8") as f:
            key_data = json.load(f)
        token = key_data.get("apikey") or key_data.get("token")

        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
        from qiskit import transpile

        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance="open-instance")
        backend = service.backend(args.backend)
        props = backend.properties(refresh=True)
        cal_timestamp = str(props.last_update_date) if props else "unknown"

        print(f"Connected to {args.backend}. Last calibration: {cal_timestamp}")
        print("Transpiling 36 circuits onto physical layout...")
        isa_circuits = [transpile(c, backend=backend, initial_layout=args.qubits, optimization_level=1) for c in circuits]

        print("Submitting batch job to QPU...")
        sampler = SamplerV2(backend)
        job = sampler.run(isa_circuits, shots=args.shots)
        job_id = job.job_id()
        print(f"Job ID: {job_id} | Status: {job.status()} | Waiting for execution...")

        result = job.result()
        print(f"Job {job_id} completed successfully!")
        counts_list = [result[i].data.c.get_counts() for i in range(len(circuits))]
    else:
        from qiskit_aer import AerSimulator
        from qiskit import transpile
        backend = AerSimulator()
        isa_circuits = [transpile(c, backend=backend, optimization_level=1) for c in circuits]
        job = backend.run(isa_circuits, shots=args.shots)
        job_id = "dryrun_phase5_job"
        result = job.result()
        counts_list = [result.get_counts(c) for c in isa_circuits]
        cal_timestamp = "dryrun_sim"

    total_wall = time.time() - start_wall

    # 3. Save raw counts
    raw_data = {
        "job_id": job_id,
        "backend": args.backend,
        "physical_qubits": args.qubits,
        "calibration_timestamp": cal_timestamp,
        "shots": args.shots,
        "circuits": []
    }
    for i, meta in enumerate(metadata):
        raw_data["circuits"].append({
            "index": i,
            "mode": meta["mode"],
            "angle_idx": meta["angle_idx"],
            "theta": meta["theta"],
            "label": meta["label"],
            "target_q": meta["target_q"],
            "counts": counts_list[i]
        })

    with open(run_dir / "raw_counts.json", "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2)

    # 4. Extract marginals and perform analysis
    # Organize data: p1_iso[q][angle_idx], p1_sim[q][angle_idx]
    p1_iso = {0: [0.0]*9, 1: [0.0]*9, 2: [0.0]*9}
    p1_sim = {0: [0.0]*9, 1: [0.0]*9, 2: [0.0]*9}

    for i, meta in enumerate(metadata):
        p1 = extract_p1_marginals(counts_list[i], args.shots)
        a_idx = meta["angle_idx"]
        if meta["mode"] == "isolated":
            t_q = meta["target_q"]
            p1_iso[t_q][a_idx] = p1[t_q]
        elif meta["mode"] == "simultaneous":
            for q in range(3):
                p1_sim[q][a_idx] = p1[q]

    analysis = {
        "backend": args.backend,
        "qubits": args.qubits,
        "job_id": job_id,
        "calibration_timestamp": cal_timestamp,
        "angles": ANGLES,
        "angle_labels": ANGLE_LABELS,
        "qubit_analysis": {}
    }

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append(f"PHASE 5 ANALYSIS: {args.backend} (Qubits: {args.qubits})")
    report_lines.append(f"Job ID: {job_id} | Calibration: {cal_timestamp} | Shots: {args.shots}")
    report_lines.append("=" * 80)

    for q in range(3):
        phys_q = args.qubits[q]
        # Empirical readout errors at poles from isolated mode
        # theta = 0 -> p(1|0) = eps0
        # theta = pi -> p(0|1) = 1 - p(1|pi) = eps1
        eps0 = p1_iso[q][0]
        eps1 = 1.0 - p1_iso[q][8]

        # Model 0: Pure readout baseline across all 9 angles
        # p0(theta) = (1 - eps1)*sin^2(theta/2) + eps0*cos^2(theta/2)
        p0_curve = [(1.0 - eps1)*(math.sin(th/2.0)**2) + eps0*(math.cos(th/2.0)**2) for th in ANGLES]
        
        # Residuals
        res_iso = [p1_iso[q][k] - p0_curve[k] for k in range(9)]
        res_sim = [p1_sim[q][k] - p0_curve[k] for k in range(9)]
        crosstalk = [p1_sim[q][k] - p1_iso[q][k] for k in range(9)]

        # Fit Model 1: delta_theta * 0.5 * sin(theta) to res_iso
        # Linear least squares: delta_theta = sum(res * sin(th)) / (0.5 * sum(sin^2(th)))
        sin_th = np.array([math.sin(th) for th in ANGLES])
        y = np.array(res_iso)
        x = 0.5 * sin_th
        denom = np.sum(x**2)
        delta_theta_fit = np.sum(x * y) / denom if denom > 1e-12 else 0.0
        
        # Goodness-of-fit R^2
        y_pred = delta_theta_fit * x
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-12 else 0.0

        delta_theta_deg = math.degrees(delta_theta_fit)

        analysis["qubit_analysis"][f"Q{phys_q}"] = {
            "phys_qubit": phys_q,
            "logical_idx": q,
            "eps0": eps0,
            "eps1": eps1,
            "p1_isolated": p1_iso[q],
            "p1_simultaneous": p1_sim[q],
            "p0_model": p0_curve,
            "residuals_isolated": res_iso,
            "residuals_simultaneous": res_sim,
            "crosstalk_diff": crosstalk,
            "fitted_delta_theta_rad": float(delta_theta_fit),
            "fitted_delta_theta_deg": float(delta_theta_deg),
            "sin_model_r2": float(r2),
            "peak_midpoint_residual_iso": float(res_iso[4]), # theta = pi/2
            "peak_midpoint_residual_sim": float(res_sim[4])
        }

        report_lines.append(f"\n--- Transmon Q{phys_q} (logical q{q}) ---")
        report_lines.append(f"Poles Readout Errors: eps0 = {eps0:.4f} ({eps0*100:.2f}%), eps1 = {eps1:.4f} ({eps1*100:.2f}%)")
        report_lines.append(f"Fitted Coherent Over-rotation: delta_theta = {delta_theta_fit:+.5f} rad ({delta_theta_deg:+.2f} deg) | R^2 = {r2:.4f}")
        report_lines.append(f"Midpoint (pi/2) Residual: Iso = {res_iso[4]:+.5f}, Sim = {res_sim[4]:+.5f} (Cross-talk diff = {crosstalk[4]:+.5f})")
        report_lines.append(f"{'Angle':>8} | {'Ideal':>7} | {'Model 0':>8} | {'P1_Iso':>8} | {'Res_Iso':>8} | {'P1_Sim':>8} | {'Res_Sim':>8} | {'CrossTalk':>9}")
        report_lines.append("-" * 84)
        for k in range(9):
            ideal = math.sin(ANGLES[k]/2.0)**2
            report_lines.append(
                f"{ANGLE_LABELS[k]:>8} | {ideal:7.4f} | {p0_curve[k]:8.4f} | {p1_iso[q][k]:8.4f} | {res_iso[k]:+8.4f} | "
                f"{p1_sim[q][k]:8.4f} | {res_sim[k]:+8.4f} | {crosstalk[k]:+9.4f}"
            )

    report_text = "\n".join(report_lines)
    print(report_text)

    with open(run_dir / "analysis.json", "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)

    with open(run_dir / "report.txt", "w", encoding="utf-8") as f:
        f.write(report_text + "\n")

    campaign_meta = {
        "preregistration": "docs/PREREGISTRATION-angle_calibration.md",
        "backend": args.backend,
        "physical_qubits": args.qubits,
        "shots": args.shots,
        "job_id": job_id,
        "calibration_timestamp": cal_timestamp,
        "timestamp": timestamp,
        "wall_time_seconds": total_wall
    }
    with open(run_dir / "campaign.json", "w", encoding="utf-8") as f:
        json.dump(campaign_meta, f, indent=2)

    print(f"\nAll data and analysis written to {run_dir}")

if __name__ == "__main__":
    main()
