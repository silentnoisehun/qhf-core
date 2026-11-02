//! Quantum decoding: measured bit counts / probabilities -> (A, f, phi) parameters.

use std::f64::consts::PI;

/// Decode amplitude A from P(q0 = 0):
/// A = 2 * arccos(sqrt(P(q0=0)))
pub fn decode_amplitude(p0: f64) -> f64 {
    let p_clamped = p0.clamp(0.0, 1.0);
    2.0 * p_clamped.sqrt().acos()
}

/// Decode frequency f from P(q0 = 1):
/// f = arcsin(sqrt(P(q0=1))) / pi
pub fn decode_frequency(p1: f64) -> f64 {
    let p_clamped = p1.clamp(0.0, 1.0);
    p_clamped.sqrt().asin() / PI
}

/// Decode phase phi from P(q0 = 1):
/// phi = 2 * arcsin(sqrt(P(q0=1)))
pub fn decode_phase(p1: f64) -> f64 {
    let p_clamped = p1.clamp(0.0, 1.0);
    2.0 * p_clamped.sqrt().asin()
}

/// Decode complete wavepacket (A, f, phi) from raw probability observations.
pub fn decode_wave(p_amp_0: f64, p_freq_1: f64, p_phase_1: f64) -> (f64, f64, f64) {
    (
        decode_amplitude(p_amp_0),
        decode_frequency(p_freq_1),
        decode_phase(p_phase_1),
    )
}
