#!/usr/bin/env bash
# Production run: textured, then the planar control, then post-processing.
#
# Sequential rather than concurrent on purpose. Both variants would otherwise
# compete for the same cores and memory, and the planar control is only
# meaningful if it ran under the same conditions as the textured case --
# including how loaded the machine was, since a memory-starved solve can fall
# back or fail differently. Running them one after the other keeps the
# comparison clean and keeps peak memory predictable.
#
# Safe to re-run: every stage is idempotent and the sweep resumes from its
# shards, so an interruption costs only the wavelength in flight.
set -u
cd "$(dirname "$0")"

export F3D_PROFILE=production
export F3D_PPW="${F3D_PPW:-5}"
export F3D_SKIN_FLOOR="${F3D_SKIN_FLOOR:-14}"
export F3D_LINSOLVER="${F3D_LINSOLVER:-d1}"
export F3D_LAMBDA_STEP="${F3D_LAMBDA_STEP:-10}"
export F3D_WORKERS="${F3D_WORKERS:-8}"
export F3D_CORES_PER_WORKER="${F3D_CORES_PER_WORKER:-5}"
export F3D_CORES="${F3D_CORES:-8}"

echo "=================================================================="
echo " PRODUCTION RUN   ppw=$F3D_PPW  skin_floor=$F3D_SKIN_FLOOR"
echo " solver=$F3D_LINSOLVER  lambda step=${F3D_LAMBDA_STEP} nm"
echo " ${F3D_WORKERS} workers x ${F3D_CORES_PER_WORKER} cores"
echo " started $(date -Is)"
echo "=================================================================="

for variant in textured planar; do
  echo
  echo "################################################################"
  echo "#  ${variant}   $(date -Is)"
  echo "################################################################"
  ./run_study.sh "$variant" || echo "!! ${variant} exited non-zero -- continuing"
done

echo
echo "################ generation profiles G(z) ################"
source ./env.sh
# Turns the per-wavelength depth profiles the workers emitted into the single
# AM1.5G-weighted G(z) the drift-diffusion model consumes, and cross-checks it
# against the absorptance spectrum by an independent route.
for variant in textured planar; do
  python3 -u build/f3d_14_generation_profile.py "$variant" || true
done

echo
echo "################ comparison + figures ################"
python3 -u build/f3d_10_photocurrent.py \
    "results/f3d_FASnI3_absorptance_production.csv" \
    "results/f3d_FASnI3_absorptance_production_planar.csv" --compare || true
python3 -u build/f3d_11_figures.py || true

echo "PRODUCTION_ALL_DONE $(date -Is)"
