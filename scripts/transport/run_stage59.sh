#!/bin/bash
# Stage 59 -- re-run FASnI3, Cs2AgBiBr6 and Cu2AgBiI6 transport on the
# refreshed full-wave 3D G(z), same treatment BaZrS3 got in stage 58.
#
# CONTROL DISCIPLINE. Each absorber gets a control run on its OLD G(z) first.
# It must reproduce the published base case before the new-G(z) result is
# believed. In stage 58 exactly this caught a wrong Na_htl that would have
# masked the real optical change. Controls run on the standard 25 mV grid --
# Jsc and Voc are step-size independent, so that is a sufficient check and
# costs minutes instead of hours.
#
# Cu2AgBiI6 NEEDS the 1 mV grid (941 points) for its TREATMENT run: at 25 mV
# the base case lands on spurious S-NDR branches and reports FF 4.13 /
# PCE 86.6%. Only the dense curve is a valid device result -- the published
# 13.856 / 1.512 / 0.473 / 9.91% comes from jv_cabi_light_base_dense.csv.
#
# Runs sequentially: one COMSOL session at a time is this box's memory budget.
set -u
cd /home/mohiuddin/Desktop/COMSOL_SOLAR_CELL
S=build_scripts/stage44_run_case.py
R=full3d/results
ts() { date +%H:%M:%S; }

# --- FASnI3 (Spiro; published base 14.74 / 0.987 / 0.517 / 7.52%) ----------
cp -f models/FASnI3_pilot_3d.mph models/FASnI3_pilot_3d_full3d.mph
echo "#### $(ts) FASnI3 control (old G(z))"
python3 -u $S models/FASnI3_pilot_3d_full3d.mph f3dctrl_fasni3_light_base 1 1 1 \
  "chi_abs=3.5[V]" "tau_srh=43[ns]" "epsr_abs=8.2" || true
echo "#### $(ts) FASnI3 treatment (new G(z))"
python3 -u $S models/FASnI3_pilot_3d_full3d.mph f3d_fasni3_light_base 1 0 1 \
  "chi_abs=3.5[V]" "tau_srh=43[ns]" "epsr_abs=8.2" \
  "GZ=/home/mohiuddin/Desktop/COMSOL_SOLAR_CELL/$R/f3d_FASnI3_planar_Gz_AM15G_forTransport.csv" || true

# --- Cs2AgBiBr6 (Spiro; published base 2.010 / 1.711 / 0.286 / 0.98%) ------
cp -f models/Cs2AgBiBr6_pilot_3d.mph models/Cs2AgBiBr6_pilot_3d_full3d.mph
echo "#### $(ts) Cs2AgBiBr6 control (old G(z))"
python3 -u $S models/Cs2AgBiBr6_pilot_3d_full3d.mph f3dctrl_cs_light_base 1 1 1 \
  "chi_abs=4.0[V]" "tau_srh=13.7[ns]" "epsr_abs=5.8" "VEND=-1.9" "T_dev=300[K]" || true
echo "#### $(ts) Cs2AgBiBr6 treatment (new G(z))"
python3 -u $S models/Cs2AgBiBr6_pilot_3d_full3d.mph f3d_cs_light_base 1 0 1 \
  "chi_abs=4.0[V]" "tau_srh=13.7[ns]" "epsr_abs=5.8" "VEND=-1.9" "T_dev=300[K]" \
  "GZ=/home/mohiuddin/Desktop/COMSOL_SOLAR_CELL/$R/f3d_Cs2AgBiBr6_planar_Gz_AM15G_forTransport.csv" || true

# --- Cu2AgBiI6 (Spiro; published base 13.856 / 1.512 / 0.473 / 9.91%) ------
cp -f models/Cu2AgBiI6_pilot_3d.mph models/Cu2AgBiI6_pilot_3d_full3d.mph
echo "#### $(ts) Cu2AgBiI6 control (old G(z), 25 mV -- Jsc/Voc check only)"
python3 -u $S models/Cu2AgBiI6_pilot_3d_full3d.mph f3dctrl_cabi_light_base 1 1 1 \
  "chi_abs=3.22[V]" "tau_srh=33[ns]" "epsr_abs=6.3" "Na_abs=1e12[1/cm^3]" \
  "VEND=-1.9" "T_dev=300[K]" || true
echo "#### $(ts) Cu2AgBiI6 treatment (new G(z), 1 mV dense -- required, S-NDR)"
python3 -u $S models/Cu2AgBiI6_pilot_3d_full3d.mph f3d_cabi_light_base_dense 1 0 1 \
  "chi_abs=3.22[V]" "tau_srh=33[ns]" "epsr_abs=6.3" "Na_abs=1e12[1/cm^3]" \
  "VLIST=range(0,-0.001,-1.9)" "T_dev=300[K]" \
  "GZ=/home/mohiuddin/Desktop/COMSOL_SOLAR_CELL/$R/f3d_Cu2AgBiI6_planar_Gz_AM15G_forTransport.csv" || true

echo "#### $(ts) STAGE59_ALL_DONE"
