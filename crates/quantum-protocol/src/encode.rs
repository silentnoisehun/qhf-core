//! Quantum encoding: wavepacket parameters → circuit rotation angles.

/// Encode amplitude A → RY rotation angle.
pub fn encode_amplitude(a: f64) -> f64 {
    a  // RY(A) → P(q₀=1) = sin²(A/2)
}

/// Encode frequency f → RY rotation angle for 2-qubit circuit.
pub fn encode_frequency(f: f64) -> f64 {
    2.0 * std::f64::consts::PI * f  // RY(2πf) + CNOT → P(q₀=1) = sin²(πf)
}

/// Encode phase φ → RY rotation angle for 2-qubit circuit.
pub fn encode_phase(phi: f64) -> f64 {
    phi  // RY(φ) + CNOT → P(q₀=1) = sin²(φ/2)
}
