//! The 16 cognitive modes: centers, names, and energy decomposition.

use ndarray::Array2;
use num_complex::Complex64;
use std::f64::consts::PI;

/// Number of cognitive modes.
pub const MODE_COUNT: usize = 16;

/// Mode names (matching the Python quantum_loop_sim.py).
pub type ModeNames = [&'static str; MODE_COUNT];
pub type ModeEnergies = [f64; MODE_COUNT];

/// Human-readable mode names.
pub const MODE_NAMES: ModeNames = [
    "ground",           // 0
    "dipole-x",         // 1
    "dipole-y",         // 2
    "quadrupole-xx",    // 3
    "quadrupole-xy",    // 4
    "quadrupole-yy",    // 5
    "hexagonal",        // 6
    "septagonal",       // 7
    "octagonal-a",      // 8
    "octagonal-b",      // 9
    "ring-1",           // 10
    "ring-2",           // 11
    "vortex-1",         // 12
    "vortex-2",         // 13
    "star-6",           // 14
    "star-8",           // 15
];

/// Mode centers in (r, θ) space.
pub fn mode_centers(rmax: f64) -> [(f64, f64); MODE_COUNT] {
    let mut centers = [(0.0, 0.0); MODE_COUNT];
    for m in 0..MODE_COUNT {
        let r = (m as f64 / (MODE_COUNT - 1) as f64) * rmax;
        let theta = 2.0 * PI * m as f64 / MODE_COUNT as f64;
        centers[m] = (r, theta);
    }
    centers
}

/// Compute the energy in each of the 16 modes by projecting ψ
/// onto the angular Fourier components.
pub fn mode_energies(
    psi: &Array2<Complex64>,
    r_grid: &[f64],
    th_grid: &[f64],
    rmax: f64,
) -> ModeEnergies {
    let nr = psi.nrows();
    let nth = psi.ncols();
    let dr = rmax / nr as f64;
    let dth = 2.0 * PI / nth as f64;

    let mut energies = [0.0; MODE_COUNT];

    for m in 0..MODE_COUNT {
        let mut proj = Complex64::new(0.0, 0.0);
        for i in 0..nr {
            let r = r_grid[i];
            for j in 0..nth {
                let theta = th_grid[j];
                let basis = Complex64::new(
                    (m as f64 * theta).cos(),
                    -(m as f64 * theta).sin(),
                );
                proj += psi[[i, j]] * basis * r * dr * dth;
            }
        }
        energies[m] = proj.norm_sqr();
    }

    // Normalize so they sum to 1
    let total: f64 = energies.iter().sum();
    if total > 1e-30 {
        for e in &mut energies {
            *e /= total;
        }
    }

    energies
}
