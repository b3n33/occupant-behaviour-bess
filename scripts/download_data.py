import os
from urllib.request import urlretrieve

REPO = "b3n33/occupant-behaviour-bess"
TAG = "v1.0.0-data"
FILES = [
    "agile_electricity_east_midlands.csv",
    "battery_optimisation_inputs.xlsx",
    "eplusout.csv",
    "metadata.csv",
    "US+SF+CZ4A+hp+slab+IECC_2024Meter.csv",
    "electricity_cleaned_small.csv",
    "Cluster_Differences.csv",
]


def main():
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    for name in FILES:
        url = f"https://github.com/{REPO}/releases/download/{TAG}/{name}"
        path = os.path.join(data_dir, name)
        print(f"Downloading {name}...")
        urlretrieve(url, path)


if __name__ == "__main__":
    main()