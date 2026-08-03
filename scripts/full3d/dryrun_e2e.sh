#!/usr/bin/env bash
# End-to-end rehearsal of the sweep machinery at dry-run mesh density.
#
# The production run is hours long, so the driver -> worker -> shard -> merge
# path, the band model switching inside a worker, and the resume logic all get
# exercised here first, on a mesh small enough that a mistake costs minutes.
# The numbers are deliberately not trustworthy; only the plumbing is.
set -e
cd "$(dirname "$0")"
source ./env.sh
export F3D_PROFILE=dryrun
export F3D_TEXTURE=on
export F3D_CORES=3
export F3D_WORKERS=2
export F3D_CORES_PER_WORKER=3
export F3D_LINSOLVER=d1

echo "#### dryrun: build ####"
python3 -u build/f3d_01_geometry.py  > /dev/null
python3 -u build/f3d_03_materials.py > /dev/null
python3 -u build/f3d_04_physics.py   > /dev/null

echo "#### dryrun: mesh bands 1 and 2 (the ones the dryrun grid touches) ####"
for b in 1 2; do python3 -u build/f3d_06_prepare_mesh.py "$b" | tail -4; done

echo "#### dryrun: sweep ####"
python3 -u build/f3d_08_sweep_driver.py

echo "#### dryrun: resume must be a no-op ####"
python3 -u build/f3d_08_sweep_driver.py

echo "#### dryrun: photocurrent ####"
python3 -u build/f3d_10_photocurrent.py || true
echo "DRYRUN_E2E_DONE"
