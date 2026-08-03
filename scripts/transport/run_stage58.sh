#!/bin/bash
# BaZrS3 transport rerun with the full-wave 3D G(z). Sequential: this box has
# 7 GB RAM and one COMSOL session at a time is the memory budget.
cd /home/mohiuddin/Desktop/COMSOL_SOLAR_CELL
S=build_scripts/stage58_bazrs3_full3d_gz.py
NEW=/home/mohiuddin/Desktop/COMSOL_SOLAR_CELL/BaZrS3_Gz_profile_AM15G_full3d.csv

# Variant A: new G(z) only -- isolates the optical effect.
cp -f models/BaZrS3_pilot_3d_work.mph models/BaZrS3_pilot_3d_full3d.mph
python3 -u $S f3d_spiroTE_light_chi4p1_tau1ns "$NEW" 1

# Variant B: new G(z) + VRS B_rad redone on the measured optics at Eg=1.88.
cp -f models/BaZrS3_pilot_3d_work.mph models/BaZrS3_pilot_3d_full3d.mph
python3 -u $S f3d_spiroTE_light_chi4p1_tau1ns_Brad "$NEW" 1 '5.373e-12[cm^3/s]'

echo "STAGE58_ALL_DONE"
