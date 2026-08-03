"""FULL-3D stage 07 -- one sweep worker: solve an assigned list of wavelengths.

Takes tasks as `band:lambda` tokens, groups them by band, and loads each
band's solve-ready model (stage 06) once. It never writes the .mph, so any
number of workers can share the same model files.

Results are flushed per wavelength, so a worker that dies costs only the
points it had not reached. Re-running skips whatever is already in its shard.

Per-layer absorptance is the volume integral of the resistive loss density
ewfd.Qh over each named selection, normalised by the power incident on the
cell:

    P_inc   = |E0|^2 / (2 Z0) * A_cell     (E0 = 1 V/m peak, normal incidence)
    A_layer = integral(ewfd.Qh) / P_inc

ENERGY CHECK, and the reason to trust any of this: the back face is PEC, so
nothing is transmitted and absorptance + reflectance must equal 1. The net
downward Poynting flux through the air plane is read independently and
compared against the volume integral of Qh -- a surface quantity against a
volume quantity, so it tests the solve instead of restating it. The residual
is the primary mesh-convergence metric for the study.

Run:  python3 full3d/build/f3d_07_sweep_worker.py <worker_id> <band:lam> ...
"""
import sys, os, csv, time, jpype
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
import mph

wid = int(sys.argv[1])
tasks = []
for tok in sys.argv[2:]:
    b, l = tok.split(':')
    tasks.append((int(b), float(l)))
if not tasks:
    print('no wavelengths assigned; nothing to do')
    sys.exit(0)

Z0 = 376.730313668                       # free-space impedance, ohm
A_CELL = (C.PITCH * 1e-9) ** 2
P_INC = 1.0 ** 2 / (2 * Z0) * A_CELL

LAYERS = [('absorber', 'sel_abs'), ('Au', 'sel_au'), ('HTL', 'sel_htl'),
          ('TiO2', 'sel_etl'), ('FTO_total', 'sel_fto')]
if C.TEXTURED:
    # Diagnostic only: the cone is inside sel_fto already, so it is reported
    # separately but never added to the budget a second time.
    LAYERS.append(('cone', 'sel_cone'))
FIELDS = ['lambda_nm', 'band', 'n_elem', 'solve_s', 'worker'] + \
         [f'A_{n}' for n, _ in LAYERS] + \
         ['A_total', 'A_from_flux', 'R_implied', 'energy_residual']

os.makedirs(C.SHARDS, exist_ok=True)
OUT = os.path.join(C.SHARDS, f'{C.ABSORBER}_{C.PROFILE}_w{wid:02d}.csv')

done = set()
if os.path.exists(OUT):
    with open(OUT) as f:
        done = {(int(r['band']), float(r['lambda_nm']))
                for r in csv.DictReader(f)}
todo = [t for t in tasks if t not in done]
todo.sort()                       # group by band -> one model load per band

print(f'[w{wid:02d}] {len(tasks)} assigned, {len(todo)} to solve, '
      f'{C.CORES_PER_WORKER} cores', flush=True)
if not todo:
    print(f'[w{wid:02d}] nothing to do', flush=True)
    sys.exit(0)

client = mph.start(cores=C.CORES_PER_WORKER)
state = dict(band=None, model=None, java=None, nelem=0)


def load_band(band):
    """Swap in the solve-ready model for `band`, releasing the previous one."""
    if state['band'] == band:
        return
    if state['model'] is not None:
        try:
            client.remove(state['model'])
        except Exception:
            pass
    path = C.ready_path(band)
    t0 = time.time()
    model = client.load(path)
    java = model.java
    state.update(band=band, model=model, java=java,
                 nelem=int(java.component('comp1').mesh('mesh1').getNumElem()))
    print(f'[w{wid:02d}] band {band} loaded ({state["nelem"]} elements) '
          f'in {time.time()-t0:.0f} s', flush=True)


# ------------------------------------------------- generation profile G(z)
# The whole point of this study is to hand a NEW G(z) to the existing
# drift-diffusion model ("texture the optics, planarise the transport"), so
# the depth profile is extracted here, inside the solve that already exists.
# Doing it later would mean re-solving all 61 wavelengths a second time --
# hours of compute for data that costs seconds while the solution is in hand.
#
# The textured cell is NOT laterally uniform, so Qh is averaged over x and y
# at each depth before being handed to a 1D-in-z transport model. That lateral
# average is the honest reduction: it conserves total absorbed power per unit
# depth, which is what sets the generation rate.
NZ_PROFILE = 60
NXY_PROFILE = 15
_L = C.LAYERS
_Z_ABS0 = _L['h_au'] + _L['h_htl']
_Z_ABS1 = _Z_ABS0 + _L['h_abs']
_PAD = 1.5                                  # keep points off the interfaces
_zs = [_Z_ABS0 + _PAD + i * (_L['h_abs'] - 2 * _PAD) / (NZ_PROFILE - 1)
       for i in range(NZ_PROFILE)]
# CELL-CENTRED lateral sampling: x_i = (i + 1/2) * pitch / N tiles the unit
# cell with N equal sub-cells, so the plain mean of the samples IS the
# midpoint-rule average over the WHOLE cell, and no point lands on a periodic
# boundary (where evaluation is ambiguous).
#
# The earlier grid spanned [8, pitch-8] instead. That looks harmless but
# excludes ~9 % of the cell area, and the excluded border is exactly the flat
# region OUTSIDE the cone footprint (the cone spans 10-340 nm), where the
# field is genuinely different. It biased the depth-integrated photocurrent
# by -5 % against the independent spectral route -- which is precisely what
# the stage-14 cross-check is for.
_xy = [(i + 0.5) * C.PITCH / NXY_PROFILE for i in range(NXY_PROFILE)]
PROF = os.path.join(C.SHARDS, f'{C.ABSORBER}_{C.PROFILE}_w{wid:02d}_Gz.csv')
PROF_FIELDS = ['lambda_nm', 'band', 'z_nm', 'Qh_avg_W_m3']


def profile_points():
    xs, ys, zs = [], [], []
    for z in _zs:
        for x in _xy:
            for y in _xy:
                xs.append(x); ys.append(y); zs.append(z)
    return xs, ys, zs


_PX, _PY, _PZ = profile_points()


def extract_gz(java, dset, lam, band):
    """Laterally averaged Qh(z) through the absorber, W/m^3."""
    ds = java.result().dataset()
    if 'cpt_gz' in [str(t) for t in ds.tags()]:
        ds.remove('cpt_gz')
    cpt = ds.create('cpt_gz', 'CutPoint3D')
    cpt.set('data', dset)
    cpt.set('pointx', ' '.join(f'{v:.6g}' for v in _PX))
    cpt.set('pointy', ' '.join(f'{v:.6g}' for v in _PY))
    cpt.set('pointz', ' '.join(f'{v:.6g}' for v in _PZ))
    num = java.result().numerical()
    if 'ev_gz' in [str(t) for t in num.tags()]:
        num.remove('ev_gz')
    ev = num.create('ev_gz', 'EvalPoint')
    ev.set('data', 'cpt_gz')
    ev.set('expr', ['ewfd.Qh'])
    # getReal() is 2D for a multi-point evaluation and 1x1 for a scalar, so
    # flatten rather than assuming a shape.
    vals = []
    for r in ev.getReal():
        try:
            vals.extend(float(v) for v in r)
        except TypeError:
            vals.append(float(r))
    n = NXY_PROFILE * NXY_PROFILE
    if len(vals) != n * len(_zs):
        raise RuntimeError(f'expected {n*len(_zs)} points, got {len(vals)}')
    rows = []
    for i, z in enumerate(_zs):
        chunk = [v for v in vals[i * n:(i + 1) * n] if v == v]   # drop NaN
        if not chunk:
            continue
        rows.append({'lambda_nm': lam, 'band': band, 'z_nm': round(z, 3),
                     'Qh_avg_W_m3': f'{sum(chunk)/len(chunk):.6e}'})
    return rows


def find_dataset(java):
    """The dataset stage 06 attached to sol_opt, with a search fallback."""
    if 'dset_opt' in [str(t) for t in java.result().dataset().tags()]:
        return 'dset_opt'
    for d in [str(t) for t in java.result().dataset().tags()]:
        ds = java.result().dataset(d)
        try:
            if str(ds.getType()) == 'Solution' and \
               str(ds.getString('solution')) == 'sol_opt':
                return d
        except Exception:
            pass
    return None


def solve_one(band, lam):
    load_band(band)
    java = state['java']
    num = java.result().numerical()

    def clean(tag):
        if tag in [str(t) for t in num.tags()]:
            num.remove(tag)

    # Free the PREVIOUS wavelength's stored solution before solving the next.
    # Without this the worker's memory grows monotonically across the sweep --
    # measured at 63.8 GB after one solve and 68.8 GB after two on the same
    # 348k mesh -- because Comsol keeps each solution's data alive in the
    # model. On a 61-wavelength sweep that is an OOM, not a nuisance.
    try:
        java.sol('sol_opt').clearSolutionData()
    except Exception:
        try:
            java.sol('sol_opt').clearSolution()
        except Exception:
            pass

    java.param().set('lda0', f'{lam}[nm]')
    t0 = time.time()
    # Run the SOLVER, not the study. study.run() regenerates a default solver
    # sequence, which would silently put the direct solver back and blow the
    # memory budget; sol_opt is the iterative sequence stage 06 configured.
    java.sol('sol_opt').runAll()
    dt = time.time() - t0
    dset = find_dataset(java)

    row = {'lambda_nm': lam, 'band': band, 'n_elem': state['nelem'],
           'solve_s': round(dt, 1), 'worker': wid}
    tot = 0.0
    for name, selname in LAYERS:
        clean('iv')
        iv = num.create('iv', 'IntVolume')
        iv.set('data', dset)
        iv.selection().named(selname)
        iv.set('expr', ['ewfd.Qh'])
        a = float(num.get('iv').getReal()[0][0]) / P_INC
        row[f'A_{name}'] = round(a, 6)
        # FTO_total already includes the cone; the cone row is diagnostic
        # only, so it must not enter the budget a second time.
        if name != 'cone':
            tot += a
    row['A_total'] = round(tot, 6)

    try:
        clean('isf')
        isf = num.create('isf', 'IntSurface')
        isf.set('data', dset)
        isf.selection().named('sel_bnd_airpml')
        isf.set('expr', ['ewfd.Poavz'])
        A_flux = -float(isf.getReal()[0][0]) / P_INC
    except Exception as e:
        A_flux = float('nan')
        print(f'[w{wid:02d}]   flux read failed: {str(e)[:70]}', flush=True)
    row['A_from_flux'] = round(A_flux, 6)
    row['R_implied'] = round(1.0 - tot, 6)
    row['energy_residual'] = round(tot - A_flux, 6)

    # Wrapped: a failure here must never cost the absorptance result, which is
    # what the sweep exists for.
    gz = []
    try:
        gz = extract_gz(java, dset, lam, band)
    except Exception as e:
        print(f'[w{wid:02d}]   G(z) extraction failed: {str(e)[:90]}',
              flush=True)
    return row, gz


new_file = not os.path.exists(OUT)
new_prof = not os.path.exists(PROF)
with open(OUT, 'a', newline='') as fh, open(PROF, 'a', newline='') as pf:
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    pw = csv.DictWriter(pf, fieldnames=PROF_FIELDS)
    if new_file:
        w.writeheader()
        fh.flush()
    if new_prof:
        pw.writeheader()
        pf.flush()
    for band, lam in todo:
        try:
            row, gz = solve_one(band, lam)
        except Exception as e:
            print(f'[w{wid:02d}] b{band} lambda={lam:.0f} FAILED: '
                  f'{str(e)[:200]}', flush=True)
            continue
        w.writerow(row)
        fh.flush()
        if gz:
            pw.writerows(gz)
            pf.flush()
        flag = '' if abs(row['energy_residual']) < 0.02 else '  ** ENERGY DRIFT **'
        print(f'[w{wid:02d}] b{band} lambda={lam:6.0f} nm  '
              f'A_abs={row["A_absorber"]:.4f}  A_tot={row["A_total"]:.4f}  '
              f'resid={row["energy_residual"]:+.4f}  ({row["solve_s"]:.0f} s)'
              f'{flag}', flush=True)

print(f'[w{wid:02d}] WORKER DONE', flush=True)
