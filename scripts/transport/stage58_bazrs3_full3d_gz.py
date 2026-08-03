"""Stage 58 -- re-run the BaZrS3/Spiro transport with the full-wave 3D G(z).

WHY. The parent optical stage was refreshed with the corrected full-wave 3D
pipeline (real FTO dispersion, fixed Floquet periodic mesh, fixed AM1.5G
quadrature) AND with the MEASURED Nishigaki 2020 dielectric function in place
of the DFT-computed KK file. BaZrS3's ideal Jsc fell 12.29 -> 10.31 mA/cm2.
The published device Jsc of 11.85 therefore EXCEEDS the refreshed optical
ceiling, which is impossible: the transport model was being fed generation
that the measured optics say does not occur.

WHAT THIS DOES. Restores the model to its Spiro-OMeTAD HTL configuration (the
work model was left in its CuO state by stage 32), points Gz_fn at a chosen
G(z) profile, and runs the forward-bias J-V exactly as stage 37 did.

CONTROL DISCIPLINE. Run this twice:
    control    -> the OLD Spiro profile; MUST reproduce Jsc 11.85 / Voc 1.341 /
                  FF 0.340 / PCE 5.40%. If it does not, the Spiro restoration
                  is not faithful and nothing downstream can be attributed to
                  the new optics.
    full3d     -> the new profile. The difference is then the real effect.

B_RAD. The published B_rad = 2.335e-9 cm^3/s reproduces the van
Roosbroeck-Shockley integral over the OLD KK optics taken from 1.75 eV -- but
the model's own Eg_abs is 1.88 eV and its ni^2 is built from 1.88, so the
published value pairs a 1.75 eV integral with a 1.88 eV ni^2 and is ~12x too
large even on its own optics. Redone consistently at 1.88 eV over the MEASURED
Nishigaki data it is 5.37e-12 cm^3/s, ~435x smaller, because VRS weights the
band edge through the Boltzmann factor and the measured near-edge absorption
is far weaker than the DFT-computed KK file's. Pass b_rad to test it.

Usage: python3 stage58_bazrs3_full3d_gz.py <name> <gz_csv> <rerun_std2:0|1> [b_rad]
"""
import mph, numpy as np, traceback, sys, os

MODEL = '/home/mohiuddin/Desktop/COMSOL_SOLAR_CELL/models/BaZrS3_pilot_3d_full3d.mph'
OUTDIR = '/home/mohiuddin/Desktop/COMSOL_SOLAR_CELL/results'
os.makedirs(OUTDIR, exist_ok=True)

name, gz_csv, rerun_std2 = sys.argv[1], sys.argv[2], sys.argv[3] == '1'
b_rad = sys.argv[4] if len(sys.argv) > 4 else None

# Spiro-OMeTAD HTL. Values read back from models/BaZrS3_pilot_3d.mph, the
# saved PRE-CuO-swap state -- NOT from build_stage15_heterojunction.py, which
# sets Na_htl = 1e19. Some later stage changed it to 1e18 and only the model
# records that; using the script value gives Jsc 12.095 / FF 0.381 instead of
# the published 11.846 / 0.340, because extra HTL doping eases hole
# extraction. The control run below is what caught it.
SPIRO = {
    'Eg_htl':   ('2.9[V]',           'Spiro band gap [Rahman 2023]'),
    'chi_htl':  ('2.15[V]',          'Spiro electron affinity, avg 2.1-2.2 eV'),
    'epsr_htl': ('3',                'Spiro rel. permittivity'),
    'mun_htl':  ('1e-4[cm^2/(V*s)]', 'Spiro electron mobility [Rahman 2023]'),
    'mup_htl':  ('1e-4[cm^2/(V*s)]', 'Spiro hole mobility [Rahman 2023]'),
    'Nc_htl':   ('2.2e18[1/cm^3]',   'Spiro Nc [Rahman 2023]'),
    'Nv_htl':   ('2.2e18[1/cm^3]',   'Spiro Nv [Rahman 2023]'),
    'Na_htl':   ('1e18[1/cm^3]',     'Spiro p-type doping, as-saved pre-swap state'),
}

client = mph.start(cores=2)
model = client.load(MODEL)
m = model.java
p = m.param()
semi = m.component('comp1').physics('semi')
udg1 = semi.feature('udg1')

for k, (v, d) in SPIRO.items():
    p.set(k, v, d)
print('HTL -> Spiro-OMeTAD', flush=True)

m.func('Gz_fn').set('filename', gz_csv)
print(f'Gz_fn -> {gz_csv}', flush=True)

if b_rad is not None:
    p.set('B_rad', b_rad,
          'radiative coeff - VRS from MEASURED Nishigaki 2020 optics, '
          'integrated from Eg_abs=1.88 eV consistently with ni2_abs')
    print(f'B_rad -> {b_rad}', flush=True)

semi.feature('tsrh1').active(True)
semi.feature('udr_rad').active(True)
p.set('chi_abs', '4.1[V]')
p.set('tau_srh', '1[ns]')
p.set('ramp', '1e-8')
# Thermionic-emission interface model: the published Spiro case is 'spiroTE'.
semi.feature('hetero1').set('HeteroModelSelection', '2')
semi.feature('hetero2').set('HeteroModelSelection', '2')
# No interface recombination, matching the published base case.
semi.feature('surf_htl').active(False)
semi.feature('surf_etl').active(False)
# FORWARD bias = negative Vapp on the top (n-side) contact.
m.study('std5').feature('stat5').setIndex('plistarr', 'range(0,-0.025,-1.5)', 1)


def remove_sols(study):
    while True:
        hit = False
        for stag in [str(t) for t in m.sol().tags()]:
            try:
                if str(m.sol(stag).study()) == study:
                    m.sol().remove(stag); hit = True; break
            except Exception:
                pass
        if not hit:
            return


def dataset_of(study):
    tag = None
    for stag in [str(t) for t in m.sol().tags()]:
        try:
            if str(m.sol(stag).study()) == study and len(m.sol(stag).feature().tags()) > 0:
                tag = stag
        except Exception:
            pass
    dt = None
    for d in [str(t) for t in m.result().dataset().tags()]:
        ds = m.result().dataset(d)
        try:
            if str(ds.getType()) == 'Solution' and str(ds.getString('solution')) == tag \
               and 'Store' not in str(ds.label()):
                dt = d
        except Exception:
            pass
    return dt


print(f'=== CASE {name} (gz={os.path.basename(gz_csv)}) ===', flush=True)
try:
    remove_sols('std3')
    if rerun_std2:
        # Band offsets moved when the HTL parameters changed, so the
        # equilibrium/continuation solve must be redone before the sweep.
        udg1.active(False)
        remove_sols('std2')
        m.study('std2').run()
        print('  std2 re-solved', flush=True)
    udg1.active(True)
    remove_sols('std5')
    m.study('std5').run()
    print('  std5 solved', flush=True)
    dt = dataset_of('std5')
    nt = [str(t) for t in m.result().numerical().tags()]
    if 'gev_jv' in nt:
        m.result().numerical().remove('gev_jv')
    g = m.result().numerical().create('gev_jv', 'EvalGlobal')
    g.set('data', dt)
    g.set('expr', ['Vapp', 'semi.I0_4', 'semi.I0_3'])
    arr = np.array(g.getReal())
    np.savetxt(f'{OUTDIR}/jv_{name}.csv', arr, delimiter=',',
               header='rows: Vapp_V | I_top_A | I_bottom_A')
    print(f'  saved jv_{name}.csv shape={arr.shape}', flush=True)
    model.save()
    print('  OK', flush=True)
except Exception:
    traceback.print_exc()
    print(f'  CASE {name} FAILED', flush=True)
    sys.exit(1)
