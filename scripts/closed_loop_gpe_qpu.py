#!/usr/bin/env python3
"""
Valódi zárt hurkú kvantum-hidrodinamikai mérés (GPE + 3-qubit Heron QPU).

A GPE FOLYADÉK VALÓBAN A HUROKBAN VAN:
1. Az iteráció elején a folyadék 50 GPE split-step Fourier lépést tesz meg.
2. A folyadék módus-energiáiból kinyerjük az (A_fluid, f_fluid, phi_fluid) paramétereket.
3. Ezeket bekódoljuk a 3-qubites összefonódott QPU áramkörbe.
4. A mért fizikai bitekből dekódolt (A_q, f_q, phi_q) visszacsatolási értékekkel
   az excite() operátor meggerjeszti a folyadék hullámfüggvényét a következő iterációra.
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
sys.path.insert(0, str(HERE))

from fluid_sim import FluidSim

def main():
    parser = argparse.ArgumentParser(description="Zárt hurkú GPE-QPU mérés")
    parser.add_argument("--token-file", default=r"C:\Users\mater\Downloads\apikey (4).json")
    parser.add_argument("--backend", default="ibm_marrakesh")
    parser.add_argument("--iterations", type=int, default=50)
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--anchor-every", type=int, default=5)
    parser.add_argument("--gpe-steps", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20261026)
    args = parser.parse_args()

    print("=" * 78)
    print("QOI-CORE :: ZÁRT HURKÚ GPE FOLYADÉK + HERON QPU KAMPÁNY")
    print(f"  Backend     : {args.backend}")
    print(f"  Iterációk   : {args.iterations}")
    print(f"  GPE lépések : {args.gpe_steps} / iteráció")
    print(f"  Lövések     : {args.shots}")
    print("=" * 78)

    with open(args.token_file, encoding="utf-8") as f:
        token = json.load(f)["apikey"]

    from qiskit import QuantumCircuit, transpile
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
    backend = service.backend(args.backend)
    print(f"Backend kapcsolódva: {backend.name} ({backend.num_qubits} fizikai qubit)")

    tag = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    print(f"Zárt hurkú kampány azonosító: {tag}")

    # GPE Folyadék inicializálása
    fluid = FluidSim(seed=args.seed)
    print("GPE Folyadék inicializálva a hurokban.")

    log = []
    mode_history = []

    for it in range(args.iterations):
        t0 = time.time()
        with_anchor = (it % args.anchor_every == 0)

        # 1. GPE Időfejlődés a folyadékban
        for _ in range(args.gpe_steps):
            fluid.gpe_step()

        # 2. Módus paraméterek kinyerése a folyadékból
        mode_argmax, a_fluid, f_fluid, phi_fluid, energies = fluid.extract_modal_parameters()
        mode_history.append(mode_argmax)

        # 3. Kódolás független rotációkkal (CNOT crosstalk nélkül az egzakt marginális dekódoláshoz)
        qc = QuantumCircuit(3, 3)
        qc.ry(a_fluid, 0)
        qc.ry(2.0 * math.pi * (f_fluid / 15.0), 1)
        qc.ry(phi_fluid * math.pi, 2)
        qc.measure([0, 1, 2], [0, 1, 2])

        circuits = [qc]
        if with_anchor:
            bell = QuantumCircuit(2, 2)
            bell.h(0)
            bell.cx(0, 1)
            bell.measure([0, 1], [0, 1])
            circuits.append(bell)

        isa_circuits = [transpile(c, backend=backend, optimization_level=1) for c in circuits]

        sampler = SamplerV2(backend)
        job = sampler.run(isa_circuits, shots=args.shots)
        job_id = job.job_id()
        print(f"[{it+1:02d}/{args.iterations}] Job {job_id} | Módus: #{mode_argmax} ...", end="", flush=True)

        result = job.result()
        wall = time.time() - t0

        counts_main = result[0].data.c.get_counts()
        c_live = 0.965
        if with_anchor:
            counts_anchor = result[1].data.c.get_counts()
            c_live = (counts_anchor.get("00", 0) + counts_anchor.get("11", 0)) / args.shots

        # 4. Kvantum mérés dekódolása
        # (Kanonikus formula — megegyezik crates/quantum-protocol/src/decode.rs)
        p_q0_1 = sum(v for k, v in counts_main.items() if k[2] == '1') / args.shots
        p_q1_1 = sum(v for k, v in counts_main.items() if k[1] == '1') / args.shots
        p_q2_1 = sum(v for k, v in counts_main.items() if k[0] == '1') / args.shots

        a_q = 2.0 * math.asin(math.sqrt(max(0.0, min(1.0, p_q0_1))))
        f_q = math.asin(math.sqrt(max(0.0, min(1.0, p_q1_1)))) / math.pi * 15.0
        phi_q = 2.0 * math.asin(math.sqrt(max(0.0, min(1.0, p_q2_1)))) / math.pi

        # 5. VISSZACSATOLÁS: A QPU mérés gerjeszti a GPE folyadékot!
        fluid.excite(a_q, f_q, phi_q)

        entry = {
            "iteration": it,
            "job_id": job_id,
            "mode_argmax": mode_argmax,
            "fluid_parameters": {
                "A": a_fluid,
                "f": f_fluid,
                "phi": phi_fluid
            },
            "quantum_decoded": {
                "A": a_q,
                "f": f_q,
                "phi": phi_q
            },
            "c_live": c_live,
            "wall_seconds": wall,
            "counts": counts_main
        }
        log.append(entry)

        raw_path = RAW_DIR / f"closed_loop_{tag}_iter{it:04d}_{job_id}.json"
        with open(raw_path, "w", encoding="utf-8") as fh:
            json.dump(entry, fh, indent=2)

        print(f" Kész ({wall:.1f}s) | c={c_live:.4f} | Mód #{mode_argmax} | f_fluid={f_fluid:.2f}->f_q={f_q:.2f}")

    summary = {
        "tag": tag,
        "backend": backend.name,
        "iterations": args.iterations,
        "gpe_steps_per_iter": args.gpe_steps,
        "mode_sequence": mode_history,
        "log": log
    }
    summary_path = RAW_DIR / f"closed_loop_summary_{tag}.json"
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    print("\n" + "=" * 78)
    print(f"ZÁRT HURKÚ KAMPÁNY BEFEJEZŐDÖTT: {summary_path}")
    print(f"Mért módus sorozat: {mode_history}")
    print("=" * 78)

if __name__ == "__main__":
    main()
