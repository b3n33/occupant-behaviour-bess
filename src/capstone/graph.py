from pathlib import Path
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

# --- Config ---
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"

EPLUSOUT_PATH = DATA_DIR / "eplusout.csv"
ELECTRICITY_PATH = DATA_DIR / "electricity_cleaned_small.csv"

# Row window for plotting (start index and number of rows)
ROW_START = 1
ROW_COUNT = 400
ROW_RANGE = slice(ROW_START, ROW_START + ROW_COUNT)
MODIFIED_ROW_RANGE = slice(ROW_RANGE.start + 1, ROW_RANGE.stop + 1)

CONVERSION_FACTOR = 3600000 * 4982.19  # J to kWh per m^2

PLOT_SERIES = [
    ("Robin_office_Sammie", 4802, "Red", "High OEB"),
    ("Eagle_office_Lillian", 4844.1, "Blue", "Low OEB"),
]

SIM_COLUMN = "Electricity:Facility [J](Hourly)"
FIG_PATH = ROOT / "docs" / "figures" / "dif.pdf"
# --- End config ---

def parse_energyplus_datetime(st: str, year: int = 2017) -> pd.Timestamp:
    st = st.strip()
    month = int(st[0:2])
    day = int(st[3:5])
    hour = int(st[7:9])
    minute = int(st[10:12])
    if hour != 24:
        return pd.Timestamp(year, month, day, hour, minute)
    return pd.Timestamp(year, month, day, 0, minute) + pd.Timedelta("1 day")

def parse_measured_datetime(st: str, year: int = 2017) -> pd.Timestamp:
    st = st.strip()
    day = int(st[8:10])
    month = int(st[5:7])
    hour = int(st[11:13])
    minute = int(st[14:16])
    return pd.Timestamp(year, month, day, hour, minute)

def main() -> None:
    df_ep = pd.read_csv(
        EPLUSOUT_PATH,
        parse_dates=[0],
        index_col=[0],
        date_parser=parse_energyplus_datetime,
    )

    df_load = pd.read_csv(
        ELECTRICITY_PATH,
        parse_dates=[0],
        index_col=[0],
        skiprows=lambda x: x > 0 and x < 8785,
        date_parser=parse_measured_datetime,
    )

    df_ep = df_ep / CONVERSION_FACTOR

    plt.rcParams.update({"font.size": 9})
    fig, ax = plt.subplots(figsize=(7.5, 2.5))

    # Plot measured series
    for col, denom, color, label in PLOT_SERIES:
        if col not in df_load.columns:
            print(f"Skipping {col}: column not found.")
            continue
        ax.plot(
            df_load[col][MODIFIED_ROW_RANGE] / denom,
            color=color,
            linewidth=1,
            label=label,
        )

    # Plot simulation series
    if SIM_COLUMN not in df_ep.columns:
        raise ValueError(f"Missing simulation column: {SIM_COLUMN}")
    ax.plot(
        df_ep[SIM_COLUMN][ROW_RANGE],
        color="black",
        linewidth=1,
        label="Simulation",
    )

    ax.set_xlabel("Date")
    ax.set_ylabel(r"$\mathrm{Electricity\ Demand\ (kWh/m^2)}$")
    ax.tick_params(axis="both", labelsize=8)
    ax.legend(fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.grid(True)
    FIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIG_PATH, bbox_inches="tight", dpi=300)

    plt.show()


if __name__ == "__main__":
    main()
