# Investigating the Impact of Occupancy Behaviour on Predicted Electrical Demand and Energy Flexibility

Quantifies occupants' energy behaviour (OEB) from simulated vs measured demand, clusters it into behavioural profiles and enhances forecasts to optimise a communal battery energy storage system (BESS) sizing and costs.

## Overview

Building energy demand models often focus on physical building characteristics while simplifying OEB. This project quantifies and clusters OEB into five distinct consumption profiles, which are used to improve energy demand predictions. The resulting OEB-adjusted forecasts are then incorporated into a Mixed-Integer Linear Programming (MILP) and Particle Swarm Optimisation (PSO) framework to optimise the capacity of a communal BESS.

## Features
- End-to-end pipeline with flags to download data and skip MATLAB (`run_pipeline.py`)
- Automated data acquisition from the GitHub release via Docker and Python scripts (`docker_run.sh`, `download_data.py`)
- Hourly OEB quantification from EnergyPlus simulation vs measured demand (`compute_absolute_differences.py`)
- Fuzzy c-means clustering in MATLAB to create five behavioural profiles and export clustered OEB (`clusters.m`)
- Plot of simulated vs measured demand for selected buildings (`graph.py`)
- Combine clustered OEB with a residential EnergyPlus baseline to create demand profile and perform communal BESS sizing optimisation using MILP and PSO (`optimise_battery_size.py`)
- Containerised and reproducible runs via Docker (`Dockerfile`, `docker_run.sh`) with pinned Python dependencies (`requirements.txt`)

## Tech Stack
- Python (NumPy, pandas, matplotlib, OR-Tools for MILP, PySwarms for PSO)
- MATLAB (genfis for fuzzy c-means clustering)
- EnergyPlus (building energy simulation)
- Docker (optional)

## Repository Structure
- `src/capstone/`: core Python modules (OEB calculation, plotting, optimisation)
- `scripts/`: pipeline and utility scripts
- `matlab/`: fuzzy c-means clustering script for OEB profiling
- `data/`: input/output data files (gitignored)
- `docs/figures/`: generated plots and figures
- `Dockerfile`, `docker_run.sh`: containerised execution
- `requirements.txt`: pinned Python dependencies

## Installation 
### Docker (recommended)
One-command setup (downloads the input data release and runs the pipeline):
```bash
docker build -t oeb-bess . && docker run --rm oeb-bess
```
### Local installation
- Windows
```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m scripts.run_pipeline --download-data --skip-matlab
```
- macOS / Linux
```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m scripts.run_pipeline --download-data --skip-matlab
```
- Notes:
   - PySwarms requires Python 3.5-3.12
   - MATLAB is only required for fuzzy clustering (`clusters.m`); if it's installed, can remove `--skip-matlab` (Docker skips MATLAB)
   - EnergyPlus is only required to re-run the simulation output data; set `RUN_ENERGYPLUS = True` in `compute_absolute_differences.py` if it's installed

## Data
- `agile_electricity_east_midlands.csv`: [Octopus Agile energy tariff](https://agilebuddy.uk/historic/download)
- `battery_optimisation_inputs.xlsx`: Grid and battery parameters for BESS optimisation
- `eplusout.csv`: EnergyPlus simulation used for quantifying OEB
- `metadata.csv`: [Area of buildings for normalisation](https://www.nature.com/articles/s41597-020-00712-x)
- `US+SF+CZ4A+hp+slab+IECC_2024Meter.csv`: EnergyPlus simulation used for baseline BESS load profile
- `electricity_cleaned_small.csv`: [Measured demand for 6 buildings](https://www.nature.com/articles/s41597-020-00712-x)
- `Cluster_Differences.csv`: Clustered OEB output
- `docs/figures/dif.pdf`: simulation vs measured plot
- `docs/figures/clusters_mf.png`: fuzzy membership functions
- `docs/figures/battery_decision_space.pdf`: PSO decision space plot