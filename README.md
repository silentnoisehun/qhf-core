# QHF Bell-Spectator: Quantum-Hydrodynamic Entrainment on Heron QPU

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![IBM Quantum](https://img.shields.io/badge/IBM%20Quantum-Heron%20r2%20(156q)-blue.svg)](https://quantum.ibm.com/)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0003--3986--6039-green.svg)](https://orcid.org/0009-0003-3986-6039)

**Preregistered experimental campaigns testing macroscopic quantum-hydrodynamic spectator entrainment and closed feedback loops on a 156-qubit superconducting quantum processor (`ibm_marrakesh`, Heron r2).**

**Author:** Máté Róbert (Rongyász)  
**Affiliation:** Silent Coder Labs  
**ORCID:** [0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039)  
**Contact:** materobi86@gmail.com  

---

## 🔬 Experimental Lineage & Structure

This repository archives the complete, step-by-step preregistered experimental campaigns investigating whether classical-quantum closed feedback loops (coupling a 2D Gross–Pitaevskii superfluid simulation to physical superconducting transmon qubits) deviate from standard isolated quantum mechanics.

---

### 1. Phase 1: Sequential Interleaved Baseline Campaign (`docs/PREREGISTRATION-c_live.md`)
* **Design:** 60 blocks (120 IBM Quantum jobs), 1024 shots per job.
* **Layout:** Physical edge qubits `[0, 1, 2]` (main 3-qubit RY circuit) and `[0, 1]` (Bell anchor). Circuits executed sequentially in each job.
* **Result (Campaign `20261107T012230Z`):**
  - Mean $c_F = 0.9305$, Mean $c_N = 0.9279$
  - Difference $d = +0.00254$, standard deviation $s = 0.0200$, $t = 0.982$, $p = 0.165$.
  - Result: $H_1$ not supported under the preregistered threshold ($\Delta \ge 0.003, p < 0.01$). Standard QM prediction ($d = 0$) held.

---

### 2. Phase 2: Simultaneous 5-Qubit Spectator Campaign (`docs/PREREGISTRATION-c_live_simultaneous.md`)
* **Pre-Execution Amendments (Audit & Rigor):**
  1. **Drive Equivalence Across Arms:** Both F and N arms execute with strictly identical microwave rotations $(A, f, \phi)$ extracted from the fluid. In arm F, measurements excite the fluid; in arm N, the fluid is decoupled. This isolates the feedback loop from trivial drive-induced Stark/crosstalk shifts.
  2. **Optimal Transmon Chain:** Mapped to the highest-fidelity internal line on the Heron lattice: `[51, 52, 53, 54, 55]`. Bell pair `[54, 55]` features $<0.49\%$ readout error and $0.13\%$ two-qubit gate error (baseline $c \approx 0.986$).
  3. **Simultaneous Single-Circuit Architecture:** A single 5-qubit circuit runs both the main GPE register `[51, 52, 53]` and the spectator Bell pair `[54, 55]` simultaneously.
  4. **Strict Block Angle-Locking:** Fluid parameters $(A, f, \phi)$ are computed strictly once per block before shuffling, ensuring $F$ and $N$ receive identical microwave angles regardless of execution order.
* **Result (Campaign `20261107T023824Z`, 60 complete blocks = 120 live QPU jobs):**
  - Mean $c_F = 0.98570$, Mean $c_N = 0.98549$
  - Difference $d = c_F - c_N = +0.00021$
  - Standard deviation $s = 0.00399$ (shot-noise limited at 2048 shots)
  - $t = 0.4108$, $p_{\text{one-sided}} = 0.341$, $p_{\text{two-sided}} = 0.683$
  - First-half mean diff (blocks 0–29): $-0.00024$; Second-half mean diff (blocks 30–59): $+0.00067$
  - **In-situ Calibration & Queue Sensitivity:** Initial calibration at `02:36:25 UTC` (`03:36:25 CET`). An automatic Heron calibration update occurred at `02:47:47 UTC` (`03:47:47 CET`), corresponding to block 33. In block 38, arm N waited 18 minutes in the backend queue after arm F due to transient backend scheduling. Excluding blocks 33–38 entirely (leaving 54 paired blocks): $d = -0.00017 \approx -0.0002$, $s = 0.00346$, $t = -0.365$, $p = 0.72$. The result is unchanged by queue latency and calibration shifts.
  - **Decision:** All criteria for $H_1$ ($\Delta \ge 0.003, p < 0.01$, sign consistency) failed. **$H_1$ is NOT supported. Standard textbook quantum mechanics ($d = 0$) holds.**

---

### 3. Phase 3: QPU vs Noise-Matched Classical RNG Experiment (`docs/PREREGISTRATION-qpu_vs_rng.md`)
* **Hypothesis:** Does a Gross–Pitaevskii fluid whose feedback comes from real QPU measurements (arm Q) evolve differently from an identical fluid whose feedback comes from a classical binomial random generator with the same encoding and in-situ measured readout error (arm C)?
* **Design (including Amendment 1):**
  - Scripts: `scripts/qpu_vs_rng.py` and `scripts/qpu_vs_rng_analyze.py`, seed `20261108`.
  - $R = 20$ replicates, 40 iterations (burn-in 10), 1024 shots, 50 GPE steps per iteration.
  - **Optimal Qubit Chain:** Fixed layout `[53, 54, 55]` on `ibm_marrakesh` (reassigned from `[51, 52, 53]` in Amendment 1 because Q51 exhibits a 15.9% readout error that could induce drift artifacts, whereas Q53, Q54, and Q55 feature 1.8%, 0.5%, and 0.4% readout errors respectively).
  - 1 job per iteration: 20 main circuits from Q fluids + 2 in-situ calibration circuits ($|000\rangle$ and $|111\rangle$) on physical qubits `[53, 54, 55]` (40 jobs in total).
  - Arm C receives ideal probabilities distorted with the exact in-situ $P(1|0)$ and $P(0|1)$ measured in the same job, sampled binomially.
* **Primary Decision Rule (Pre-registered):**
  - Unit: Replicate. $D_r = \text{mean } f_Q - \text{mean } f_C$ over iterations 11–40, where $f$ is mode centroid.
  - Exact two-sided sign-flip permutation test ($2^{20} = 1,048,576$ permutations).
  - $H_1$ supported only if: (1) two-sided permutation $p < 0.01$, and (2) mean $D$ has the same sign in replicates 0–9 and 10–19.
* **Stopping Rule & Audit Trail:**
  - The monthly free allocation (600s) on the executing account was reached at job 34. In strict accordance with the preregistered stopping rule (*"If the run breaks, all complete iterations are analysed with the same rule (minimum 13 iterations), and the number is reported"*), execution stopped cleanly at 33 complete iterations (well exceeding the minimum 13 required).
  - *Integrity / Unblinding Audit:* The first 17 raw JSON iterations were committed in `6021cb6` purely as an operational git backup; the statistical analyzer `qpu_vs_rng_analyze.py` was strictly executed only after campaign completion.
* **Result (Campaign `20261107T032204Z`, 33 complete iterations, 23 evaluated iters 10–32):**
  - Mean $D(f) = +0.00147$
  - Standard deviation $\text{sd}(D) = 0.00790$
  - Half 1 (replicates 0–9): Mean $D = +0.00234$
  - Half 2 (replicates 10–19): Mean $D = +0.00060$ (halves sign match: True)
  - Exact two-sided sign-flip permutation $p$-value: **$p = 0.411070$** (threshold: $p < 0.01$)
  - Secondary metrics: $D(A) = -0.00036$ ($p = 0.803$), $D(\sigma_\phi) = +0.07860$ ($p < 0.0001$), $D(\text{autocorr}_f) = +0.01459$ ($p < 0.0001$).
  - **Decision:** $p = 0.411 \gg 0.01$. **$H_1$ is NOT supported. Standard textbook quantum mechanics holds.** The QPU-fed Gross–Pitaevskii fluid and the noise-matched classical RNG-fed fluid are statistically indistinguishable.

---

### 4. Phase 4: Replication on Second Backend (`docs/PREREGISTRATION-qpu_vs_rng_replication.md`)
* **Design & Lock-in (Registered in advance of Phase 3 completion):**
  - Backend: `ibm_kingston` (156q Heron r2).
  - Fresh independent seed: `20261109`.
  - Algorithmic chain selection via `scripts/select_chain.py` (lowest readout error linear chain $\le 0.03$ with reported 2Q gate errors). Selected: `[48, 49, 50]` (mean readout error $0.47\%$).
* **Combined Decision Rule:** The QPU/RNG difference is claimed **only if** $H_1$ is supported in Phase 3 **and** in this replication, **with the same sign of mean $D$**.
* **Combined Conclusion:** Because Phase 3 yielded $p = 0.411$ ($H_1$ not supported), the combined criterion for claiming a physical difference cannot be met under the preregistration rules. Standard quantum mechanics stands corroborated across all campaigns.

---

## 📁 Repository Layout

```
├── docs/
│   ├── PREREGISTRATION-c_live.md                 # Phase 1 protocol (interleaved sequential)
│   ├── PREREGISTRATION-c_live_simultaneous.md    # Phase 2 protocol (simultaneous 5-qubit spectator)
│   ├── PREREGISTRATION-qpu_vs_rng.md             # Phase 3 protocol (QPU vs noise-matched RNG)
│   └── PREREGISTRATION-qpu_vs_rng_replication.md # Phase 4 protocol (replication on ibm_kingston)
├── scripts/
│   ├── c_live_interleaved.py                     # Phase 1 runner
│   ├── c_live_analyze.py                         # Phase 1 analyzer
│   ├── c_live_simultaneous.py                    # Phase 2 runner
│   ├── c_live_simultaneous_analyze.py            # Phase 2 analyzer
│   ├── qpu_vs_rng.py                             # Phase 3 & 4 runner
│   ├── qpu_vs_rng_analyze.py                     # Phase 3 & 4 analyzer
│   ├── select_chain.py                           # Algorithmic optimal chain selector
│   └── fluid_sim.py                              # GPE 2D split-step Fourier solver
└── measurement_raw/
    ├── c_live/
    │   └── 20261107T012230Z/                     # Phase 1: 120-job live Heron QPU dataset & analysis.json
    ├── c_live_simultaneous/
    │   └── 20261107T023824Z/                     # Phase 2: Complete 120-job live Heron QPU dataset & analysis.json
    └── qpu_vs_rng_replication/
        └── layout_selection.json                 # Algorithmic selection output for ibm_kingston
```

---

## 🛠️ Replication & Verification

To verify the Phase 2 simultaneous spectator campaign from raw quantum counts:
```bash
python scripts/c_live_simultaneous_analyze.py measurement_raw/c_live_simultaneous/20261107T023824Z
```

To run a zero-quota dry run of the Phase 3 QPU vs RNG pipeline:
```bash
python scripts/qpu_vs_rng.py --dry-run --replicates 20 --iterations 40
python scripts/qpu_vs_rng_analyze.py measurement_raw/qpu_vs_rng/<dry_run_folder>
```
