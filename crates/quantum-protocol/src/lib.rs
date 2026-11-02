//! # Quantum Protocol — Encoding, Decoding, and QPU Bridge
//!
//! The encoding scheme for the (A, f, φ) wavepacket parameters:
//! - A (amplitude): RY(A) → P(q₀=1) = sin²(A/2)
//! - f (frequency): RY(2πf) + CNOT → P(q₀=1) = sin²(πf)
//! - φ (phase): RY(φ) + CNOT → P(q₀=1) = sin²(φ/2)

pub mod encode;
pub mod decode;

pub use encode::{encode_amplitude, encode_frequency, encode_phase};
pub use decode::{decode_amplitude, decode_frequency, decode_phase, decode_wave};
