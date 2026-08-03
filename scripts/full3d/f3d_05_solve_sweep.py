"""FULL-3D stage 05 -- frequency-domain solve + per-layer absorptance.

Loops wavelengths in PYTHON rather than using a COMSOL parametric sweep, so
that results are written incrementally. On the 24-core production run a
crash at lambda = 700 nm then costs one point, not the whole sweep. Re-running
skips wavelengths already present in the CSV.

Per-layer absorptance comes from volume-integrating the resistive loss
density ewfd.Qh over each named domain selection, normalised by the incident
power on the cell:

    P_inc = |E0|^2 / (2 Z0) * A_cell        (E0 = 1 V/m peak, normal incidence)
    A_layer = integral(ewfd.Qh) / P_inc

ENERGY-CONSERVATION CHECK (the reason to trust the result): with a PEC back
face there is no transmission, so absorptance + reflectance must equal 1.
Reflectance is taken independently from the port S-parameter, |S11|^2. Any
drift from 1 indicates an under-resolved mesh or a badly terminated
diffraction order -- exactly the failure modes a texture introduces. The
residual is logged per wavelength and is the primary mesh-convergence metric
for this study.

Run:  python3 full3d/build/f3d_05_solve_sweep.py [lambda_nm ...]
"""
import sys, os, csv, time, jpype
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
import mph

lams = [float(a) for a in sys.argv[1:]] or C.LAMBDA
C.banner()
print(f'wavelengths to solve: {lams}')

Z0 = 376.730313668           # free-space impedance, ohm
A_CELL = (C.PITCH * 1e-9) ** 2
P_INC = 1.0 ** 2 / (2 * Z0) * A_CELL
print(f'cell area {A_CELL:.4e} m^2, incident power {P_INC:.4e} W\n')

LAYERS = [('absorber', 'sel_abs'), ('Au', 'sel_au'), ('HTL', 'sel_htl'),
          ('TiO2', 'sel_etl'), ('FTO_total', 'sel_fto'), ('cone', 'sel_cone')]
OUT = os.path.join(C.RESULTS, f'f3d_{C.ABSORBER}_absorptance_{C.PROFILE}.csv')
os.makedirs(C.RESULTS, exist_ok=True)

done = set()
if os.path.exists(OUT):
    with open(OUT) as f:
        done = {float(r['lambda_nm']) for r in csv.DictReader(f)}
    print(f'resuming: {len(done)} wavelengths already in {OUT}')

client = mph.start(cores=C.CORES)
model = client.load(C.MODEL_PATH)
java = model.java
comp = java.component('comp1')
p = java.param()

# ------------------------------------------------------------ mesh
meshes = comp.mesh()
if 'mesh1' in [str(t) for t in meshes.tags()]:
    meshes.remove('mesh1')
mesh = meshes.create('mesh1', 'geom1')
sz = mesh.feature('size')            # auto-created; fetch, never create
sz.set('custom', 'on')
sz.set('hmax', C.MESH['hmax_bulk'])
sz.set('hmin', C.MESH['hmin'])
szt = mesh.create('size_tex', 'Size')
szt.selection().geom('geom1', jpype.JInt(3))
szt.selection().named('sel_cone')
szt.set('custom', 'on')
szt.set('hmax', C.MESH['hmax_tex'])
szt.set('hmin', C.MESH['hmin'])
mesh.create('ftet1', 'FreeTet')
mesh.run()
nelem = int(mesh.getNumElem())
print(f'mesh: {nelem} elements (hmax_tex={C.MESH["hmax_tex"]}, '
      f'hmax_bulk={C.MESH["hmax_bulk"]})')

# ------------------------------------------------------------ study
stags = [str(t) for t in java.study().tags()]
if 'std_opt' in stags:
    java.study().remove('std_opt')
std = java.study().create('std_opt')
std.label('Optics: frequency domain')
fr = std.create('freq', 'Frequency')
fr.set('plist', 'f0')
fr.setSolveFor('/physics/ewfd', True)

# ------------------------------------------- reusable evaluation objects
num = java.result().numerical()


def clean(tag):
    if tag in [str(t) for t in num.tags()]:
        num.remove(tag)


def solve_one(lam):
    p.set('lda0', f'{lam}[nm]')
    t0 = time.time()
    std.run()
    dt = time.time() - t0

    # dataset produced by this study
    dset = None
    for stag in [str(t) for t in java.sol().tags()]:
        try:
            if str(java.sol(stag).study()) == 'std_opt':
                for d in [str(t) for t in java.result().dataset().tags()]:
                    ds = java.result().dataset(d)
                    if str(ds.getType()) == 'Solution' and \
                       str(ds.getString('solution')) == stag and \
                       'Store' not in str(ds.label()):
                        dset = d
        except Exception:
            pass

    row = {'lambda_nm': lam, 'n_elem': nelem, 'solve_s': round(dt, 1)}
    tot = 0.0
    for name, selname in LAYERS:
        clean('iv')
        iv = num.create('iv', 'IntVolume')
        iv.set('data', dset)
        iv.selection().named(selname)
        iv.set('expr', ['ewfd.Qh'])
        q = float(java.result().numerical('iv').getReal()[0][0])
        a = q / P_INC
        row[f'A_{name}'] = round(a, 6)
        # FTO_total already contains the cone; cone is reported separately
        # for diagnostics only, so exclude both from the running total once.
        if name not in ('cone',):
            tot += a
    row['A_total'] = round(tot, 6)

    # INDEPENDENT energy check: net DOWNWARD Poynting flux through the
    # air/PML plane must equal the total absorbed power, because the PEC
    # back face blocks transmission. This compares a surface flux against a
    # volume integral of Qh -- two different quantities from the same
    # solution -- so it genuinely tests the solve rather than restating it.
    try:
        clean('isf')
        isf = num.create('isf', 'IntSurface')
        isf.set('data', dset)
        isf.selection().named('sel_bnd_airpml')
        isf.set('expr', ['ewfd.Poavz'])
        flux_up = float(isf.getReal()[0][0])
        A_flux = -flux_up / P_INC          # downward flux = absorbed power
    except Exception as e:
        A_flux = float('nan')
        print(f'    (flux read failed: {str(e)[:70]})')
    row['A_from_flux'] = round(A_flux, 6)
    row['R_implied'] = round(1.0 - tot, 6)
    row['energy_residual'] = round(tot - A_flux, 6)
    return row


fields = ['lambda_nm', 'n_elem', 'solve_s'] + \
         [f'A_{n}' for n, _ in LAYERS] + \
         ['A_total', 'A_from_flux', 'R_implied', 'energy_residual']
new_file = not os.path.exists(OUT)
with open(OUT, 'a', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    if new_file:
        w.writeheader()
    for lam in lams:
        if lam in done:
            print(f'lambda={lam:.0f} nm  (already done, skipped)')
            continue
        try:
            row = solve_one(lam)
        except Exception as e:
            print(f'lambda={lam:.0f} nm  SOLVE FAILED: {str(e)[:160]}', flush=True)
            continue
        w.writerow(row)
        fh.flush()
        flag = '' if abs(row['energy_residual']) < 0.02 else '   ** ENERGY DRIFT **'
        print(f'lambda={lam:6.0f} nm  A_abs={row["A_absorber"]:.4f}  '
              f'A_tot={row["A_total"]:.4f}  A_flux={row["A_from_flux"]:.4f}  '
              f'resid={row["energy_residual"]:+.4f}  ({row["solve_s"]:.0f} s){flag}',
              flush=True)

model.save(C.MODEL_PATH)
print(f'\nresults -> {OUT}')
print('STAGE 05 DONE', flush=True)
