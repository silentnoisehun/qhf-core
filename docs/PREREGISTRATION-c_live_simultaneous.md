# Preregistration: Simultaneous 5-qubit Spectator Entrainment Test on Heron QPU

Author: Máté Róbert (ORCID 0009-0003-3986-6039)
Repository: https://github.com/silentnoisehun/qhf-bell-spectator
Date of registration: 2026-11-07 01:55:00 UTC
Amendment 1 Date: 2026-11-07 02:00:00 UTC
Amendment 2 Date: 2026-11-07 02:10:00 UTC (before hardware execution)

## Hypothesis

**H1:** In a single, unified 5-qubit circuit mapped to a connected physical transmon chain `[51-52-53]--[54-55]` on `ibm_marrakesh` (Heron r2), when the Gross–Pitaevskii (GPE) fluid is in the active closed loop driving qubits `[51, 52, 53]`, the Bell-anchor correlation $c = P(00) + P(11)$ on the directly adjacent spectator pair `[54, 55]` is significantly higher than in the open control arm ($N$).

**Standard quantum mechanics with isolated transmons and no-signaling predicts no difference ($d = 0$).**
Both arms execute identical microwave rotations on the main register; the only difference is whether the fluid steps and receives feedback, or remains decoupled.

## Amendments (Pre-Execution Audit)

### Amendment 1:
1. **Drive Equivalence Across Arms:** Both F and N arms execute the circuit with identical microwave rotations extracted from the fluid.
2. **Optimal Transmon Chain:** Mapped to the highest-fidelity internal line on the Heron lattice: `[51, 52, 53, 54, 55]`. Bell pair `[54, 55]` features $<0.49\%$ readout error and $0.13\%$ two-qubit gate error (baseline $c \approx 0.985-0.990$).
3. **Simultaneous Single-Circuit Architecture:** A single 5-qubit circuit runs both the main GPE register `[51, 52, 53]` and the spectator Bell pair `[54, 55]` simultaneously.

### Amendment 2 (Audit & Pre-Run Refinement):
1. **Strict Block-Level Angle Synchronization:**
   In every block, the GPE fluid advances 50 steps once at the beginning of the block to extract $(A, f, \phi)$. Regardless of whether F or N runs first in the randomized block schedule, both arms execute with the exact same $(A, f, \phi)$ parameters. Only arm F's measurement feedback is returned to the fluid. This eliminates any order-dependent angle lag.
2. **Calibration Snapshot Logging:**
   Physical backend properties (`backend.properties()`), including individual qubit readout errors and two-qubit gate errors for the chain `[51..55]`, are captured directly before the run and permanently archived in `campaign.json`.
3. **Sensitivity / Statistical Power:**
   For $N = 60$ blocks with $\sigma \approx 0.009$, statistical power is $\approx 55–60\%$ for $\Delta = 0.003$ and $>80\%$ for $\Delta \ge 0.004$.

## Primary Analysis & Decision Rule (Strictly Directional H1)

Script: `scripts/c_live_simultaneous_analyze.py`. For each complete block: $d = c_F - c_N$.
H1 is **supported** only if all three hold:
1. $mean(d) \ge 0.003$
2. one-sided paired t-test $p < 0.01$
3. $mean(d) > 0$ in both the first and second half of the blocks independently.

In all other cases, H1 is **not supported** and the textbook prediction ($d = 0$) stands.
All raw data, campaign metadata, and analysis outputs will be pushed to the repository.
