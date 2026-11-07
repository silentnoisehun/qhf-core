# Preregistration: Simultaneous 5-qubit Spectator Entrainment Test on Heron QPU

Author: Máté Róbert (ORCID 0009-0003-3986-6039)
Repository: https://github.com/silentnoisehun/qhf-core
Date of registration: 2026-11-07 01:55:00 UTC
Amendment 1 Date: 2026-11-07 02:00:00 UTC (before hardware execution)

## Hypothesis

**H1:** In a single, unified 5-qubit circuit mapped to a connected physical transmon chain `[51-52-53]--[54-55]` on `ibm_marrakesh` (Heron r2), when the Gross–Pitaevskii (GPE) fluid is in the active closed loop driving qubits `[51, 52, 53]`, the Bell-anchor correlation $c = P(00) + P(11)$ on the directly adjacent spectator pair `[54, 55]` is significantly higher than in the open control arm ($N$).

**Standard quantum mechanics with isolated transmons and no-signaling predicts no difference ($d = 0$).**
Both arms execute identical microwave rotations on the main register; the only difference is whether the fluid steps and receives feedback, or remains decoupled.

## Amendment 1 Updates (Pre-Run Audit)

1. **Drive Equivalence Across Arms:**
   Both F and N arms execute the circuit with the exact same microwave rotation parameters $(A, f, \phi)$ extracted from the fluid. In arm F, decoded measurements excite the GPE fluid and the fluid steps; in arm N, the fluid neither steps nor receives feedback. This isolates the fluid closed-loop coupling from trivial drive-induced Stark/crosstalk shifts.
2. **Optimal Transmon Chain Selection:**
   Instead of the chip boundary edge `[0..4]`, the physical layout is fixed to the high-fidelity internal line `[51, 52, 53, 54, 55]`:
   - Main GPE register: `[51, 52, 53]`
   - Bell spectator pair: `[54, 55]` (readout error $< 0.49\%$, 2Q gate error $0.13\%$, baseline $c \approx 0.985-0.990$).
3. **Statistical Power & Sample Size:**
   - 60 blocks (120 total jobs), 2048 shots per iteration.
   - Standard deviation target $\sigma \approx 0.008-0.010$, providing $>80\%$ power to detect shifts $\ge 0.003$.

## Primary Analysis & Decision Rule (Strictly Directional H1)

Script: `scripts/c_live_simultaneous_analyze.py`. For each complete block: $d = c_F - c_N$.
H1 is **supported** only if all three hold:
1. $mean(d) \ge 0.003$
2. one-sided paired t-test $p < 0.01$
3. $mean(d) > 0$ in both the first and second half of the blocks independently.

In all other cases, H1 is **not supported** and the textbook prediction ($d = 0$) stands.
All raw data, campaign metadata, and analysis outputs will be pushed to the repository.
