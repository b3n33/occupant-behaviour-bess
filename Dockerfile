FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*


# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

CMD ["bash", "docker_run.sh"]


FROM python:3.11-slim

# WORKDIR /app

# # System deps
# RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# # Python deps
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # App code
# COPY . .

# # Inline "docker_run.sh" logic here
# CMD ["bash", "-c", "\
# set -euo pipefail; \
# REPO='b3n33/occupant-behaviour-bess'; \
# RELEASE_TAG='v1.0.0-data'; \
# DATA_DIR='data'; \
# mkdir -p \"$DATA_DIR\"; \
# download() { \
#   local filename=\"$1\"; \
#   local url=\"https://github.com/${REPO}/releases/download/${RELEASE_TAG}/${filename}\"; \
#   echo \"Downloading ${filename}...\"; \
#   curl -L -o \"${DATA_DIR}/${filename}\" \"${url}\"; \
# }; \
# download 'agile_electricity_east_midlands.csv'; \
# download 'battery_optimisation_inputs.xlsx'; \
# download 'eplusout.csv'; \
# download 'metadata.csv'; \
# download 'US+SF+CZ4A+hp+slab+IECC_2024Meter.csv'; \
# download 'electricity_cleaned_small.csv'; \
# python scripts/run_pipeline.py --skip-matlab \
# "]


