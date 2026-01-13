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

## Docker (recommended)
One‑command run (downloads the input data release and runs the pipeline):
`docker build -t oeb-bess . && docker run --rm oeb-bess`

## Outputs
- `data/Absolute_Differences.csv`: hourly OEB.
- `data/Cluster_Differences.csv`: clustered OEB profile.
- `docs/figures/dif.pdf`: simulation vs measured plot.
- `docs/figures/clusters_mf.png`: fuzzy membership functions.
- `docs/figures/battery_decision_space.pdf`: PSO decision space plot.

## Notes on optional tools
- MATLAB is only required for the fuzzy clustering step (`matlab/clusters.m`). The Docker run skips MATLAB.
- EnergyPlus is only required if you want to re‑run the simulation in `compute_absolute_differences.py` (`RUN_ENERGYPLUS = True`).

## Full manual run (optional)
1) Install Python 3.10–3.11 and dependencies:
   - `pip install -r requirements.txt`
2) OEB:
   - `python -m capstone.compute_absolute_differences`
3) Fuzzy clustering (MATLAB):
   - `matlab -batch "run(fullfile('matlab','clusters.m'))"`
4) Plot comparison:
   - `python -m capstone.graph`
5) BESS sizing + dispatch:
   - `python -m capstone.optimise_battery_size`