# Preregistration: does the GPE fluid in the loop change the Bell-anchor correlation c_live?

Author: Máté Róbert (ORCID 0009-0003-3986-6039)
Repository: https://github.com/silentnoisehun/qhf-core
Date of registration: 2026-11-07 01:21:00 UTC

## Hypothesis

**H1:** When the Gross–Pitaevskii fluid is in the closed loop, the Bell-anchor correlation c = P(00) + P(11) of an H + CX circuit on a fixed physical qubit pair is higher than when the fluid is not in the loop.

**Standard quantum mechanics predicts no difference (d = 0).** The Bell circuit does not take any input from the fluid; it is the same circuit in both arms. Ideal simulation gives c = 1.0 in both arms; a noise model with ~1% readout error and ~1% two-qubit error gives c ≈ 0.973–0.975 in both arms.

## Prior data (2 November 2026, exploratory, not part of this test)

Real anchors only (the logged default value 0.965 of non-anchor iterations excluded): with fluid c = 0.9717 (n = 10), without fluid c = 0.9693 (n = 16), difference +0.0024, Welch p = 0.26. The two runs were 24 minutes apart, so calibration drift was not controlled. Per-anchor spread 0.0049, equal to 1024-shot noise.

## Design

- Script: `scripts/c_live_interleaved.py`, seed 20261107, 60 blocks (120 jobs), 1024 shots, 50 GPE steps per F iteration.
- Each block holds one F iteration (fluid steps, its parameters are encoded, the decoded values excite the fluid) and one N iteration (the main circuit runs with the last F parameters; the fluid neither steps nor is excited). The order inside each block is random (fixed seed).
- Every iteration submits the same two circuits in one job: the 3-qubit RY main circuit and the Bell anchor.
- The Bell anchor runs on the same fixed physical qubit pair in every iteration; the main circuit on a fixed 3-qubit layout. Both layouts are written to `campaign.json` before the first job.
- c is computed only from measured Bell counts. No default values.
- Backend: ibm_marrakesh (Heron r2), one session, no change of settings during the run.

## Primary analysis and decision rule (fixed now)

Script: `scripts/c_live_analyze.py`. For each complete block, d = c_F − c_N.

H1 is **supported** only if all three hold:
1. mean d ≥ 0.003
2. one-sided paired t-test p < 0.01
3. mean d > 0 in the first half and in the second half of the blocks separately

In every other case H1 is **not supported**, and the result is reported as a negative result.

## Stopping and exclusions

- The run is not stopped early because of interim results, and is not extended.
- If the run breaks (IBM error, quota), all complete blocks so far are analysed with the same rule, and the number of blocks is reported.
- A job is excluded only if it failed to return counts; every exclusion is listed.

## Controls and reporting

- A dry run with the local statevector sampler (`--dry-run`) must give d ≈ 0; it checks the pipeline, not the hypothesis.
- All raw JSON files, `campaign.json` and `analysis.json` are pushed to the repository, whatever the result.
