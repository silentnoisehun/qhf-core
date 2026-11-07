# Preregistration: does a QPU-fed Gross–Pitaevskii fluid behave differently from a fluid fed by a noise-matched classical random generator?

Author: Máté Róbert (ORCID 0009-0003-3986-6039)  
Repository: https://github.com/silentnoisehun/qhf-bell-spectator  
Date of initial registration: 2026-11-07 03:15:00 UTC (04:15 CET) (commit `e358105` before any hardware run)  
Date of Amendment 1: 2026-11-07 03:22:00 UTC (04:22 CET) (commit before any hardware run)

## Hypothesis

**H1:** A Gross–Pitaevskii fluid whose feedback comes from real QPU measurements (arm Q) evolves differently from an identical fluid, started from the same initial state, whose feedback comes from a classical binomial random generator with the same encoding and the same, in-situ measured readout error (arm C).

**Standard quantum mechanics predicts no difference beyond noise.** QPU measurement outcomes of single-qubit RY states are binomial samples of $\sin^2(\theta/2)$, distorted by readout error. A classical generator that samples the same probabilities with the same readout error produces statistically identical marginals, so the two fluids are statistically indistinguishable.

Direction is not predicted; the test is two-sided.

## Design

- Scripts: `scripts/qpu_vs_rng.py` and `scripts/qpu_vs_rng_analyze.py`, seed 20261108.
- $R = 20$ replicates, 40 iterations, 1024 shots, 50 GPE steps per iteration, fixed layout `[53, 54, 55]` on `ibm_marrakesh` (see Amendment 1).
- Each replicate holds two fluids with the same seed (identical initial state): Q and C.
- One job per iteration: the 20 main circuits built from the Q fluids' parameters, plus two calibration circuits ($|000\rangle$ and $|111\rangle$) on the same physical qubits. 40 jobs in total.
- Arm Q: the measured per-qubit marginals are decoded and excite the Q fluid.
- Arm C: the ideal probabilities $\sin^2(\theta/2)$ from the C fluid's own parameters are distorted with the readout error measured in the same job ($P(1|0)$, $P(0|1)$ per qubit), sampled binomially with the same number of shots, decoded the same way, and excite the C fluid.
- The decoder uses only per-qubit marginals, so independent per-qubit binomial sampling in arm C is exact for what the fluid receives.
- Calibration timestamps at the start and end of the run are saved in `campaign.json`.

## Amendment 1 (Pre-Execution Hardware Audit)

- **Qubit Layout Selection:** In the initial registration, layout `[51, 52, 53]` was specified. The live calibration on `ibm_marrakesh` revealed that physical qubit 51 exhibits a 15.9% readout error ($P(\text{err}) = 0.159$). Transmons with ~16% readout error are prone to within-job fluctuations, which could introduce spurious drifts between calibration circuits and main circuits. To ensure rigorous, artifact-free execution, the layout is reassigned to the ultra-low-noise chain **`[53, 54, 55]`**:
  - Q53 readout error: $1.8\%$ ($0.0176$)
  - Q54 readout error: $0.5\%$ ($0.0049$)
  - Q55 readout error: $0.4\%$ ($0.0044$)
  All three physical qubits operate with $<1.8\%$ readout error, expected to give sub-percent stability between the calibration circuits and the 20 replicate circuits.
- **Timestamp correction:** The initial registration timestamp was recorded in CET (04:15) but labeled UTC; the corrected UTC timestamp is 03:15 UTC.

## Primary analysis and decision rule (fixed now)

Unit: the replicate. For each replicate $r$, $D_r = \text{mean } f_Q - \text{mean } f_C$ over iterations 11–40 (burn-in 10), where $f$ is the fluid's mode centroid from `extract_modal_parameters`.

Note: in pilot simulations the dominant mode index stays 0 in every iteration, so the mode index itself is uninformative; the continuous centroid $f$ is used instead.

Primary test: exact two-sided sign-flip permutation test on mean $D$ ($2^{20}$ sign assignments = 1,048,576 permutations).

H1 is **supported** only if both hold:
1. two-sided permutation $p < 0.01$
2. mean $D$ has the same sign in replicates 0–9 and in replicates 10–19

In every other case H1 is **not supported** and the textbook prediction stands.

## Secondary analyses (reported, not decisive)

Mean amplitude $A$, circular standard deviation of $\phi$, lag-1 autocorrelation of $f$, each as $Q - C$ per replicate with the same permutation test. With several secondary metrics, a single $p < 0.05$ among them is expected by chance and is not evidence for H1. In the pilot dry run, where both arms are classical by construction, one secondary metric gave $p = 0.022$.

## Sensitivity

In the dry run the replicate-level spread was $\text{sd}(D) \approx 0.013$, so the test can detect a mean shift of roughly 0.009 in $f$ (about 5% of its typical value) at $p < 0.01$.

## Stopping, exclusions, replication

- No early stopping on interim results, no extension.
- If the run breaks, all complete iterations are analysed with the same rule (minimum 13 iterations), and the number is reported.
- A job is excluded only if it returned no counts; every exclusion is listed.
- **A supported H1 counts as evidence only after a replication run on a second backend (e.g. ibm_kingston) with a fresh preregistration and the same rule.**

## Reporting

All raw JSON files, `campaign.json` and `analysis.json` are pushed to the repository, whatever the result.
