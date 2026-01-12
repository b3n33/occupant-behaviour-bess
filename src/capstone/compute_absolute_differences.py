from pathlib import Path
import os
import subprocess
import pandas as pd

# --- Config ---
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
EP_DIR = ROOT / "EnergyPlusV22-1-0"

IDF_PATH = DATA_DIR / "ASHRAE901_OfficeMedium_STD2016_NewYork.idf"
EPW_PATH = DATA_DIR / "USA_NY_New.York-John.F.Kennedy.Intl.AP.744860_TMY3.epw"
OUTPUT_DIR = DATA_DIR

METADATA_PATH = DATA_DIR / "metadata.csv"
EPLUSOUT_PATH = DATA_DIR / "eplusout.csv"
ELECTRICITY_PATH = DATA_DIR / "electricity_cleaned.csv"
OUTPUT_FILE = DATA_DIR / "Absolute_Differences.csv"

BUILDING_TITLES = [
    "Eagle_office_Elias",
    "Robin_office_Shirlene",
    "Eagle_office_Lane",
    "Eagle_office_Remedios",
    "Robin_office_Sammie",
    "Eagle_office_Lillian",
    "Lamb_office_Gerardo",
]

ROW_COUNT = 8760
CONVERSION_FACTOR = 3600000 * 4982.19  # J to kWh per m^2
RUN_ENERGYPLUS = False
OPEN_OUTPUT = False
# --- End config ---


def run_energyplus() -> int:
    exe_path = EP_DIR / "EnergyPlus"
    cmd = [
        str(exe_path),
        "--readvars",
        "--output-directory",
        str(OUTPUT_DIR),
        "--weather",
        str(EPW_PATH),
        str(IDF_PATH),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    print("---ARGS---\n", result.args)
    print(
        "---RETURNCODE---\n",
        result.returncode,
        "(SUCCESS)" if result.returncode == 0 else "(FAIL)",
    )
    print("---STDOUT---\n", result.stdout)
    print("---STDERR---\n", result.stderr)

    return result.returncode


def load_metadata_map() -> dict:
    df = pd.read_csv(METADATA_PATH)
    if "building_id" not in df.columns:
        raise ValueError("metadata.csv missing 'building_id' column")
    return dict(zip(df["building_id"], df.iloc[:, 6]))


def build_absolute_differences() -> pd.DataFrame:
    df_ep = pd.read_csv(EPLUSOUT_PATH)
    df_load = pd.read_csv(ELECTRICITY_PATH)
    metadata = load_metadata_map()

    ep_series = df_ep.iloc[:ROW_COUNT, 1] / CONVERSION_FACTOR
    result = pd.DataFrame({"Date/Time": df_ep.iloc[:ROW_COUNT, 0]})

    for title in BUILDING_TITLES:
        if title not in df_load.columns or title not in metadata:
            continue

        denom = metadata[title]
        if pd.isna(denom) or denom == 0:
            continue

        load_series = df_load.iloc[1 : ROW_COUNT + 1][title].reset_index(drop=True) / denom
        result[title] = ep_series.reset_index(drop=True) - load_series

    return result


def main() -> None:
    if RUN_ENERGYPLUS:
        rc = run_energyplus()
        if rc != 0:
            return

    df = build_absolute_differences()
    df.to_csv(OUTPUT_FILE, index=False)

    if OPEN_OUTPUT:
        os.startfile(OUTPUT_FILE)

    print(f"CSV file has been created: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
