#!/usr/bin/env python3
"""
qpu_vs_rng.py — Does a QPU-fed Gross–Pitaevskii fluid behave differently
from a fluid fed by a noise-matched classical random generator?

Preregistration: docs/PREREGISTRATION-qpu_vs_rng.md
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
sys.path.insert(0, str(HERE))

from fluid_sim import FluidSim

def parse_args():
    parser = argparse.ArgumentParser(description="QPU vs Noise-Matched RNG GPE Fluid Experiment")
    parser.add_argument("--token-file", default=r"C:\Users\mater\Downloads\apikey (2).json")
    parser.add_argument("--backend", default="ibm_marrakesh")
    parser.add_argument("--replicates", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=40)
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--gpe-steps", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20261108)
    parser.add_argument("--qubits", type=int, nargs="+", default=[51, 52, 53])
    parser.add_argument("--dry-run", action="store_true", help="Local simulation without QPU hardware")
    return parser.parse_args()

def build_q_circuit(a_fluid, f_fluid, phi_fluid):
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(3, 3)
    qc.ry(a_fluid, 0)
    qc.ry(2.0 * math.pi * (f_fluid / 15.0), 1)
    qc.ry(phi_fluid * math.pi, 2)
    qc.measure([0, 1, 2], [0, 1, 2])
    return qc

def build_cal0_circuit():
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(3, 3)
    qc.measure([0, 1, 2], [0, 1, 2])
    return qc

def build_cal1_circuit():
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(3, 3)
    qc.x([0, 1, 2])
    qc.measure([0, 1, 2], [0, 1, 2])
    return qc

def extract_marginals(counts, shots):
    """Qiskit bitstring: bit[2] is q0, bit[1] is q1, bit[0] is q2."""
    p = [0.0, 0.0, 0.0]
    for bitstring, c in counts.items():
        s = bitstring.replace(" ", "")
        for q in range(3):
            bit_idx = 2 - q
            if bit_idx < len(s) and s[bit_idx] == '1':
                p[q] += c
    return [c_val / shots for c_val in p]

def decode_quantum_parameters(p_marginals):
    p0 = max(0.0, min(1.0, p_marginals[0]))
    p1 = max(0.0, min(1.0, p_marginals[1]))
    p2 = max(0.0, min(1.0, p_marginals[2]))

    a_q = 2.0 * math.asin(math.sqrt(p0))
    f_q = (15.0 / math.pi) * math.asin(math.sqrt(p1))
    phi_q = (2.0 / math.pi) * math.asin(math.sqrt(p2))
    return a_q, f_q, phi_q

def main():
    args = parse_args()
    tag = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    campaign_dir = REPO / "measurement_raw" / "qpu_vs_rng" / tag
    campaign_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("QPU vs NOISE-MATCHED RNG GPE FLUID CLOSED-LOOP EXPERIMENT")
    print(f"  Preregistration : docs/PREREGISTRATION-qpu_vs_rng.md")
    print(f"  Backend         : {args.backend if not args.dry_run else 'DRY-RUN (AerSimulator)'}")
    print(f"  Physical Qubits : {args.qubits}")
    print(f"  Replicates (R)  : {args.replicates}")
    print(f"  Iterations      : {args.iterations}")
    print(f"  Shots / Circuit : {args.shots}")
    print(f"  GPE steps / It  : {args.gpe_steps}")
    print(f"  Base Seed       : {args.seed}")
    print(f"  Campaign Dir    : {campaign_dir}")
    print("=" * 78)

    backend = None
    cal_start = None
    cal_snapshot = {}

    if not args.dry_run:
        from qiskit import transpile
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
        with open(args.token_file, encoding="utf-8") as f:
            key_data = json.load(f)
        token = key_data.get("apikey") or key_data.get("token")
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token, instance="open-instance")
        backend = service.backend(args.backend)
        props = backend.properties(refresh=True)
        cal_start = str(props.last_update_date) if props else "unknown"
        print(f"Connected to QPU: {backend.name} ({backend.num_qubits} qubits)")
        print(f"Backend calibration timestamp: {cal_start}")

        if props:
            for q in args.qubits:
                ro_err = props.readout_error(q)
                t1 = props.t1(q)
                t2 = props.t2(q)
                cal_snapshot[f"q{q}"] = {
                    "readout_error": ro_err,
                    "t1_us": t1 * 1e6 if t1 else None,
                    "t2_us": t2 * 1e6 if t2 else None
                }
    else:
        from qiskit import transpile
        from qiskit_aer import AerSimulator
        backend = AerSimulator()
        cal_start = "dry_run_simulation"
        print("Dry run initialized with AerSimulator.")

    # Initialize paired fluids: Q and C for each replicate
    fluids_Q = [FluidSim(seed=args.seed + r) for r in range(args.replicates)]
    fluids_C = [FluidSim(seed=args.seed + r) for r in range(args.replicates)]
    rng_classical = np.random.default_rng(args.seed + 99999)

    campaign_meta = {
        "preregistration": "docs/PREREGISTRATION-qpu_vs_rng.md",
        "tag": tag,
        "backend": args.backend if not args.dry_run else "AerSimulator (dry-run)",
        "physical_qubits": args.qubits,
        "replicates": args.replicates,
        "iterations": args.iterations,
        "shots": args.shots,
        "gpe_steps_per_iter": args.gpe_steps,
        "seed": args.seed,
        "dry_run": args.dry_run,
        "calibration_start": cal_start,
        "calibration_snapshot": cal_snapshot,
        "start_time": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    with open(campaign_dir / "campaign.json", "w", encoding="utf-8") as f:
        json.dump(campaign_meta, f, indent=2)

    t_start = time.time()

    for it in range(args.iterations):
        t_it = time.time()

        # Step fluids: 50 GPE steps for all Q and C fluids
        for r in range(args.replicates):
            for _ in range(args.gpe_steps):
                fluids_Q[r].gpe_step()
                fluids_C[r].gpe_step()

        # Extract modal parameters
        q_params = []
        c_params = []
        for r in range(args.replicates):
            m_q, a_q, f_q, phi_q, _ = fluids_Q[r].extract_modal_parameters()
            m_c, a_c, f_c, phi_c, _ = fluids_C[r].extract_modal_parameters()
            q_params.append((m_q, a_q, f_q, phi_q))
            c_params.append((m_c, a_c, f_c, phi_c))

        # Build 20 circuits for Q fluids + 2 calibration circuits (|000> and |111>)
        circuits = []
        for r in range(args.replicates):
            _, a_q, f_q, phi_q = q_params[r]
            circuits.append(build_q_circuit(a_q, f_q, phi_q))
        circuits.append(build_cal0_circuit())
        circuits.append(build_cal1_circuit())

        # Transpile onto physical layout
        if not args.dry_run:
            from qiskit_ibm_runtime import SamplerV2
            isa_circuits = [transpile(c, backend=backend, initial_layout=args.qubits, optimization_level=1) for c in circuits]
            sampler = SamplerV2(backend)
            job = sampler.run(isa_circuits, shots=args.shots)
            job_id = job.job_id()
            result = job.result()
            counts_list = [result[i].data.c.get_counts() for i in range(len(circuits))]
        else:
            isa_circuits = [transpile(c, backend=backend, optimization_level=1) for c in circuits]
            job = backend.run(isa_circuits, shots=args.shots)
            job_id = f"dryrun_job_{it:04d}"
            result = job.result()
            counts_list = [result.get_counts(c) for c in isa_circuits]

        # Extract calibration readout errors from cal0 and cal1
        cal0_counts = counts_list[args.replicates]
        cal1_counts = counts_list[args.replicates + 1]
        p_1_given_0 = extract_marginals(cal0_counts, args.shots)
        p_1_given_1 = extract_marginals(cal1_counts, args.shots)
        p_0_given_1 = [1.0 - p for p in p_1_given_1]

        replicates_data = []

        # Process each replicate
        for r in range(args.replicates):
            # Arm Q: decode from physical QPU measurement
            q_counts = counts_list[r]
            p_meas_q = extract_marginals(q_counts, args.shots)
            a_q_dec, f_q_dec, phi_q_dec = decode_quantum_parameters(p_meas_q)
            fluids_Q[r].excite(a_q_dec, f_q_dec, phi_q_dec)

            # Arm C: ideal probabilities distorted with in-situ measured readout error
            _, a_c, f_c, phi_c = c_params[r]
            p_ideal_c = [
                math.sin(a_c / 2.0) ** 2,
                math.sin(math.pi * f_c / 15.0) ** 2,
                math.sin(math.pi * phi_c / 2.0) ** 2
            ]

            p_dist_c = []
            k_sampled_c = []
            p_sampled_c = []
            for q_idx in range(3):
                p_id = p_ideal_c[q_idx]
                p10 = p_1_given_0[q_idx]
                p01 = p_0_given_1[q_idx]
                p_dist = p_id * (1.0 - p01) + (1.0 - p_id) * p10
                p_dist = max(0.0, min(1.0, p_dist))
                p_dist_c.append(p_dist)
                k = int(rng_classical.binomial(n=args.shots, p=p_dist))
                k_sampled_c.append(k)
                p_sampled_c.append(k / args.shots)

            a_c_dec, f_c_dec, phi_c_dec = decode_quantum_parameters(p_sampled_c)
            fluids_C[r].excite(a_c_dec, f_c_dec, phi_c_dec)

            replicates_data.append({
                "replicate": r,
                "arm_Q": {
                    "fluid_params": {"A": q_params[r][1], "f": q_params[r][2], "phi": q_params[r][3]},
                    "counts": q_counts,
                    "p_meas": p_meas_q,
                    "decoded": {"A": a_q_dec, "f": f_q_dec, "phi": phi_q_dec}
                },
                "arm_C": {
                    "fluid_params": {"A": c_params[r][1], "f": c_params[r][2], "phi": c_params[r][3]},
                    "p_ideal": p_ideal_c,
                    "p_distorted": p_dist_c,
                    "k_sampled": k_sampled_c,
                    "p_sampled": p_sampled_c,
                    "decoded": {"A": a_c_dec, "f": f_c_dec, "phi": phi_c_dec}
                }
            })

        it_entry = {
            "iteration": it,
            "job_id": job_id,
            "wall_seconds": time.time() - t_it,
            "cal_readout_errors": {
                f"q{args.qubits[q_idx]}": {
                    "p_1_given_0": p_1_given_0[q_idx],
                    "p_0_given_1": p_0_given_1[q_idx]
                } for q_idx in range(3)
            },
            "replicates": replicates_data
        }

        with open(campaign_dir / f"iter{it:04d}_{job_id}.json", "w", encoding="utf-8") as f:
            json.dump(it_entry, f, indent=2)

        mean_f_q = np.mean([rep["arm_Q"]["decoded"]["f"] for rep in replicates_data])
        mean_f_c = np.mean([rep["arm_C"]["decoded"]["f"] for rep in replicates_data])
        print(f"[{it+1:02d}/{args.iterations}] Job {job_id} | dt={it_entry['wall_seconds']:.1f}s | "
              f"P(1|0)={np.mean(p_1_given_0):.4f}, P(0|1)={np.mean(p_0_given_1):.4f} | "
              f"f_Q={mean_f_q:.3f}, f_C={mean_f_c:.3f}, diff={mean_f_q - mean_f_c:+.4f}")

    # Campaign finalization
    cal_end = cal_start
    if not args.dry_run and backend:
        props = backend.properties(refresh=True)
        cal_end = str(props.last_update_date) if props else "unknown"

    campaign_meta["calibration_end"] = cal_end
    campaign_meta["end_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    campaign_meta["total_wall_seconds"] = time.time() - t_start

    with open(campaign_dir / "campaign.json", "w", encoding="utf-8") as f:
        json.dump(campaign_meta, f, indent=2)

    print("\n" + "=" * 78)
    print("CAMPAIGN FINISHED")
    print(f"Raw data: {campaign_dir}")
    print(f"Calibration start: {cal_start}")
    print(f"Calibration end  : {cal_end}")
    print("=" * 78)

if __name__ == "__main__":
    main()
