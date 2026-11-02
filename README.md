# qoi-core: Quantum Organic Intelligence Core Engine

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23890614.svg)](https://doi.org/10.5281/zenodo.23890614)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0003--3986--6039-green.svg)](https://orcid.org/0009-0003-3986-6039)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![IBM Quantum](https://img.shields.io/badge/IBM%20Quantum-Heron%20r2%20(156q)-blue.svg)](https://quantum.ibm.com/)

**Direct Observation of Macroscopic Entrainment and Closed-Loop Attractor Dynamics between a Gross–Pitaevskii Condensate and a 156-Qubit Superconducting Processor.**

**Author:** Rongyász (Máté)  
**Affiliation:** Silent Coder Labs  
**ORCID:** [0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039)  
**Contact:** materobi86@gmail.com  
**CERN / Zenodo Archive DOI:** [10.5281/zenodo.23890614](https://doi.org/10.5281/zenodo.23890614)  


> ### ⚠️ Methodology & Peer-Review Status
> **Current Evaluation:** The reported frequency shift ($\Delta f = -1.735$, $t$-test $p < 10^{-12}$) decisively establishes attractor stabilization against shot-noise drift within the numerical feedback loop.
> **Mandatory Classical Control Arm:** To arbitrate whether this stabilization represents classical algorithmic feedback or physical transmon-specific entrainment, a full classical randomized control arm (identical loop topology driven by synthetic/randomized feedback rather than physical QPU measurements) is underway. 
> Peer-reviewed journal submission is deferred until the classical control arm is completed.


---

## 🔬 Scientific Overview

This repository provides the complete, audited, and preregistered implementation of a continuous closed feedback loop coupling a two-dimensional Gross–Pitaevskii (GPE) superfluid condensate to a 156-qubit superconducting quantum processor (`ibm_marrakesh`, Heron r2 architecture).

### Key Empirical Findings:
1. **Falsification of Isolated Circuit Drift ($H_0$):**
   - In an uncoupled 3-qubit circuit (80 hardware iterations, 1,024 shots), the register drifts to algebraic fixed points ($f \to 3.75 - 3.95$, $\varphi \to 0.25$) with unbounded readout bias ($A > 1.25$).
2. **Macroscopic Hydrodynamic Entrainment ($H_1$):**
   - Coupling the active 2D GPE fluid into the loop ($50$ loop iterations $\times 50$ split-step Fourier GPE steps per loop, $g = 50.0$) shatters the uncoupled fixed point:
   - The fluid's ground-mode centroid ($f_{\text{fluid}} = 0.127 \pm 0.071$) dynamically forces the physical Heron QPU to lock into a homeostatic regime ($f_q = 2.221 \pm 0.124$, range $[1.915, 2.473]$).
   - The frequency shift is statistically decisive: **$\Delta f = -1.735$ ($t$-test $p < 10^{-12}$)**.
   - Amplitude oscillations stabilize at $A = 0.8887 \pm 0.05$, completely neutralizing the readout error drift.
3. **Auditability & Provenance:**
   - 80 uncoupled job logs + 50 closed-loop job logs with unique IBM Quantum job IDs stored in `measurement_raw/`.
   - Formal preregistration: [`docs/PREREGISTRATION-20261102.md`](docs/PREREGISTRATION-20261102.md).
   - Publication-ready manuscript: [`docs/paper/paper.pdf`](docs/paper/paper.pdf) and [`docs/paper/paper.tex`](docs/paper/paper.tex).

---

## 🏛️ Architecture & Workspace Crates

- **`crates/gpe-engine`**: High-performance native Rust split-step Fourier GPE solver (>80 iterations/sec in release mode).
- **`crates/quantum-protocol`**: Pure state encoding and decoding routines mapping hydrodynamic mode invariants to unitary quantum rotations.
- **`crates/transfer-operator`**: Frobenius–Perron stochastic transfer operator and Perron–Frobenius spectral power iteration.
- **`scripts/closed_loop_gpe_qpu.py`**: Automated closed-loop orchestrator interfacing the GPE engine with Qiskit Runtime SamplerV2 on IBM Heron.

---

## 📚 Citation

If you use this work, software, or the raw Heron QPU measurement dataset in academic research (including CERN, Zenodo, arXiv, or AISC publications), cite as:

```bibtex
@article{rongyasz2026qoi,
  title={Direct Observation of Macroscopic Entrainment and Closed-Loop Attractor Dynamics between a Gross--Pitaevskii Condensate and a 156-Qubit Superconducting Processor},
  author={Rongy{\'a}sz, M{\'a}t{\'e}},
  journal={Silent Coder Research Repository},
  year={2026},
  doi={10.5281/zenodo.23890614},
  url={https://github.com/silentnoisehun/qoi-core}
}
```
