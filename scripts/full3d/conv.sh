#!/usr/bin/env bash
# Mesh-convergence study, run with the DIRECT solver.
#
# Direct, not iterative, on purpose: the quantity being measured is
# DISCRETISATION error, and an iterative solve would fold its own tolerance
# and convergence behaviour into the same number. Direct is also the faster
# choice at these mesh sizes -- it only became unaffordable on the 400k-800k
# element meshes that this study exists to show are unnecessary.
cd "$(dirname "$0")"
source ./env.sh
export F3D_PROFILE=production
export F3D_CORES="${F3D_CORES:-12}"
export F3D_LINSOLVER=d1
export F3D_SKIN_FLOOR="${F3D_SKIN_FLOOR:-14}"

python3 -u build/f3d_09_mesh_convergence.py 700 3 4 5
echo "#### 400 nm ####"
python3 -u build/f3d_09_mesh_convergence.py 400 3 4 5
echo "ALL_CONVERGENCE_DONE"
