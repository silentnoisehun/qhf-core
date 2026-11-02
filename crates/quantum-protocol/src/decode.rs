//! Quantum decoding: measured bit counts / probabilities -> (A, f, phi) parameters.
//!
//! Canonical single source of truth for parameter decoding from physical
//! computational-basis readout probabilities.

use std::f64::consts::PI;

/// Maximum modal frequency scaling factor in GPE fluid solver.
pub const DEFAULT_FREQ_MAX: f64 = 15.0;

/// Decode amplitude A from P(q0 = 1):
/// A = 2 * arcsin(sqrt(P(q0=1)))
/// Equivalent to 2 * arccos(sqrt(P(q0=0))) for pure states.
pub fn decode_amplitude(p1: f64) -> f64 {
    let p_clamped = p1.clamp(0.0, 1.0);
    2.0 * p_clamped.sqrt().asin()
}

/// Decode amplitude A from ground-state probability P(q0 = 0).
pub fn decode_amplitude_from_p0(p0: f64) -> f64 {
    let p_clamped = p0.clamp(0.0, 1.0);
    2.0 * p_clamped.sqrt().acos()
}

/// Decode normalized frequency f_norm in [0, 0.5] from P(q1 = 1):
/// f_norm = arcsin(sqrt(P(q1=1))) / pi
pub fn decode_frequency_norm(p1: f64) -> f64 {
    let p_clamped = p1.clamp(0.0, 1.0);
    p_clamped.sqrt().asin() / PI
}

/// Decode scaled physical frequency f in [0, freq_max] from P(q1 = 1):
/// f = (arcsin(sqrt(P(q1=1))) / pi) * freq_max
pub fn decode_frequency_scaled(p1: f64, freq_max: f64) -> f64 {
    decode_frequency_norm(p1) * freq_max
}

/// Default physical frequency decoder scaled to [0, 15.0].
pub fn decode_frequency(p1: f64) -> f64 {
    decode_frequency_scaled(p1, DEFAULT_FREQ_MAX)
}

/// Decode phase phi in [0, 1.0] from P(q2 = 1) assuming non-folding RY(pi * phi):
/// phi = arcsin(sqrt(P(q2=1))) / (pi / 2.0) = 2.0 * arcsin(sqrt(P(q2=1))) / pi
pub fn decode_phase(p1: f64) -> f64 {
    let p_clamped = p1.clamp(0.0, 1.0);
    2.0 * p_clamped.sqrt().asin() / PI
}

/// Decode complete wavepacket (A, f, phi) from raw probability observations.
pub fn decode_wave(p_amp_1: f64, p_freq_1: f64, p_phase_1: f64) -> (f64, f64, f64) {
    (
        decode_amplitude(p_amp_1),
        decode_frequency(p_freq_1),
        decode_phase(p_phase_1),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_amplitude_roundtrip() {
        for a in [0.0f64, 0.25, 0.5, 0.75, 1.0] {
            let p1: f64 = (a / 2.0).sin().powi(2);
            let decoded = decode_amplitude(p1);
            assert!((decoded - a).abs() < 1e-10);
        }
    }

    #[test]
    fn test_frequency_scaled_roundtrip() {
        for f in [0.0f64, 1.5, 3.75, 7.5] {
            let p1: f64 = (PI * (f / DEFAULT_FREQ_MAX)).sin().powi(2);
            let decoded = decode_frequency(p1);
            assert!((decoded - f).abs() < 1e-10);
        }
    }

    #[test]
    fn test_phase_unfolding_roundtrip() {
        for phi in [0.0f64, 0.2, 0.5, 0.8, 1.0] {
            let theta = PI * phi / 2.0; // from RY(pi*phi)
            let p1: f64 = theta.sin().powi(2);
            let decoded = decode_phase(p1);
            assert!((decoded - phi).abs() < 1e-10);
        }
    }
}
