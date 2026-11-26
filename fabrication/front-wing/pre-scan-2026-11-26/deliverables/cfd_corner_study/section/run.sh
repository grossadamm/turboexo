#!/usr/bin/env bash
# Reproduce the data and images in this directory. Uses at most two solver threads.
set -euo pipefail
cd "$(dirname "$0")"
CAD_PY="${CAD_PY:-../../../.venv/bin/python}"
PLOT_PY="${PLOT_PY:-python3}"
OPENMP_DIR="${OPENMP_DIR:-/opt/homebrew/opt/libomp}"
flags=(-std=c++17 -O3 -ffast-math -fno-finite-math-only)
clang++ "${flags[@]}" -Xpreprocessor -fopenmp -I"$OPENMP_DIR/include" -L"$OPENMP_DIR/lib" -lomp solve.cpp -o solve_repro
clang++ "${flags[@]}" benchmark.cpp -o benchmark_repro
./benchmark_repro > benchmark.log
"$CAD_PY" prepare.py 2 1.25 > grid_build.log
./solve_repro empty_2.grid empty_2 650 1 .065 1 1 > empty_2.log
for case in on off; do
  ./solve_repro "${case}_2.grid" "${case}_2" 650 22 .065 2 2 > "${case}_2.log"
  ./solve_repro "${case}_1.25.grid" "${case}_dense_1.25" 650 22 .065 2 .5 12 > "${case}_dense_1.25.log"
  ./solve_repro "${case}_2.grid" "${case}_re1300_2" 1300 22 .065 2 2 > "${case}_re1300_2.log"
done
FLOW_DIR="$PWD" "$PLOT_PY" analyze.py
