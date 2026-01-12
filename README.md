# Occupant Energy Behaviour + BESS Optimisation

Project that quantifies Occupant Energy Behaviour (OEB) as the difference between simulated and measured electricity demand, clusters that behaviour with fuzzy C-means and uses the result in a communal battery energy storage system (BESS) sizing optimisation.

## What this does
- Compute hourly OEB from EnergyPlus simulation vs measured data.
- Cluster OEB with fuzzy logic (MATLAB FCM) to produce behavioural profiles.
- Combine clustered OEB with a residential EnergyPlus baseline to create demand profile.
- Optimise communal BESS Mixed-Integer Linear Programming (MILP) and Particle Swarm Optimisation (PSO) framework.

## Repository layout
- `src/capstone/compute_absolute_differences.py`: OEB from simulation vs measured data.
- `matlab/clusters.m`: FCM clustering + membership functions + clustered OEB output.
- `src/capstone/graph.py`: plot simulated vs measured demand.
- `src/capstone/optimise_battery_size.py`: BESS MILP + PSO sizing optimisation.
- `scripts/run_pipeline.py`: entry point (steps toggled in `main()`).
- `docs/figures/`: generated figures.

## Data and dependencies
- Data files are expected in `data/` (ignored by git). Key inputs:
  - `electricity_cleaned.csv`, `metadata.csv` from https://github.com/buds-lab/building-data-genome-project-2
  - `eplusout.csv`(generated),`Absolute_Differences.csv` (generated), `Cluster_Differences.csv` (generated)
  - `US+SF+CZ4A+hp+slab+IECC_2024Meter.csv` from https://www.energycodes.gov/prototype-building-models
  - `battery_optimisation_inputs.xlsx`, `agile_electricity_east_midlands.csv` from https://agilebuddy.uk/historic/download
- Python packages: `pandas`, `numpy`, `matplotlib`, `ortools`, `pyswarms`
- MATLAB for clustering step (`matlab/clusters.m`)
- EnergyPlus required only if `RUN_ENERGYPLUS = True` in `compute_absolute_differences.py`

## Setup
- Python 3.10-3.11 (pyswarms compatibility; 3.12+ not supported)
- `pip install -r requirements.txt`

Smoke test (no data required):
`python -c "import sys; sys.path.insert(0,'src'); import capstone.compute_absolute_differences as c; print('ok')"`

## How to run (typical pipeline)
1) OEB (Python):
   - `python -m capstone.compute_absolute_differences`
2) Fuzzy clustering (MATLAB):
   - `matlab -batch "run(fullfile('matlab','clusters.m'))"`
3) Plot comparison (Python):
   - `python -m capstone.graph`
4) BESS sizing + dispatch (Python):
   - `python -m capstone.optimise_battery_size`

Run the full pipeline (skip MATLAB if you don't have it installed):
`python scripts/run_pipeline.py --skip-matlab`

## Outputs
- `data/Absolute_Differences.csv`: hourly OEB.
- `data/Cluster_Differences.csv`: clustered OEB profile.
- `docs/figures/dif.pdf`: simulation vs measured plot.
- `docs/figures/clusters_mf.png`: fuzzy membership functions.
- `docs/figures/battery_decision_space.pdf`: PSO decision space plot.

## Notes
- The MATLAB clustering script uses a confidence threshold to select conservative OEB upper bounds.
- The optimisation uses a communal BESS across `NUM_BUILDINGS = 6`.
