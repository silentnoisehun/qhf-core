//! The GPE fluid state and split-step Fourier time stepper.

use ndarray::Array2;
use num_complex::Complex64;
use rustfft::{FftPlanner, num_complex::Complex as RComplex};
use serde::{Serialize, Deserialize};
use std::f64::consts::PI;

/// Grid and physics configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FluidConfig {
    /// Radial grid points.
    pub nr: usize,
    /// Angular grid points.
    pub nth: usize,
    /// Maximum radius.
    pub rmax: f64,
    /// Time step.
    pub dt: f64,
    /// Nonlinear coupling g.
    pub g: f64,
    /// Harmonic trap frequency (ω).
    pub omega: f64,
}

impl Default for FluidConfig {
    fn default() -> Self {
        Self {
            nr: 64,
            nth: 64,
            rmax: 8.0,
            dt: 0.002,
            g: 50.0,
            omega: 1.0,
        }
    }
}

/// The GPE fluid — owns the wavefunction and the FFT planners.
pub struct Fluid {
    pub config: FluidConfig,
    /// The wavefunction ψ(r, θ) as a complex 2D array [nr × nth].
    pub psi: Array2<Complex64>,
    /// Radial coordinates.
    pub r_grid: Vec<f64>,
    /// Angular coordinates.
    pub th_grid: Vec<f64>,
    /// Trapping potential V(r, θ).
    pub potential: Array2<f64>,
    /// Kinetic propagator in Fourier space.
    kinetic_prop: Array2<Complex64>,
}

/// One GPE step result.
pub struct GpeStep {
    pub mode_argmax: usize,
    pub coherence: f64,
}

impl Fluid {
    /// Create a new fluid with given configuration and seed for initial state.
    pub fn new(config: FluidConfig, seed: u64) -> Self {
        let nr = config.nr;
        let nth = config.nth;
        let dr = config.rmax / nr as f64;
        let dth = 2.0 * PI / nth as f64;

        // Radial and angular grids
        let r_grid: Vec<f64> = (0..nr).map(|i| (i as f64 + 0.5) * dr).collect();
        let th_grid: Vec<f64> = (0..nth).map(|j| j as f64 * dth).collect();

        // Trapping potential: harmonic V = ω² r²
        let mut potential = Array2::zeros((nr, nth));
        for i in 0..nr {
            let r = r_grid[i];
            for j in 0..nth {
                potential[[i, j]] = config.omega * config.omega * r * r;
            }
        }

        // Initial wavefunction: Gaussian ground state with seeded perturbation
        let mut psi = Array2::zeros((nr, nth));
        let mut rng_state = seed;
        for i in 0..nr {
            let r = r_grid[i];
            let gauss = (-r * r / 4.0).exp();
            for j in 0..nth {
                // Simple LCG-based perturbation for reproducibility
                rng_state = rng_state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
                let phase = (rng_state >> 33) as f64 / (1u64 << 31) as f64 * 2.0 * PI;
                let perturbation = 0.01 * Complex64::new(phase.cos(), phase.sin());
                psi[[i, j]] = Complex64::new(gauss, 0.0) + perturbation * gauss;
            }
        }

        // Normalize
        let norm: f64 = psi.iter()
            .enumerate()
            .map(|(idx, &v)| {
                let i = idx / nth;
                let r = r_grid[i];
                v.norm_sqr() * r * dr * dth
            })
            .sum::<f64>()
            .sqrt();
        if norm > 1e-15 {
            psi.mapv_inplace(|v| v / norm);
        }

        // Kinetic propagator in Fourier space
        let kinetic_prop = Self::build_kinetic_propagator(nr, nth, config.rmax, config.dt);

        Self {
            config,
            psi,
            r_grid,
            th_grid,
            potential,
            kinetic_prop,
        }
    }

    fn build_kinetic_propagator(nr: usize, nth: usize, rmax: f64, dt: f64) -> Array2<Complex64> {
        let dr = rmax / nr as f64;
        let mut prop = Array2::zeros((nr, nth));

        for i in 0..nr {
            let kr = if i <= nr / 2 {
                2.0 * PI * i as f64 / (nr as f64 * dr)
            } else {
                2.0 * PI * (i as f64 - nr as f64) / (nr as f64 * dr)
            };
            for j in 0..nth {
                let kth = if j <= nth / 2 {
                    j as f64
                } else {
                    j as f64 - nth as f64
                };
                let k2 = kr * kr + kth * kth;
                let phase = -0.5 * k2 * dt;
                prop[[i, j]] = Complex64::new(phase.cos(), phase.sin());
            }
        }
        prop
    }

    /// Perform one Strang split-step:
    /// half potential → full kinetic (FFT) → half potential.
    pub fn gpe_step(&mut self) -> GpeStep {
        let nr = self.config.nr;
        let nth = self.config.nth;
        let dt = self.config.dt;
        let g = self.config.g;

        // Half-step potential
        for i in 0..nr {
            for j in 0..nth {
                let v = self.potential[[i, j]];
                let density = self.psi[[i, j]].norm_sqr();
                let phase = -0.5 * dt * 0.5 * (v + g * density);
                self.psi[[i, j]] *= Complex64::new(phase.cos(), phase.sin());
            }
        }

        // Forward FFT (row-by-row, then column-by-column)
        self.fft2d_forward();

        // Kinetic propagator in Fourier space
        for i in 0..nr {
            for j in 0..nth {
                self.psi[[i, j]] *= self.kinetic_prop[[i, j]];
            }
        }

        // Inverse FFT
        self.fft2d_inverse();

        // Half-step potential again
        for i in 0..nr {
            for j in 0..nth {
                let v = self.potential[[i, j]];
                let density = self.psi[[i, j]].norm_sqr();
                let phase = -0.5 * dt * 0.5 * (v + g * density);
                self.psi[[i, j]] *= Complex64::new(phase.cos(), phase.sin());
            }
        }

        let energies = crate::mode_energies(&self.psi, &self.r_grid, &self.th_grid, self.config.rmax);
        let mode_argmax = energies.iter()
            .enumerate()
            .max_by(|(_, a), (_, b)| a.partial_cmp(b).unwrap())
            .map(|(i, _)| i)
            .unwrap_or(0);
        let coherence = self.coherence();

        GpeStep { mode_argmax, coherence }
    }

    fn fft2d_forward(&mut self) {
        let nr = self.config.nr;
        let nth = self.config.nth;
        let mut planner = FftPlanner::<f64>::new();
        let fft_r = planner.plan_fft_forward(nr);
        let fft_th = planner.plan_fft_forward(nth);

        // FFT along rows (θ direction)
        for i in 0..nr {
            let mut row: Vec<RComplex<f64>> = (0..nth)
                .map(|j| {
                    let c = self.psi[[i, j]];
                    RComplex::new(c.re, c.im)
                })
                .collect();
            fft_th.process(&mut row);
            for j in 0..nth {
                self.psi[[i, j]] = Complex64::new(row[j].re, row[j].im);
            }
        }

        // FFT along columns (r direction)
        for j in 0..nth {
            let mut col: Vec<RComplex<f64>> = (0..nr)
                .map(|i| {
                    let c = self.psi[[i, j]];
                    RComplex::new(c.re, c.im)
                })
                .collect();
            fft_r.process(&mut col);
            for i in 0..nr {
                self.psi[[i, j]] = Complex64::new(col[i].re, col[i].im);
            }
        }
    }

    fn fft2d_inverse(&mut self) {
        let nr = self.config.nr;
        let nth = self.config.nth;
        let mut planner = FftPlanner::<f64>::new();
        let ifft_r = planner.plan_fft_inverse(nr);
        let ifft_th = planner.plan_fft_inverse(nth);
        let scale = 1.0 / (nr as f64 * nth as f64);

        // IFFT along columns
        for j in 0..nth {
            let mut col: Vec<RComplex<f64>> = (0..nr)
                .map(|i| {
                    let c = self.psi[[i, j]];
                    RComplex::new(c.re, c.im)
                })
                .collect();
            ifft_r.process(&mut col);
            for i in 0..nr {
                self.psi[[i, j]] = Complex64::new(col[i].re * scale.sqrt(), col[i].im * scale.sqrt());
            }
        }

        // IFFT along rows
        for i in 0..nr {
            let mut row: Vec<RComplex<f64>> = (0..nth)
                .map(|j| {
                    let c = self.psi[[i, j]];
                    RComplex::new(c.re, c.im)
                })
                .collect();
            ifft_th.process(&mut row);
            for j in 0..nth {
                self.psi[[i, j]] = Complex64::new(row[j].re * scale.sqrt(), row[j].im * scale.sqrt());
            }
        }
    }

    /// Wavefunction coherence (normalized overlap with ground state).
    pub fn coherence(&self) -> f64 {
        let nr = self.config.nr;
        let nth = self.config.nth;
        let dr = self.config.rmax / nr as f64;
        let dth = 2.0 * PI / nth as f64;

        let mut overlap = Complex64::new(0.0, 0.0);
        let mut norm_psi = 0.0;
        let mut norm_ground = 0.0;

        for i in 0..nr {
            let r = self.r_grid[i];
            let gauss = (-r * r / 4.0).exp();
            let w = r * dr * dth;
            for j in 0..nth {
                let psi_val = self.psi[[i, j]];
                let ground = Complex64::new(gauss, 0.0);
                overlap += psi_val.conj() * ground * w;
                norm_psi += psi_val.norm_sqr() * w;
                norm_ground += ground.norm_sqr() * w;
            }
        }

        if norm_psi < 1e-30 || norm_ground < 1e-30 {
            return 0.0;
        }
        (overlap.norm_sqr() / (norm_psi * norm_ground)).sqrt()
    }
}
