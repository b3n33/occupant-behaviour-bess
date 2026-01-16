from pathlib import Path
import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ortools.linear_solver import pywraplp
import pyswarms as pso

# --- Config ---
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"

CLUSTER_DIFF_PATH = DATA_DIR / "Cluster_Differences.csv"                #sum of building cluster differences [kwh/m2]
EP_PATH = DATA_DIR / "US+SF+CZ4A+hp+slab+IECC_2024Meter.csv"            #EnergyPlus output CSV for sample building
FIG_PATH = ROOT / "docs" / "figures" / "battery_decision_space.pdf"
INPUT_XLSX = DATA_DIR / "battery_optimisation_inputs.xlsx"
PRICE_CSV = DATA_DIR / "agile_electricity_east_midlands.csv"

EP_COLUMN = "Electricity:Facility [J](Hourly) "                         # note trailing space in source CSV
HOUSE_SIZE = 220.82                                                     # m^2 of a single detached house
NUM_BUILDINGS = 6                                                       # number of buildings in the communal BESS system

PRICE_CAPACITY = 90                                                     # £ per kWh of battery capacity
YEARS = 10                                                              # simulation years for cost calculation

PSO_PARTICLES = 3
PSO_ITERS = 10
PSO_OPTIONS = {"c1": 0.5, "c2": 0.3, "w": 0.9}                          # cognitive, social, inertia weights
BOUNDS = (np.array([1.0]), np.array([162.0]))                           # kWh capacity range

PLOT_DECISION_SPACE = False
SAVE_FIG = False
# --- End config ---

cost_cache = {}


def custom_to_datetime(date_str: str) -> pd.Timestamp:
    date_str = "2017/" + date_str.strip()
    if date_str[12:14] == "24":
        return pd.to_datetime(date_str[:10], format="%Y/%m/%d") + pd.Timedelta(days=1)
    return pd.to_datetime(date_str, format="%Y/%m/%d %H:%M:%S")


def load_cluster_diff() -> pd.Series:
    df = pd.read_csv(CLUSTER_DIFF_PATH, header=None)
    return df.iloc[:, 0]


def load_ep_data() -> pd.DataFrame:
    df = pd.read_csv(EP_PATH)
    df = df.iloc[:-5]
    return df


def build_load_series(df_ep: pd.DataFrame, cluster_diff: pd.Series) -> pd.Series:
    energy = df_ep[EP_COLUMN] / 3600000                                 # J to kWh
    energy = energy * NUM_BUILDINGS                                     # kWh for all buildings
    load = energy + cluster_diff * HOUSE_SIZE
    return load.dropna()


def build_market_df(df_ep: pd.DataFrame, load_series: pd.Series):
    workbook = pd.ExcelFile(INPUT_XLSX)

    market_df = workbook.parse("Timeseries data").iloc[:, :3]
    market_df = market_df.iloc[: len(df_ep)]

    market_df.iloc[:, 0] = df_ep.iloc[: len(market_df), 0].astype(str).values
    market_df.iloc[:, 2] = load_series.iloc[: len(market_df)].values

    price = pd.read_csv(PRICE_CSV, header=None).iloc[::2].iloc[1:, 2].reset_index(drop=True)
    price = price.iloc[: len(market_df)]
    market_df.iloc[:, 1] = price.values

    market_df.columns = ["time", "market_price_1", "load"]
    market_df = market_df[~pd.isnull(market_df["time"])].fillna(0)

    market_df["time"] = market_df["time"].str.strip()
    market_df["time"] = market_df["time"].apply(custom_to_datetime)
    market_df.sort_values(by=["time"], inplace=True)
    market_df["time_string"] = market_df["time"].dt.strftime("%d/%m/%Y %H:%M")
    market_df.set_index("time_string", inplace=True)

    return market_df, workbook


def build_input_data(market_df: pd.DataFrame, workbook: pd.ExcelFile) -> dict:
    grid_df = workbook.parse("Grid").iloc[:, :4]
    grid_df.columns = [
        "max_buy_power",
        "max_sell_power",
        "max_import_power",
        "max_export_power",
    ]

    batt_df = workbook.parse("Battery").iloc[:, :8]
    batt_df.columns = [
        "max_charge_rate",
        "max_discharge_rate",
        "capacity",
        "charge_eff",
        "discharge_eff",
        "min_soc",
        "max_soc",
        "initial_soc",
    ]

    time_interval = market_df.iloc[1]["time"] - market_df.iloc[0]["time"]

    input_data = {
        "simData": {
            "startTime": datetime.datetime.strptime(market_df.index[0], "%d/%m/%Y %H:%M"),
            "dt": int(round(time_interval.total_seconds())) / (60 * 60),
            "tIndex": market_df.shape[0],
        },
        "market": market_df.to_dict(),
        "grid": {key: item[0] for key, item in grid_df.to_dict().items()},
        "batt": {key: item[0] for key, item in batt_df.to_dict().items()},
    }

    return input_data


def build_time_index(input_data: dict) -> list[str]:
    start_time = input_data["simData"]["startTime"].strftime("%d/%m/%Y %H:%M")
    t_index = input_data["simData"]["tIndex"]
    dt = input_data["simData"]["dt"]
    timestamp = pd.date_range(start_time, periods=t_index, freq=str(dt * 60) + "min")
    return [t.strftime("%d/%m/%Y %H:%M") for t in timestamp]


def optimise_battery_size(bat_cap: np.ndarray, input_data: dict, time: list[str]) -> np.ndarray:
    n_particles = bat_cap.shape[0]
    costs = np.zeros(n_particles)

    for p in range(n_particles):
        bat_cap_p = float(bat_cap[p, 0])
        if bat_cap_p in cost_cache:
            costs[p] = cost_cache[bat_cap_p]
            continue

        solver = pywraplp.Solver.CreateSolver("CBC")
        inf = solver.infinity()

        t_index = input_data["simData"]["tIndex"]
        dt = input_data["simData"]["dt"]

        v_grid = [solver.NumVar(lb=-inf, ub=inf, name="") for _ in range(t_index)]
        v_batt_power = [solver.NumVar(lb=-inf, ub=inf, name="") for _ in range(t_index)]
        v_charge = [solver.NumVar(lb=-inf, ub=0, name="") for _ in range(t_index)]
        v_discharge = [solver.NumVar(lb=0, ub=inf, name="") for _ in range(t_index)]
        v_charge_status = [solver.BoolVar(name="") for _ in range(t_index)]
        v_soc = [solver.NumVar(lb=0, ub=1, name="") for _ in range(t_index)]

        for i in range(t_index):
            t = time[i]

            solver.Add(v_grid[i] == input_data["market"]["load"][t] - v_batt_power[i])
            solver.Add(v_grid[i] <= input_data["grid"]["max_buy_power"])
            solver.Add(v_grid[i] >= -input_data["grid"]["max_sell_power"])
            solver.Add(
                input_data["market"]["load"][t] - (v_discharge[i] + v_charge[i])
                <= input_data["grid"]["max_import_power"]
            )
            solver.Add(
                input_data["market"]["load"][t] - (v_discharge[i] + v_charge[i])
                >= -input_data["grid"]["max_export_power"]
            )

            solver.Add(v_batt_power[i] == v_charge[i] + v_discharge[i])
            solver.Add(v_charge[i] >= -input_data["batt"]["max_charge_rate"] * v_charge_status[i])
            solver.Add(v_discharge[i] <= input_data["batt"]["max_discharge_rate"] * (1 - v_charge_status[i]))

            if i == 0:
                solver.Add(
                    v_soc[i]
                    == input_data["batt"]["initial_soc"]
                    - dt / bat_cap_p * (
                        v_charge[i] * (1 - input_data["batt"]["charge_eff"])
                        + v_discharge[i] / (1 - input_data["batt"]["discharge_eff"])
                    )
                )
            else:
                solver.Add(
                    v_soc[i]
                    == v_soc[i - 1]
                    - dt / bat_cap_p * (
                        v_charge[i] * (1 - input_data["batt"]["charge_eff"])
                        + v_discharge[i] / (1 - input_data["batt"]["discharge_eff"])
                    )
                )

            solver.Add(v_soc[i] >= input_data["batt"]["min_soc"])
            solver.Add(v_soc[i] <= input_data["batt"]["max_soc"])

        obj = bat_cap_p * PRICE_CAPACITY + sum(
            v_grid[i] * input_data["market"]["market_price_1"][time[i]] * dt
            for i in range(t_index)
        ) * YEARS / 100

        solver.Minimize(obj)
        status = solver.Solve()

        if status in (solver.OPTIMAL, solver.FEASIBLE):
            cost_value = round(solver.Objective().Value(), 2)
        else:
            cost_value = np.inf

        cost_cache[bat_cap_p] = cost_value
        costs[p] = cost_value

    return costs


def plot_decision_space(optimiser: pso.single.GlobalBestPSO) -> None:
    pos_history = np.array(optimiser.pos_history)
    bat_sizes = pos_history[:, :, 0].flatten()
    costs = np.array([cost_cache.get(float(x), np.nan) for x in bat_sizes])

    plt.rcParams.update({"font.size": 9})
    fig, ax = plt.subplots(figsize=(3.25, 5))
    ax.scatter(bat_sizes, costs / 1000, alpha=1, color="black")
    ax.set_xlabel("Battery Capacity (kWh)")
    ax.set_ylabel("Cost (thousands of pence)")
    ax.grid(True)
    ax.tick_params(axis="both", labelsize=8)
    
    if SAVE_FIG:
        FIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(FIG_PATH, bbox_inches="tight", dpi=300)
    
    plt.show()


def main() -> None:
    cluster_diff = load_cluster_diff()
    df_ep = load_ep_data()
    load_series = build_load_series(df_ep, cluster_diff)

    market_df, workbook = build_market_df(df_ep, load_series)
    input_data = build_input_data(market_df, workbook)
    time = build_time_index(input_data)

    optimiser = pso.single.GlobalBestPSO(
        n_particles=PSO_PARTICLES,
        dimensions=1,
        options=PSO_OPTIONS,
        bounds=BOUNDS,
        ftol=0.01,
        ftol_iter=10,
    )
    cost, pos = optimiser.optimize(
        lambda x: optimise_battery_size(x, input_data, time),
        iters=PSO_ITERS,
    )

    print(f"Optimal Battery Capacity: {pos} kWh")
    print(f"Minimum Energy Cost: £{cost}")

    if PLOT_DECISION_SPACE:
        plot_decision_space(optimiser)


if __name__ == "__main__":
    main()