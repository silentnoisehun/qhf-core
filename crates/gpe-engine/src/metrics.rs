//! Mode-sequence metrics: distinct modes, brain ratio, entropy, transient entropy.

use std::collections::HashSet;

/// Computed metrics for a mode sequence.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Metrics {
    pub distinct_modes: usize,
    pub brain_ratio: f64,
    pub h_hmax: f64,
    pub transient_h: f64,
    pub hist: [u32; 16],
    pub n: usize,
}

/// Compute metrics from a mode-argmax sequence.
pub fn metrics(seq: &[usize]) -> Metrics {
    let n = seq.len();
    if n == 0 {
        return Metrics {
            distinct_modes: 0,
            brain_ratio: 0.0,
            h_hmax: 0.0,
            transient_h: 0.0,
            hist: [0; 16],
            n: 0,
        };
    }

    // Histogram
    let mut hist = [0u32; 16];
    for &m in seq {
        if m < 16 {
            hist[m] += 1;
        }
    }

    // Distinct modes
    let distinct: HashSet<usize> = seq.iter().copied().collect();
    let distinct_modes = distinct.len();

    // Brain ratio: fraction in the most common mode (ground = mode 0)
    let max_count = *hist.iter().max().unwrap_or(&0);
    let brain_ratio = max_count as f64 / n as f64;

    // Shannon entropy
    let h: f64 = hist.iter()
        .filter(|&&c| c > 0)
        .map(|&c| {
            let p = c as f64 / n as f64;
            -p * p.ln()
        })
        .sum();
    let h_max = (16.0_f64).ln();
    let h_hmax = if h_max > 0.0 { h / h_max } else { 0.0 };

    // Transient entropy: entropy of the transition matrix
    let mut transitions = [[0u32; 16]; 16];
    for w in seq.windows(2) {
        if w[0] < 16 && w[1] < 16 {
            transitions[w[0]][w[1]] += 1;
        }
    }
    let total_transitions = (n - 1).max(1) as f64;
    let transient_h: f64 = transitions.iter()
        .flat_map(|row| row.iter())
        .filter(|&&c| c > 0)
        .map(|&c| {
            let p = c as f64 / total_transitions;
            -p * p.ln()
        })
        .sum::<f64>() / (16.0_f64 * 16.0_f64).ln();

    Metrics {
        distinct_modes,
        brain_ratio,
        h_hmax,
        transient_h,
        hist,
        n,
    }
}
