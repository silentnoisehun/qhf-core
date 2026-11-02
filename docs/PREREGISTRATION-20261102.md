# FORMAL PREREGISTRATION PROTOCOL: QOI-CORE-20261102-GPE-QPU
Date: 2026-11-02
Author: Rongyasz (Mate)
Repository: https://github.com/silentnoisehun/qoi-core
Backend Target: ibm_marrakesh (156-qubit Heron r2)
Available Reserve: 424 s (consumed: 176 s / 600 s)

## 1. Primary Hypothesis
In a closed feedback loop where:
1. GPE fluid field psi evolves under split-step Fourier kinetic and nonlinear potential operator (50 GPE steps per loop).
2. The extracted macroscopic mode observables (A, f, phi) are encoded onto a 3-qubit entangled register:
   Ry(phi)_2 * CX_{1->2} * Ry(2*pi*f/15)_1 * CX_{0->1} * Ry(A)_0 |000>
3. The measured physical Heron quantum probabilities decoded into (A_q, f_q, phi_q) EXCITE the GPE fluid via:
   psi <- excite(psi, A_q, f_q, phi_q)
   with proper radial scaling target_rad = (f/15)*rmax and modular angular wrapping.

## 2. Testable Falsification Criterion (The Delta vs Standard QM Fixed Points)
- **Null Hypothesis (H0 - Standard Circuit Drift):**
  Without true hydrodynamic fluid coupling, the 3-qubit circuit drifts to its intrinsic unperturbed algebraic fixed points:
  phi -> 0.2500, f -> 3.7500, and A drifts upwards (readout bias > 1.25).
- **Alternative Hypothesis (H1 - Macroscopic Fluid Entrainment):**
  With genuine GPE coupling (g = 50.0), the nonlinear wave disperses the fixed point and locks into discrete mode attractor transitions (M1 >= 4 distinct modes, and non-trivial excursions into modes #0, #6, #1, #2).
- **Metric Verification:**
  Empirical mode sequence from physical QPU will be compared against:
  1. The uncoupled quantum circuit drift (the 80-run baseline tag 20261102T160623Z).
  2. Classical control (exact zero-noise feedback).
  3. 200 magnitude-matched permutations of the true physical residual.

## 3. Experimental Parameters
- Iterations: 50
- Shots per circuit: 1024
- GPE steps per iteration: 50
- Anchor every: 5 iterations
- Total estimated QPU time: 50 * 3.0 s = 150.0 s
- Remaining safe margin: 424 s - 150 s = 274 s
