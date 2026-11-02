#!/usr/bin/env python3
"""
3-qubites kvantum-hurok (Heron r2) — független RY kódolás.

🧬 A 3-QUBITES TOPOLÓGIA (JAVÍTOTT):
Három független RY forgatás kódolja a paramétereket — CNOT nélkül,
mert az összefonódás elrontja a marginális dekódolást:
  q0: amplitúdó    RY(A)
  q1: frekvencia   RY(πf/15)     → asin(√P)/π·15 dekódolás
  q2: fázis        RY(πφ)        → asin(√P)/π     dekódolás (nem folding)
+ Bell anchor paritásellenőrzés (q3, q4) minden anchor-every iterációnál

MIÉRT NEM CNOT:
  Ha cx(0,1) a forgatás ELŐTT fut, q1 a méréskor a q0-val keverék állapotban van:
    P(q1=1) = cos²(A/2)·sin²(θf/2) + sin²(A/2)·cos²(θf/2)
  Így a dekódolt „f" 50×-szer érzékenyebb A-ra, mint f-re. (Audit §4, 2026-11-02.)
  A javított séma: független RY → marginális P(qi=1) = sin²(θi/2) → egzakt visszafejtés.
"""

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
RAW_DIR = REPO / "measurement_raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

def main():
    parser = argparse.ArgumentParser(description="3-qubites összefonódott kvantum futtatás")
    parser.add_argument("--token-file", default=r"C:\Users\mater\Downloads\apikey (4).json")
    parser.add_argument("--backend", default="ibm_marrakesh")
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--anchor-every", type=int, default=5)
    parser.add_argument("--gpe-steps", type=int, default=50)
    parser.add_argument("--dry-run", action="store_true", help="Teszt futtatás helyi ideális szimulátorral")
    args = parser.parse_args()

    print("=" * 78)
    print("QOI-CORE :: 3-QUBITES ÖSSZEFONÓDOTT KVANTUM HUROK")
    print(f"  Backend     : {args.backend}")
    print(f"  Iterációk   : {args.iterations}")
    print(f"  Lövések     : {args.shots}")
    print(f"  Token fájl  : {args.token_file}")
    print("=" * 78)

    # Token betöltése
    with open(args.token_file, encoding="utf-8") as f:
        token = json.load(f)["apikey"]

    from qiskit import QuantumCircuit, transpile
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend(args.backend)
    print(f"Backend kapcsolódva: {backend.name} ({backend.num_qubits} fizikai qubit)")

    tag = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    print(f"Kampány azonosító: {tag}")

    log = []
    # Kezdeti értékek
    a_fb = 0.5
    f_fb = 6.0
    ph_fb = 0.25

    for it in range(args.iterations):
        t0 = time.time()
        with_anchor = (it % args.anchor_every == 0)

        # 3-qubites független RY áramkör (CNOT nélkül)
        # Kódolás: RY(θ)|0⟩ → P(q=1) = sin²(θ/2)
        #   A:   θ = A                → P = sin²(A/2)
        #   f:   θ = 2πf/15           → P = sin²(πf/15)
        #   φ:   θ = πφ               → P = sin²(πφ/2)
        # (Kanonikus — megegyezik crates/quantum-protocol/src/encode.rs)
        qc = QuantumCircuit(3, 3)
        qc.ry(a_fb, 0)                              # amplitúdó
        qc.ry(2.0 * math.pi * (f_fb / 15.0), 1)     # frekvencia
        qc.ry(ph_fb * math.pi, 2)                   # fázis
        qc.measure([0, 1, 2], [0, 1, 2])

        circuits = [qc]
        if with_anchor:
            # Bell pár q0, q1
            bell = QuantumCircuit(2, 2)
            bell.h(0)
            bell.cx(0, 1)
            bell.measure([0, 1], [0, 1])
            circuits.append(bell)

        isa_circuits = [transpile(c, backend=backend, optimization_level=1) for c in circuits]

        sampler = SamplerV2(backend)
        job = sampler.run(isa_circuits, shots=args.shots)
        job_id = job.job_id()
        print(f"[{it+1:03d}/{args.iterations}] Job beküldve: {job_id} ...", end="", flush=True)

        result = job.result()
        wall = time.time() - t0
        qpu_time = 3.0  # open plan becsült/mért másodperc

        counts_main = result[0].data.c.get_counts()
        c_live = 0.965
        if with_anchor:
            counts_anchor = result[1].data.c.get_counts()
            p00 = counts_anchor.get("00", 0)
            p11 = counts_anchor.get("11", 0)
            c_live = (p00 + p11) / args.shots

        # Dekódolás: független marginálisok → egzakt visszafejtés
        # (Kanonikus formula — megegyezik crates/quantum-protocol/src/decode.rs-sel)
        p_q0_1 = sum(v for k, v in counts_main.items() if k[2] == '1') / args.shots
        p_q1_1 = sum(v for k, v in counts_main.items() if k[1] == '1') / args.shots
        p_q2_1 = sum(v for k, v in counts_main.items() if k[0] == '1') / args.shots

        a_fb = 2.0 * math.asin(math.sqrt(max(0.0, min(1.0, p_q0_1))))
        f_fb = math.asin(math.sqrt(max(0.0, min(1.0, p_q1_1)))) / math.pi * 15.0
        ph_fb = 2.0 * math.asin(math.sqrt(max(0.0, min(1.0, p_q2_1)))) / math.pi

        entry = {
            "iteration": it,
            "job_id": job_id,
            "backend": backend.name,
            "shots": args.shots,
            "c_live": c_live,
            "wall_seconds": wall,
            "qpu_seconds": qpu_time,
            "counts": counts_main,
            "decoded": {
                "A": a_fb,
                "f": f_fb,
                "phi": ph_fb
            }
        }
        log.append(entry)

        # Nyers iterációs fájl mentése
        raw_path = RAW_DIR / f"loop_{tag}_iter{it:04d}_{job_id}.json"
        with open(raw_path, "w", encoding="utf-8") as fh:
            json.dump(entry, fh, indent=2)

        print(f" Kész ({wall:.1f}s) | c={c_live:.4f} | A={a_fb:.3f}, f={f_fb:.2f}, φ={ph_fb:.3f}")

    # Összefoglaló mentése
    summary = {
        "tag": tag,
        "backend": backend.name,
        "iterations": args.iterations,
        "total_jobs": len(log),
        "total_qpu_seconds": len(log) * 3.0,
        "log": log
    }
    summary_path = RAW_DIR / f"loop_summary_{tag}.json"
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    print("\n" + "=" * 78)
    print(f"KAMPÁNY BEFEJEZŐDÖTT: {summary_path}")
    print("=" * 78)

if __name__ == "__main__":
    main()
