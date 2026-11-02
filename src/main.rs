use clap::{Parser, Subcommand};
use gpe_engine::{Fluid, FluidConfig, excite, metrics};
use transfer_operator::TransferOperator;
use std::time::Instant;

#[derive(Parser)]
#[command(name = "qoi-core")]
#[command(about = "Quantum Organic Intelligence - Core Rust SIMD Engine & Spectral Analysis", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Run fast GPE loop on native Rust SIMD engine
    Simulate {
        #[arg(short, long, default_value_t = 100)]
        iterations: usize,
        #[arg(short, long, default_value_t = 50)]
        gpe_steps: usize,
        #[arg(short, long, default_value_t = 20261026)]
        seed: u64,
    },
    /// Replay recorded hardware log or analyze stationary distribution via Frobenius-Perron operator
    Analyze {
        #[arg(short, long)]
        modes: String,
    },
}

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Simulate { iterations, gpe_steps, seed } => {
            println!("============================================================");
            println!("QOI-CORE :: GPE SIMD ENGINE");
            println!("  Iterációk : {}", iterations);
            println!("  GPE lépés : {} / iteráció", gpe_steps);
            println!("  Kezdő mag : {}", seed);
            println!("============================================================");

            let config = FluidConfig::default();
            let mut fluid = Fluid::new(config.clone(), seed);
            let mut mode_seq = Vec::with_capacity(iterations);

            let t0 = Instant::now();
            let mut a = 0.5;
            let mut f = 6.0;
            let mut phi = 0.25;

            for it in 0..iterations {
                excite(&mut fluid.psi, a, f, phi, config.rmax);
                let mut current_mode = 0;
                for _ in 0..gpe_steps {
                    let step = fluid.gpe_step();
                    current_mode = step.mode_argmax;
                }
                mode_seq.push(current_mode);

                // Autopoietic feedback loop update
                f = current_mode as f64;
                a = (current_mode as f64 / 15.0).clamp(0.1, 1.0);
                phi = (phi + 0.1) % 1.0;
            }

            let elapsed = t0.elapsed();
            let m = metrics(&mode_seq);

            println!("\nFutási idő : {:.3} s ({:.1} iteráció/s)", elapsed.as_secs_f64(), iterations as f64 / elapsed.as_secs_f64());
            println!("Módus sorozat: {:?}", mode_seq);
            println!("Meglátogatott módusok száma: {}", m.distinct_modes);
            println!("Brain (domináns) arány      : {:.4}", m.brain_ratio);
            println!("Normalizált entrópia H/Hmax : {:.4}", m.h_hmax);
            println!("Átmeneti entrópia           : {:.4}", m.transient_h);

            // Frobenius-Perron report
            let mut op = TransferOperator::new();
            op.record_sequence(&mode_seq);
            let report = op.report();
            println!("\nFrobenius-Perron Transzfer-Operátor:");
            println!("  Alapmódus (#0) stacionárius súly : {:.4}", report.ground_attractor_weight);
            println!("  Hexagonális (#6) stacionárius súly: {:.4}", report.hex_attractor_weight);
            println!("  Bistabil invariáns mérték igazolva : {}", report.is_bistable);
        }
        Commands::Analyze { modes } => {
            let seq: Vec<usize> = modes
                .split(',')
                .filter_map(|s| s.trim().parse().ok())
                .collect();
            println!("Elemzett módus sorozat mérete: {}", seq.len());
            let mut op = TransferOperator::new();
            op.record_sequence(&seq);
            let rep = op.report();
            println!("{}", serde_json::to_string_pretty(&rep)?);
        }
    }

    Ok(())
}
