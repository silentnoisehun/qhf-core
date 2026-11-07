# Preregistration: replication of the QPU vs noise-matched RNG test on a second backend

Author: Máté Róbert (ORCID 0009-0003-3986-6039)  
Repository: https://github.com/silentnoisehun/qhf-bell-spectator  
Date of registration: 2026-11-07 03:28:00 UTC (04:28 CET) (commit before the replication run and before Phase 3 completion)  
Parent preregistration: `docs/PREREGISTRATION-qpu_vs_rng.md` (Phase 3, incl. Amendment 1)

## Purpose

Phase 3 states that a supported H1 counts as evidence only after a replication on a second backend with the same rule. This file fixes that replication in advance. It is registered before the Phase 3 result is known, and the replication is run whatever the Phase 3 result is.

## Hypothesis

Identical to Phase 3: a QPU-fed Gross–Pitaevskii fluid (arm Q) evolves differently from an identical fluid fed by a classical binomial generator with the same encoding and the in-situ measured readout error (arm C). Standard quantum mechanics predicts no difference beyond noise. Two-sided.

## Design (only these items differ from Phase 3)

- Backend: `ibm_kingston` (Heron r2).
- Seed: 20261109 (a fresh, independent set of replicates; Phase 3 used 20261108).
- Layout: chosen by a fixed rule, not by hand, immediately before the run, with `scripts/select_chain.py`:
  - candidates are all connected 3-qubit linear chains a–b–c on the backend's coupling map;
  - a chain is excluded if any of its qubits has readout error > 0.03 or if any of its two-qubit links has no reported gate error;
  - the chain with the lowest sum of the three readout errors is selected (ties: lowest first qubit index);
  - the selected chain and the full calibration snapshot are written to `measurement_raw/qpu_vs_rng_replication/layout_selection.json` and committed with the data.
- Everything else is unchanged: R = 20 replicates, 40 iterations, 1024 shots, 50 GPE steps per iteration, one job per iteration with 20 main circuits + 2 calibration circuits, the same scripts `scripts/qpu_vs_rng.py` and `scripts/qpu_vs_rng_analyze.py`.

Run command:

```
python scripts/select_chain.py --backend ibm_kingston
python scripts/qpu_vs_rng.py --backend ibm_kingston --seed 20261109 --qubits <chain from layout_selection.json>
python scripts/qpu_vs_rng_analyze.py measurement_raw/qpu_vs_rng/<campaign>
```

## Decision rule

Identical to Phase 3: H1 is supported in the replication only if the two-sided exact sign-flip permutation p < 0.01 and mean D has the same sign in replicates 0–9 and 10–19.

**Combined conclusion (fixed now):**
- The QPU/RNG difference is claimed **only if** H1 is supported in Phase 3 **and** in this replication, **with the same sign of mean D**.
- Any other combination: the difference is not claimed, and the textbook prediction stands.

## Stopping, exclusions, reporting

As in Phase 3: no early stopping or extension; if the run breaks, all complete iterations are analysed (minimum 13); a job is excluded only if it returned no counts; all raw data, `campaign.json`, `layout_selection.json` and `analysis.json` are pushed, whatever the result.
