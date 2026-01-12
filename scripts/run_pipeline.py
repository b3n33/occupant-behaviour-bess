import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from capstone.compute_absolute_differences import main as run_diffs
from capstone.graph import main as run_graph
from capstone.optimise_battery_size import main as run_opt


def run_matlab_clusters() -> None:
    # Assumes MATLAB is on PATH
    cmd = [
        "matlab",
        "-batch",
        "run(fullfile('matlab','clusters.m'))",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    print(result.stdout)
    print(result.stderr)
    if result.returncode != 0:
        raise RuntimeError("MATLAB step failed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description = "Run the OEB + BESS pipeline.")
    parser.add_argument(
        "--skip-matlab",
        action="store_true",
        help="Skip the MATLAB fuzzy clustering step.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    run_diffs()
    if not args.skip_matlab:
        run_matlab_clusters()
    run_graph()
    run_opt()


if __name__ == "__main__":
    main()
