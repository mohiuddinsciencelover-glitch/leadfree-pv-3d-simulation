#!/usr/bin/env bash
# Planar-only 3D optics for the remaining absorbers, back to back.
#
# Purpose: refresh the PARENT manuscript's optical stage — same free-tet
# full-wave 3D machinery as the FASnI3 study, corrected FTO data, and for
# BaZrS3 the MEASURED (Nishigaki 2020) dielectric function in place of the
# DFT-computed KK file. Planar only: these runs are the parent study redone,
# not the texture paper.
#
# Absorbers run SEQUENTIALLY, each with per-band worker counts tuned to the
# memory ceiling (see run_study.sh). Running two absorbers concurrently would
# add no throughput: three big-band solves already saturate the 251 GB box,
# and cores beyond 6/solve buy nothing (memory-bandwidth-bound, measured).
#
# Resume-safe: every stage is idempotent; an interruption costs only the
# wavelengths in flight.
set -u
cd "$(dirname "$0")"

export F3D_PROFILE=production
export F3D_PPW=5 F3D_SKIN_FLOOR=14 F3D_LINSOLVER=d1
export F3D_WORKERS=3 F3D_CORES_PER_WORKER=6
export F3D_WORKERS_RED=6 F3D_WORKERS_BLUE=2 F3D_CORES=8

for ABS in Cu2AgBiI6 Cs2AgBiBr6 BaZrS3; do
  export F3D_ABSORBER="$ABS"
  echo
  echo "################################################################"
  echo "#  ${ABS}  planar 3D optics   $(date -Is)"
  echo "################################################################"
  ./run_study.sh planar || { echo "!! ${ABS} exited non-zero -- continuing"; }
  source ./env.sh
  python3 -u build/f3d_14_generation_profile.py planar || true
done

echo
echo "QUEUE_ALL_DONE $(date -Is)"
