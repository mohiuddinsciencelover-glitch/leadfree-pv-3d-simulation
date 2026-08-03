#!/usr/bin/env bash
# Second convergence round, at higher points-per-wavelength.
#
# Round one (ppw 3,4,5) showed the answer is NOT converged: ppw 3 and 4 gave
# element counts within 0.2 % of each other but absorber absorptance 7.7 %
# apart. The mesh is dominated by fixed floors (Au skin depth, cone shape,
# thin ETL), so raising ppw costs far less than it normally would while
# fixing the layers that are actually under-resolved -- the FTO was getting
# only 3-4 points per wavelength while absorbing ~30 % of the light.
#
# Note the energy residual barely moved between those two meshes (+1.26 % vs
# +1.32 %). It compares TOTAL absorbed power against total flux, so it does
# not see error in how that total is PARTITIONED between layers -- which is
# exactly the quantity J_ph depends on. Convergence has to be judged on
# A_absorber itself.
cd "$(dirname "$0")"
source ./env.sh
export F3D_PROFILE=production
export F3D_CORES="${F3D_CORES:-14}"
export F3D_LINSOLVER=d1
export F3D_SKIN_FLOOR="${F3D_SKIN_FLOOR:-14}"
export F3D_CONV_TAG=_hi

python3 -u build/f3d_09_mesh_convergence.py 700 6.5 8 10
echo "HI_CONVERGENCE_DONE"
