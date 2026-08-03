#!/usr/bin/env bash
# Full study for one variant, end to end.
#
#   ./run_study.sh textured     build -> mesh all bands -> sweep -> merge
#   ./run_study.sh planar       the same, with the cone absent
#
# Every stage is idempotent and the sweep resumes from its shards, so this is
# safe to re-run after an interruption -- it picks up at the first wavelength
# that has no result yet rather than starting over.
set -euo pipefail
cd "$(dirname "$0")"
source ./env.sh

VARIANT="${1:-textured}"
case "$VARIANT" in
  textured) export F3D_TEXTURE=on  ;;
  planar)   export F3D_TEXTURE=off ;;
  *) echo "usage: $0 [textured|planar]" >&2; exit 2 ;;
esac

export F3D_PROFILE="${F3D_PROFILE:-production}"
export F3D_CORES="${F3D_CORES:-8}"
export F3D_WORKERS="${F3D_WORKERS:-6}"
export F3D_CORES_PER_WORKER="${F3D_CORES_PER_WORKER:-6}"

echo "############ ${VARIANT}: geometry / materials / physics ############"
python3 -u build/f3d_01_geometry.py
python3 -u build/f3d_03_materials.py
python3 -u build/f3d_04_physics.py

echo "############ ${VARIANT}: mesh + solver per band ############"
for b in 0 1 2; do
  python3 -u build/f3d_06_prepare_mesh.py "$b"
done

# Verify the Floquet condition is actually satisfied before spending hours on
# the sweep. A mismatched paired-face mesh does not error -- it silently
# interpolates, and the result wanders with every remesh (see README).
echo "############ ${VARIANT}: periodicity check ############"
python3 -u build/f3d_dbg_periodicity.py 2 700 || true

# Three passes, worker count matched to each band's PER-SOLVE MEMORY -- the
# machine's binding constraint (solves are memory-bandwidth-bound; measured
# peak ~0.19 GB per 1k elements at 6 cores). Band 2's small red-end meshes
# run many-wide; band 1 runs 3-wide (~195 GB peak, the proven ceiling);
# band 0's 300 nm meshes are the largest and run 2-wide.
echo "############ ${VARIANT}: sweep, band 2 (many workers) ############"
F3D_ONLY_BANDS=2 F3D_WORKERS="${F3D_WORKERS_RED:-6}" \
  python3 -u build/f3d_08_sweep_driver.py

echo "############ ${VARIANT}: sweep, band 1 ############"
F3D_ONLY_BANDS=1 python3 -u build/f3d_08_sweep_driver.py

echo "############ ${VARIANT}: sweep, band 0 (fewer workers) ############"
F3D_ONLY_BANDS=0 F3D_WORKERS="${F3D_WORKERS_BLUE:-2}" \
  python3 -u build/f3d_08_sweep_driver.py

echo "############ ${VARIANT}: band-seam check ############"
python3 -u build/f3d_08_sweep_driver.py --overlap || true

echo "############ ${VARIANT} COMPLETE ############"
python3 -u build/f3d_10_photocurrent.py || true
