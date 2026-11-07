# Preregistration: Phase 5 — Angle-Resolved SPAM Calibration & Coherent Over-rotation Test

**Author:** Máté Róbert (ORCID: [0009-0003-3986-6039](https://orcid.org/0009-0003-3986-6039))  
**Affiliation:** Silent Coder Labs  
**Repository:** `https://github.com/silentnoisehun/qhf-bell-spectator`  
**Date:** 2026-11-07  
**Status:** Frozen prior to quantum execution  

---

## 1. Background & Scientific Question

In Phase 3 (`ibm_marrakesh`, qubits [53, 54, 55]), the primary test confirmed that the GPE fluid centroid $D(f)$ is consistent with the null hypothesis ($p = 0.411$). However, secondary metrics exhibited a strong apparent divergence ($p < 0.0001$), driven by an intermediate-angle residual bias $\Delta p \approx +0.014$ on Q53 and $+0.008$ on Q55 at intermediate rotation angles ($\theta \approx \pi/2$), whereas standard calibration at the computational poles ($\theta \in \{0, \pi\}$) reported readout errors below $1.5\%$.

In Phase 4 (`ibm_kingston`, qubits [48, 49, 50]), all secondary metrics collapsed completely to null ($p = 0.41 - 0.52$), and the intermediate-angle residuals dropped by an order of magnitude ($-0.0015$ to $+0.0032$).

**The Core Mechanistic Question:**
Is the intermediate-angle bias observed on `ibm_marrakesh` caused by:
1. **Hypothesis A (Coherent Microwave Over-rotation / Rabi Calibration Error):** A systematic pulse amplitude/length calibration error $\theta \to \theta + \delta\theta$, where the residual $\Delta p(\theta) = p_{\text{meas}}(\theta) - \sin^2(\theta/2)$ follows a $\frac{1}{2}\sin\theta$ derivative profile peaking at $\theta = \pi/2$; OR
2. **Hypothesis B (Nonlinear State-Dependent Readout Error):** A measurement confusion effect that scales monotonically with excited state population $|1\rangle$, departing from simple linear readout inversion; OR
3. **Hypothesis C (Spectator / Cross-Talk Induced Shift):** An effect appearing only when neighboring qubits are driven simultaneously, absent in isolated single-qubit rotations.

---

## 2. Experimental Design

### 2.1 Rotation Angles
We probe 9 discrete rotation angles spanning the full Bloch sphere meridian:
$$\theta_k \in \left\{ 0, \; \frac{\pi}{6}, \; \frac{\pi}{4}, \; \frac{\pi}{3}, \; \frac{\pi}{2}, \; \frac{2\pi}{3}, \; \frac{3\pi}{4}, \; \frac{5\pi}{6}, \; \pi \right\}$$

### 2.2 Circuit Configurations
For each target backend, we evaluate two execution regimes across the 9 angles:
1. **Isolated Mode:** $R_y(\theta)$ is applied to a single transmon while all other transmons remain unaddressed in the ground state. Probed for each qubit individually (3 qubits $\times$ 9 angles = 27 circuits).
2. **Simultaneous Mode:** $R_y(\theta)$ is applied synchronously to all 3 transmons in parallel, identical to the driving conditions of Phase 3 and Phase 4 (9 circuits).

Total circuits per backend: $27 + 9 = 36$ circuits.  
Shots: 4096 shots per circuit.

### 2.3 Physical Backends & Layouts
- **Primary Target (The Divergent Chip):** `ibm_marrakesh`, physical transmons `[53, 54, 55]`.
- **Secondary Target (The Baseline Chip):** `ibm_kingston`, physical transmons `[48, 49, 50]`.
- **Credentials:** `apikey (5).json` (active open-instance with remaining execution budget).

---

## 3. Mathematical Models & Explicit Predictions

### 3.1 Model 0: Pure Readout Baseline (Pole Inversion)
Given empirical error rates $\epsilon_0 = p(1|0)$ and $\epsilon_1 = p(0|1)$ measured at $\theta=0$ and $\theta=\pi$:
$$p_{\text{model}, 0}(\theta) = (1 - \epsilon_1) \sin^2\left(\frac{\theta}{2}\right) + \epsilon_0 \cos^2\left(\frac{\theta}{2}\right)$$
Residual:
$$\Delta p_0(\theta) = p_{\text{meas}}(\theta) - p_{\text{model}, 0}(\theta)$$

### 3.2 Model 1: Coherent Over-rotation ($\delta\theta$)
If the microwave drive implements $R_y(\theta + \delta\theta)$ with coherent miscalibration $\delta\theta$:
$$p_{\text{model}, 1}(\theta) = \sin^2\left(\frac{\theta + \delta\theta}{2}\right) \approx \sin^2\frac{\theta}{2} + \frac{1}{2}\sin\theta \cdot \delta\theta$$
The signature of coherent over-rotation is:
1. $\Delta p_0(0) \approx 0$ and $\Delta p_0(\pi) \approx 0$.
2. $\Delta p_0(\theta)$ is strictly positive (for over-rotation) or negative (for under-rotation) with maximum magnitude at $\theta = \pi/2$.
3. Fitted $\delta\theta \approx 2 \cdot \Delta p_0(\pi/2)$ matches the Phase 3 shift ($\approx +0.028 \text{ rad} \approx 1.6^\circ$ on Q53).

### 3.3 Model 2: Cross-Talk / Spectator Coupling
$$\Delta p_{\text{cross}}(\theta) = p_{\text{simultaneous}}(\theta) - p_{\text{isolated}}(\theta)$$
If spectator driving causes frequency shifts (AC Stark or $ZZ$ interaction), $\Delta p_{\text{cross}}(\theta)$ will be statistically significant ($p < 0.01$). If isolated and simultaneous match ($\Delta p_{\text{cross}} \approx 0$), cross-talk is excluded.

---

## 4. Pre-Determined Decision Rules

1. **Confirmation of Coherent Over-rotation:**
   If the residual profile $\Delta p_0(\theta)$ on `ibm_marrakesh` Q53/Q55 has a goodness-of-fit $R^2 > 0.85$ to the $\sin(\theta)$ template, with peak $|\Delta p_0(\pi/2)| > 0.008$ and $\delta\theta > 0$, the Phase 3 secondary divergence is **formally classified as single-qubit microwave pulse over-rotation**.
2. **Confirmation of Cross-Talk:**
   If $\Delta p_{\text{cross}}(\pi/2) > 0.005$ with $p < 0.01$, the effect is classified as spectator cross-talk.
3. **Cross-Backend Attribution:**
   If `ibm_kingston` exhibits $|\Delta p_0(\pi/2)| < 0.003$ ($5\times$ smaller than Marrakesh), this confirms that the difference between Phase 3 and Phase 4 was entirely driven by backend microwave calibration drift.

---

## 5. Protocol Constraints
- No circuit or analysis modifications after execution commences.
- All raw Qiskit job IDs, calibration snapshots, and full measurement counts will be committed to `measurement_raw/angle_calibration/`.
