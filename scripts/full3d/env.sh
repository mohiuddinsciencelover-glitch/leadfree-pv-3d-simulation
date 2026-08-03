# Environment for the FULL-3D study on the 96-core server.
# Sourced by runbg.sh, which uses `set -u`, so every expansion is guarded.
export COMSOL_ROOT="$HOME/comsol_zip/comsol63/multiphysics"
export PATH="$COMSOL_ROOT/bin:$PATH"          # MPh locates Comsol via `which comsol`
export PYTHONPATH="$HOME/.local/lib/python3.8/site-packages${PYTHONPATH:+:$PYTHONPATH}"
# Comsol scratch/recovery data, kept off the home directory
export CSTMPDIR="${CSTMPDIR:-$HOME/.comsol_tmp}"
mkdir -p "$CSTMPDIR"
