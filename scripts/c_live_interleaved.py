#!/usr/bin/env python3
"""
c_live teszt: befolyasolja-e a GPE folyadek a hurokban a Bell-horgony korrelaciojat?

Előregisztracio: docs/PREREGISTRATION-c_live.md (ezt commitold es pushold FUTTATAS ELOTT).

Terv:
  - Blokkok: minden blokkban egy F (folyadek a hurokban) es egy N (folyadek nelkul) iteracio,
    a blokkon beluli sorrend veletlen (rogzitett seed).
  - Mindket kar UGYANAZT a ket aramkort kuldi egy jobban: [fo 3-qubites aramkor, Bell-horgony].
  - F kar: a folyadek lep (gpe_steps), a parameterei kodolodnak, a mert ertekek visszagerjesztik.
  - N kar: a fo aramkor az utolso F-parameterekkel fut, de a folyadek NEM lep es NEM gerjesztodik.
  - A Bell-horgony MINDEN iteracioban fut, ugyanazon a rogzitett fizikai qubitparon.
  - c = (N_00 + N_11) / shots, KIZAROLAG mert countsbol. Nincs alapertek.

Hasznalat:
  python scripts/c_live_interleaved.py --dry-run            # helyi szimulacio, kvota nelkul
  python scripts/c_live_interleaved.py --token-file KEY.json --backend ibm_marrakesh
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
RAW_DIR = REPO / "measurement_raw" / "c_live"
sys.path.insert(0, str(HERE))

from fluid_sim import FluidSim  # a qhf-core sajat folyadek-szimulacioja


def build_main(QuantumCircuit, a, f, phi):
    qc = QuantumCircuit(3, 3)
    qc.ry(a, 0)
    qc.ry(2.0 * math.pi * (f / 15.0), 1)
    qc.ry(phi * math.pi, 2)
    qc.measure([0, 1, 2], [0, 1, 2])
    return qc


def build_bell(QuantumCircuit):
    bell = QuantumCircuit(2, 2)
    bell.h(0)
    bell.cx(0, 1)
    bell.measure([0, 1], [0, 1])
    return bell


def decode(counts, shots):
    p0 = sum(v for k, v in counts.items() if k[2] == "1") / shots
    p1 = sum(v for k, v in counts.items() if k[1] == "1") / shots
    p2 = sum(v for k, v in counts.items() if k[0] == "1") / shots
    clamp = lambda p: max(0.0, min(1.0, p))
    a_q = 2.0 * math.asin(math.sqrt(clamp(p0)))
    f_q = math.asin(math.sqrt(clamp(p1))) / math.pi * 15.0
    phi_q = 2.0 * math.asin(math.sqrt(clamp(p2))) / math.pi
    return a_q, f_q, phi_q


def main():
    ap = argparse.ArgumentParser(description="c_live osszefesult be/ki teszt")
    ap.add_argument("--token-file", default=None)
    ap.add_argument("--backend", default="ibm_marrakesh")
    ap.add_argument("--blocks", type=int, default=60, help="blokkok szama (1 blokk = 1 F + 1 N)")
    ap.add_argument("--shots", type=int, default=1024)
    ap.add_argument("--gpe-steps", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20261107)
    ap.add_argument("--bell-qubits", type=int, nargs=2, default=None,
                    help="rogzitett fizikai qubitpar a horgonyhoz (pl. 0 1); ha nincs, az elso transpile valasztja, utana rogzitve")
    ap.add_argument("--dry-run", action="store_true", help="helyi StatevectorSampler + kiolvasasi zaj, kvota nelkul")
    ap.add_argument("--dry-readout-error", type=float, default=0.012)
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

    main_proto = build_main(QuantumCircuit, 0.5, 3.0, 0.3)
    bell_proto = build_bell(QuantumCircuit)

    if args.dry_run:
        import numpy as np
        from qiskit.primitives import StatevectorSampler
        sampler = StatevectorSampler(seed=args.seed)
        nrng = np.random.default_rng(args.seed)
        backend_name = "dry-run-statevector"
        main_layout, bell_layout = [0, 1, 2], [0, 1]

        def run(circs):
            res = sampler.run(circs, shots=args.shots).result()
            outs = []
            for r in res:
                counts = r.data.c.get_counts()
                noisy = {}
                for k, v in counts.items():
                    for _ in range(v):
                        bits = "".join(ch if nrng.random() > args.dry_readout_error else ("1" if ch == "0" else "0") for ch in k)
                        noisy[bits] = noisy.get(bits, 0) + 1
                outs.append(noisy)
            return "dry-" + str(int(time.time() * 1000)), outs
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

        def phys(tc, n):
            try:
                return list(tc.layout.initial_index_layout(filter_ancillas=True))[:n]
            except Exception:
                return None

        t_main = transpile(main_proto, backend=backend, optimization_level=1, seed_transpiler=args.seed)
        main_layout = phys(t_main, 3)
        if args.bell_qubits:
            bell_layout = list(args.bell_qubits)
        else:
            t_bell = transpile(bell_proto, backend=backend, optimization_level=1, seed_transpiler=args.seed)
            bell_layout = phys(t_bell, 2)
        if not main_layout or not bell_layout:
            sys.exit("Nem sikerult rogziteni a layoutot; add meg a --bell-qubits kapcsolot.")

        def run(circs):
            isa = [
                transpile(circs[0], backend=backend, initial_layout=main_layout, optimization_level=1, seed_transpiler=args.seed),
                transpile(circs[1], backend=backend, initial_layout=bell_layout, optimization_level=1, seed_transpiler=args.seed),
            ]
            job = sampler.run(isa, shots=args.shots)
            res = job.result()
            return job.job_id(), [res[0].data.c.get_counts(), res[1].data.c.get_counts()]

    meta = {
        "campaign": tag, "backend": backend_name, "dry_run": args.dry_run, "blocks": args.blocks,
        "shots": args.shots, "gpe_steps": args.gpe_steps, "seed": args.seed,
        "main_layout": main_layout, "bell_layout": bell_layout,
        "schedule": [arm for _, arm in schedule],
        "preregistration": "docs/PREREGISTRATION-c_live.md",
    }
    (out_dir / "campaign.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print("=" * 72)
    print(f"c_live teszt | {backend_name} | {args.blocks} blokk = {2*args.blocks} job | shots={args.shots}")
    print(f"horgony qubitpar: {bell_layout} | fo aramkor: {main_layout} | kampany: {tag}")
    print("=" * 72)

    fluid = FluidSim(seed=args.seed)
    last = None  # utolso F-parameterek
    bell = build_bell(QuantumCircuit)

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

        job_id, (c_main, c_bell) = run([build_main(QuantumCircuit, a_f, f_f, phi_f), bell])
        c_val = (c_bell.get("00", 0) + c_bell.get("11", 0)) / args.shots
        a_q, f_q, phi_q = decode(c_main, args.shots)

        if arm == "F":
            fluid.excite(a_q, f_q, phi_q)

        rec = {
            "index": i, "block": blk, "arm": arm, "job_id": job_id,
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "fluid_params_used": {"A": a_f, "f": f_f, "phi": phi_f, "mode": mode},
            "decoded": {"A": a_q, "f": f_q, "phi": phi_q},
            "counts_main": c_main, "counts_bell": c_bell,
            "c_measured": c_val,
            "fluid_excited": arm == "F",
        }
        (out_dir / f"iter{i:04d}_{arm}_{job_id}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
        print(f"[{i+1:03d}/{len(schedule)}] blokk {blk:02d} {arm} | job {job_id} | c={c_val:.4f} | {time.time()-t0:.1f}s")

    print(f"Kesz. Nyers adat: {out_dir}")
    print(f"Kiertekeles: python scripts/c_live_analyze.py {out_dir}")


if __name__ == "__main__":
    main()
