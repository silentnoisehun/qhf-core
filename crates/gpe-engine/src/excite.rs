//! The `excite(ψ, A, f, φ)` function — inject quantum feedback into the fluid.
//!
//! This is the CORRECTED version (2026-11-02):
//! - Frequency coordinate properly normalized: target_rad = (f / F_MODE_INDEX_MAX) * RMAX
//! - Angular wrapping applied BEFORE hypot, not after

use ndarray::Array2;
use num_complex::Complex64;
use std::f64::consts::PI;

use crate::modes::{mode_centers, MODE_COUNT};

/// Maximum frequency mode index (0..15).
pub const F_MODE_INDEX_MAX: f64 = 15.0;

/// Excite the fluid wavefunction with quantum feedback (A, f, φ).
///
/// - `A`: amplitude feedback ∈ [0, 1]
/// - `f`: frequency mode index ∈ [0, 15]
/// - `phi`: phase feedback ∈ [0, 1]
pub fn excite(
    psi: &mut Array2<Complex64>,
    a: f64,
    f: f64,
    phi: f64,
    rmax: f64,
) {
    let nr = psi.nrows();
    let nth = psi.ncols();
    let dr = rmax / nr as f64;
    let dth = 2.0 * PI / nth as f64;

    // Target position in (r, θ) from the feedback
    let target_rad = (f / F_MODE_INDEX_MAX) * rmax;  // FIXED: proper normalization
    let target_theta = phi * 2.0 * PI;

    // Find the nearest mode center
    let centers = mode_centers(rmax);
    let mut best_mode = 0;
    let mut best_dist = f64::INFINITY;

    for (m, &(cr, cth)) in centers.iter().enumerate() {
        let d_rad = target_rad - cr;
        // Angular wrapping BEFORE hypot (FIXED: 2026-11-02)
        let mut d_ang = (target_theta - cth).abs();
        if d_ang > PI {
            d_ang = 2.0 * PI - d_ang;
        }
        let dist = (d_rad * d_rad + d_ang * d_ang).sqrt();
        if dist < best_dist {
            best_dist = dist;
            best_mode = m;
        }
    }

    // Apply Gaussian excitation around the nearest mode center
    let (center_r, center_th) = centers[best_mode];
    let sigma = rmax * 0.15;
    let amplitude = a * 0.1; // Scale down to prevent instability

    for i in 0..nr {
        let r = (i as f64 + 0.5) * dr;
        for j in 0..nth {
            let theta = j as f64 * dth;

            let d_r = r - center_r;
            let mut d_th = (theta - center_th).abs();
            if d_th > PI {
                d_th = 2.0 * PI - d_th;
            }

            let dist2 = d_r * d_r + d_th * d_th;
            let excitation = amplitude * (-dist2 / (2.0 * sigma * sigma)).exp();
            let phase = phi * 2.0 * PI;

            psi[[i, j]] += Complex64::new(
                excitation * phase.cos(),
                excitation * phase.sin(),
            );
        }
    }
}
