#!/usr/bin/env bash
# Convergence study, re-run after the periodic-mesh fix.
#
# The first attempt produced A_absorber = 0.719 / 0.663 / 0.463 at 700 nm on
# meshes of 120153 / 120346 / 123031 elements -- a 36 % swing across a 2.5 %
# change in mesh size, which is divergence, not discretisation error. Cause:
# the Floquet-paired faces carried different free-tet surface meshes, so the
# periodic coupling was interpolated and its error moved with every remesh.
# Stage 06 now meshes x=0 and y=0 and copies those meshes to the opposite
# faces, making each pair identical node-for-node.
#
# If the fix is right, A_absorber should now settle as ppw rises instead of
# wandering. That is the pass/fail criterion for this run.
cd "$(dirname "$0")"
source ./env.sh
export F3D_PROFILE=production
export F3D_CORES="${F3D_CORES:-14}"
export F3D_LINSOLVER=d1
export F3D_SKIN_FLOOR="${F3D_SKIN_FLOOR:-14}"
export F3D_CONV_TAG=_fixed

python3 -u build/f3d_09_mesh_convergence.py 700 3 4 5 6.5
echo "CONV2_DONE"
