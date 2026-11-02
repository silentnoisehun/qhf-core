//! Quantum encoding: wavepacket parameters -> circuit rotation angles.
//!
//! Pairs strictly with `decode.rs` to form an unentangled, invertible
//! 3-channel parameter transceiver without marginal crosstalk.

use std::f64::consts::PI;
use crate::decode::DEFAULT_FREQ_MAX;

/// Encode amplitude A in [0, 1] -> RY rotation angle.
/// RY(A) |0> -> cos(A/2)|0> + sin(A/2)|1> => P(1) = sin^2(A/2)
pub fn encode_amplitude(a: f64) -> f64 {
    a
}

/// Encode frequency f in [0, freq_max] -> RY rotation angle.
/// RY(pi * f / freq_max) |0> => P(1) = sin^2(pi*f / (2*freq_max))
pub fn encode_frequency_scaled(f: f64, freq_max: f64) -> f64 {
    2.0 * PI * (f / freq_max)
}

/// Default frequency encoder for [0, 15.0].
pub fn encode_frequency(f: f64) -> f64 {
    encode_frequency_scaled(f, DEFAULT_FREQ_MAX)
}

/// Encode phase phi in [0, 1.0] -> RY rotation angle.
/// Non-folding bijection over [0, 1]: RY(pi * phi) |0> => P(1) = sin^2(pi*phi / 2)
pub fn encode_phase(phi: f64) -> f64 {
    PI * phi
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::decode::{decode_amplitude, decode_frequency, decode_phase};

    #[test]
    fn test_end_to_end_transceiver() {
        let (a, f, phi) = (0.85, 3.25, 0.42);
        
        let theta_a = encode_amplitude(a);
        let p_a = (theta_a / 2.0).sin().powi(2);
        assert!((decode_amplitude(p_a) - a).abs() < 1e-10);

        let theta_f = encode_frequency(f);
        let p_f = (theta_f / 2.0).sin().powi(2);
        assert!((decode_frequency(p_f) - f).abs() < 1e-10);

        let theta_phi = encode_phase(phi);
        let p_phi = (theta_phi / 2.0).sin().powi(2);
        assert!((decode_phase(p_phi) - phi).abs() < 1e-10);
    }
}
