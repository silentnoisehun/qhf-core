//! # GPE Engine — Split-Step Fourier Gross–Pitaevskii Solver
//!
//! A native Rust implementation of the 16-mode cognitive fluid,
//! with a real split-step Fourier kinetic step (RustFFT 6.x) and
//! Strang-style time stepping.
//!
//! ## Architecture
//!
//! The wavefunction ψ lives on a polar (r, θ) grid of size `NR × NTH`.
//! The 16 modes are the energy-weighted eigenstates of the trapping
//! potential V(r, θ) = r² + Σ_m α_m cos(m·θ).
//!
//! Each GPE step:
//! 1. Half-step potential: ψ ← ψ · exp(-i·dt/2 · (V + g|ψ|²))
//! 2. Full kinetic step in Fourier space (FFT → multiply → IFFT)
//! 3. Half-step potential again (Strang splitting)
//!
//! The `excite(ψ, A, f, φ)` function injects quantum feedback
//! into the nearest mode center with correct radial normalization
//! and angular wrapping.

mod fluid;
mod modes;
mod excite;
mod metrics;

pub use fluid::{Fluid, FluidConfig, GpeStep};
pub use modes::{ModeEnergies, ModeNames, MODE_COUNT, mode_energies, mode_centers};
pub use excite::excite;
pub use metrics::{Metrics, metrics};
