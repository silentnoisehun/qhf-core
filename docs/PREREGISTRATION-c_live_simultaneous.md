# Preregistration: Simultaneous 5-qubit Spectator Entrainment Test on Heron QPU

Author: Máté Róbert (ORCID 0009-0003-3986-6039)
Repository: https://github.com/silentnoisehun/qhf-core
Date of registration: 2026-11-07 01:55:00 UTC

## Hypothesis

**H1:** In a single, unified 5-qubit circuit mapped to a connected physical transmon chain `[0-1-2]--[3-4]` on `ibm_marrakesh` (Heron r2), active Gross–Pitaevskii (GPE) fluid driving on qubits `[0, 1, 2]` produces a measurable shift in the Bell-anchor correlation $c = P(00) + P(11)$ on the directly adjacent spectator pair `[3, 4]` compared to the idle control arm ($N$).

**Standard quantum mechanics with isolated transmons predicts no difference ($d = 0$).**
In a realistic superconducting processor, simultaneous microwave driving on physically adjacent transmons couples through residual Hamiltonian crosstalk (Stark shift, ZZ-coupling, resonator dynamics).

## Design

- Script: `scripts/c_live_simultaneous.py`, seed 20261107, 30 blocks (60 jobs), 2048 shots, 50 GPE steps per F iteration.
- Architecture: 1 unified 5-qubit circuit per iteration.
- Layout: Fixed physical transmon line `[0, 1, 2, 3, 4]`. Qubits `[0, 1, 2]` = main GPE; Qubits `[3, 4]` = Bell anchor.
- F arm: Qubits `[0, 1, 2]` receive $(A, f, \phi)$ rotations simultaneously with the Bell circuit on `[3, 4]`. Decoded measurement excites the GPE fluid.
- N arm: Qubits `[0, 1, 2]` are idle (unexcited, ground state) while `[3, 4]` executes the Bell circuit.
- Backend: ibm_marrakesh (Heron r2), one continuous session.

## Primary Analysis & Decision Rule

Script: `scripts/c_live_simultaneous_analyze.py`. For each complete block: $d = c_F - c_N$.
H1 is **supported** only if all three hold:
1. $|mean(d)| \ge 0.003$
2. one-sided paired t-test $p < 0.01$
3. $mean(d)$ has the same sign in both the first and second half of the blocks.

In all other cases, H1 is **not supported**.
All raw data, campaign metadata, and analysis outputs will be pushed to the repository.
