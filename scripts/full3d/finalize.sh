#!/usr/bin/env bash
# Everything that happens after the sweeps finish, in one command.
#
# Exists because the pipeline that is currently running was launched from an
# older copy of launch_production.sh (rsync renames rather than writing in
# place, so a running bash keeps the file it started with). That copy predates
# the G(z) stage, so this covers the gap -- and it is useful anyway as a
# re-runnable "regenerate every derived product from the shards" step.
#
# Safe to re-run: every stage here reads the shards and rewrites its outputs.
set -u
cd "$(dirname "$0")"
source ./env.sh
export F3D_PROFILE="${F3D_PROFILE:-production}"

echo "############ merge shards -> spectra ############"
for variant in textured planar; do
  case "$variant" in
    textured) export F3D_TEXTURE=on  ;;
    planar)   export F3D_TEXTURE=off ;;
  esac
  echo "-- ${variant}"
  python3 -u build/f3d_08_sweep_driver.py --merge-only || true
done

echo
echo "############ G(z) for the transport model ############"
for variant in textured planar; do
  python3 -u build/f3d_14_generation_profile.py "$variant" || true
done

echo
echo "############ photocurrent + loss budget ############"
TEX=results/f3d_FASnI3_absorptance_production.csv
PLN=results/f3d_FASnI3_absorptance_production_planar.csv
if [ -f "$TEX" ] && [ -f "$PLN" ]; then
  python3 -u build/f3d_10_photocurrent.py "$TEX" "$PLN" --compare || true
elif [ -f "$TEX" ]; then
  echo "(planar reference not present yet -- reporting textured only)"
  python3 -u build/f3d_10_photocurrent.py "$TEX" || true
fi

echo
echo "############ figures ############"
export F3D_TEXTURE=on
python3 -u build/f3d_11_figures.py || true
python3 -u build/f3d_13_periodic_fix_figure.py || true

echo
echo "FINALIZE DONE $(date -Is)"
echo "figures -> full3d/results/figures/"
