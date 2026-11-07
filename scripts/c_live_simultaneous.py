#!/usr/bin/env python3
"""
c_live_simultaneous: Szimultan 5-qubites fizikai spektator csatolas tesztje Heron processzoron.

Elrendezes:
  Fizikai transzmon lanc: [0 - 1 - 2] -- [3 - 4]
  - [0, 1, 2]: GPE fo aramkor (A, f, phi forgatasok)
  - [3, 4]: Bell-horgony (H(3) -> CX(3, 4)), a 2-es qubit kozvetlen szomszedja!
  - EGYETLEN szimultan aramkor fut egyszerre a chipen!

Karok:
  - F kar: [0, 1, 2] kapja a GPE folyadek parametereit, [3, 4] szimultan letrehozza a Bell-part.
           A mert [0, 1, 2] visszagerjeszti a GPE-t.
  - N kar: [0, 1, 2] idle (nincs hajtas, alapallapot), mikozben [3, 4] fut.
           A folyadek sem nem lep, sem nem gerjesztodik.
"""

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
RAW_DIR = REPO / "measurement_raw" / "c_live_simultaneous"
sys.path.insert(0, str(HERE))

from fluid_sim import FluidSim


def build_simultaneous_circuit(QuantumCircuit, a_f, f_f, phi_f, active=True):
    # 5 qubit, 5 klasszikus bit: 0..2 = fo, 3..4 = Bell
    qc = QuantumCircuit(5, 5)
    if active:
        qc.ry(a_f, 0)
        qc.ry(2.0 * math.pi * (f_f / 15.0), 1)
        qc.ry(phi_f * math.pi, 2)
    
    # Szimultan Bell-par a szomszedos 3, 4 qubiteken
    qc.h(3)
    qc.cx(3, 4)
    
    qc.measure([0, 1, 2, 3, 4], [0, 1, 2, 3, 4])
    return qc


def decode_main(counts, shots):
    # bitstring hossza 5: bit4 bit3 bit2 bit1 bit0
    p0 = sum(v for k, v in counts.items() if k[4] == "1") / shots
    p1 = sum(v for k, v in counts.items() if k[3] == "1") / shots
    p2 = sum(v for k, v in counts.items() if k[2] == "1") / shots
    clamp = lambda p: max(0.0, min(1.0, p))
    a_q = 2.0 * math.asin(math.sqrt(clamp(p0)))
    f_q = math.asin(math.sqrt(clamp(p1))) / math.pi * 15.0
    phi_q = 2.0 * math.asin(math.sqrt(clamp(p2))) / math.pi
    return a_q, f_q, phi_q


def extract_bell_correlation(counts, shots):
    # Bell bitek a 3 es 4 pozicioban (k[1] es k[0] a balrol-jobbra indexelesnel)
    # k string formaban: c[4] c[3] c[2] c[1] c[0]
    n_00 = sum(v for k, v in counts.items() if k[0] == "0" and k[1] == "0")
    n_11 = sum(v for k, v in counts.items() if k[0] == "1" and k[1] == "1")
    return (n_00 + n_11) / shots


def main():
    ap = argparse.ArgumentParser(description="Szimultan 5-qubites GPE-Bell teszt")
    ap.add_argument("--token-file", default=None)
    ap.add_argument("--backend", default="ibm_marrakesh")
    ap.add_argument("--blocks", type=int, default=30, help="blokkok szama (1 blokk = 1 F + 1 N)")
    ap.add_argument("--shots", type=int, default=2048)
    ap.add_argument("--gpe-steps", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20261107)
    ap.add_argument("--layout", type=int, nargs=5, default=[0, 1, 2, 3, 4],
                    help="fizikai 5-qubit lanc: 0..2 = fo, 3..4 = Bell")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    from qiskit import QuantumCircuit, transpile

    tag = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out_dir = RAW_DIR / (tag + ("_dry" if args.dry_run else ""))
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    schedule = []
    for b in range(args.blocks):
        pair = ["F", "N"]
        rng.shuffle(pair)
        schedule += [(b, arm) for arm in pair]

    if args.dry_run:
        from qiskit.primitives import StatevectorSampler
        sampler = StatevectorSampler(seed=args.seed)
        backend_name = "dry-run-statevector"

        def run(qc):
            res = sampler.run([qc], shots=args.shots).result()
            counts = res[0].data.c.get_counts()
            return "dry-" + str(int(time.time() * 1000)), counts
    else:
        if not args.token_file:
            sys.exit("Add meg a --token-file kapcsolot (vagy --dry-run).")
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
        with open(args.token_file, encoding="utf-8") as fh:
            token = json.load(fh)["apikey"]
        service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        backend = service.backend(args.backend)
        backend_name = backend.name
        sampler = SamplerV2(backend)

        def run(qc):
            isa = transpile(qc, backend=backend, initial_layout=args.layout, optimization_level=1, seed_transpiler=args.seed)
            job = sampler.run([isa], shots=args.shots)
            res = job.result()
            return job.job_id(), res[0].data.c.get_counts()

    meta = {
        "campaign": tag, "backend": backend_name, "dry_run": args.dry_run, "blocks": args.blocks,
        "shots": args.shots, "gpe_steps": args.gpe_steps, "seed": args.seed,
        "layout": args.layout,
        "schedule": [arm for _, arm in schedule],
        "preregistration": "docs/PREREGISTRATION-c_live_simultaneous.md",
    }
    (out_dir / "campaign.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("=" * 72)
    print(f"c_live_simultaneous | {backend_name} | {args.blocks} blokk = {2*args.blocks} job | shots={args.shots}")
    print(f"5-qubites lanc: {args.layout} | fo: {args.layout[:3]} | Bell: {args.layout[3:]}")
    print("=" * 72)

    fluid = FluidSim(seed=args.seed)
    last = None

    for i, (blk, arm) in enumerate(schedule):
        t0 = time.time()
        if arm == "F" or last is None:
            for _ in range(args.gpe_steps):
                fluid.gpe_step()
            mode, a_f, f_f, phi_f, _ = fluid.extract_modal_parameters()
            params = (a_f, f_f, phi_f, mode)
            if arm == "F":
                last = params
        else:
            params = last
        a_f, f_f, phi_f, mode = params

        active = (arm == "F")
        qc = build_simultaneous_circuit(QuantumCircuit, a_f, f_f, phi_f, active=active)
        job_id, counts = run(qc)

        c_val = extract_bell_correlation(counts, args.shots)
        a_q, f_q, phi_q = decode_main(counts, args.shots)

        if arm == "F":
            fluid.excite(a_q, f_q, phi_q)

        rec = {
            "index": i, "block": blk, "arm": arm, "job_id": job_id,
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "fluid_params_used": {"A": a_f, "f": f_f, "phi": phi_f, "mode": mode},
            "decoded": {"A": a_q, "f": f_q, "phi": phi_q},
            "counts": counts,
            "c_measured": c_val,
            "fluid_excited": arm == "F",
        }
        (out_dir / f"iter{i:04d}_{arm}_{job_id}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
        print(f"[{i+1:03d}/{len(schedule)}] blokk {blk:02d} {arm} | job {job_id} | c={c_val:.4f} | {time.time()-t0:.1f}s")

    print(f"Kesz. Nyers adat: {out_dir}")
    print(f"Kiertekeles: python scripts/c_live_simultaneous_analyze.py {out_dir}")


if __name__ == "__main__":
    main()
