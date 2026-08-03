"""FULL-3D stage 09 -- mesh convergence study at fixed wavelengths.

Two jobs, one run:

 1. EVIDENCE. A reviewer of a full-wave 3D result will ask how the mesh was
    chosen. "8 points per wavelength" is an assertion; absorptance that stops
    moving as the mesh is refined is evidence. This produces the latter.

 2. SIZING. The production mesh should be the COARSEST one whose answer has
    stopped changing, not the finest one that fits in memory. Cost rises as
    ppw^3, so guessing high is expensive -- at ppw = 8 the blue band reached
    836k elements, and refining past convergence buys nothing but wall-clock.

For each ppw the script rebuilds the mesh, solves the given wavelengths, and
records absorber absorptance plus the independent energy-conservation
residual. Convergence is judged on A_absorber, since that is what J_ph is
computed from; the residual is reported alongside as a second, independent
check that is not derived from the same integral.

Run:  python3 full3d/build/f3d_09_mesh_convergence.py <lam_nm> [ppw ...]
"""
import sys, os, csv, time, json, jpype
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
import f3d_optics as O
import f3d_mesh as M
import mph

lam = float(sys.argv[1]) if len(sys.argv) > 1 else 700.0
ppws = [float(x) for x in sys.argv[2:]] or [3.0, 4.0, 5.0, 6.5, 8.0]
C.banner()
print(f'convergence at lambda = {lam:.0f} nm, ppw = {ppws}\n')

Z0 = 376.730313668
A_CELL = (C.PITCH * 1e-9) ** 2
P_INC = 1.0 / (2 * Z0) * A_CELL
LAYERS = [('absorber', 'sel_abs'), ('Au', 'sel_au'), ('HTL', 'sel_htl'),
          ('TiO2', 'sel_etl'), ('FTO_total', 'sel_fto')]

TAG = os.environ.get('F3D_CONV_TAG', '')
OUT = os.path.join(C.RESULTS,
                   f'f3d_{C.ABSORBER}_convergence_{int(lam)}nm{TAG}.csv')
os.makedirs(C.RESULTS, exist_ok=True)

client = mph.start(cores=C.CORES)
model = client.load(C.MODEL_PATH)
java = model.java
comp = java.component('comp1')
java.param().set('lda0', f'{lam}[nm]')

rows = []
for ppw in ppws:
    print(f'--- ppw = {ppw} ---')
    sizes = O.mesh_sizes(lam, ppw, C.MESH['hmin'], C.MESH['hmax_cap'],
                         C.MESH['skin_floor'], verbose=False)
    print('    ' + '  '.join(f'{m}={h:.1f}' for m, h in sizes.items()))

    # Same builder stage 06 uses, so this study measures the mesh that
    # actually produces the results -- periodic face copy included.
    nelem, _ = M.build(comp, sizes)

    stags = [str(t) for t in java.study().tags()]
    if 'std_opt' not in stags:
        std = java.study().create('std_opt')
        fr = std.create('freq', 'Frequency')
        fr.set('plist', 'f0')
        fr.setSolveFor('/physics/ewfd', True)
    sols = java.sol()
    for t in [str(x) for x in sols.tags()]:
        sols.remove(t)
    sol = sols.create('sol_opt')
    sol.study('std_opt')
    sol.attach('std_opt')
    sol.createAutoSequence('std_opt')
    sol.feature('s1').feature('fc1').set('linsolver', C.SOLVER['linsolver'])

    dsets = java.result().dataset()
    if 'dset_opt' in [str(t) for t in dsets.tags()]:
        dsets.remove('dset_opt')
    ds = dsets.create('dset_opt', 'Solution')
    ds.set('solution', 'sol_opt')

    t0 = time.time()
    try:
        sol.runAll()
    except Exception as e:
        print(f'    SOLVE FAILED: {str(e)[:160]}', flush=True)
        continue
    dt = time.time() - t0

    num = java.result().numerical()

    def clean(tag):
        if tag in [str(t) for t in num.tags()]:
            num.remove(tag)

    row = {'ppw': ppw, 'n_elem': nelem, 'solve_s': round(dt, 1)}
    tot = 0.0
    for name, selname in LAYERS:
        clean('iv')
        iv = num.create('iv', 'IntVolume')
        iv.set('data', 'dset_opt')
        iv.selection().named(selname)
        iv.set('expr', ['ewfd.Qh'])
        a = float(num.get('iv').getReal()[0][0]) / P_INC
        row[f'A_{name}'] = round(a, 6)
        tot += a
    row['A_total'] = round(tot, 6)
    clean('isf')
    isf = num.create('isf', 'IntSurface')
    isf.set('data', 'dset_opt')
    isf.selection().named('sel_bnd_airpml')
    isf.set('expr', ['ewfd.Poavz'])
    row['A_from_flux'] = round(-float(isf.getReal()[0][0]) / P_INC, 6)
    row['energy_residual'] = round(row['A_total'] - row['A_from_flux'], 6)
    rows.append(row)
    print(f'    {nelem:8d} elem  A_abs={row["A_absorber"]:.5f}  '
          f'A_tot={row["A_total"]:.5f}  resid={row["energy_residual"]:+.5f}  '
          f'({dt:.0f} s)', flush=True)

    with open(OUT, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

print(f'\nresults -> {OUT}')
if len(rows) > 1:
    ref = rows[-1]['A_absorber']
    print(f'\nrelative to the finest mesh (ppw={rows[-1]["ppw"]}, '
          f'A_abs={ref:.5f}):')
    for r in rows:
        print(f'  ppw {r["ppw"]:4.1f}  {r["n_elem"]:8d} elem  '
              f'dA/A = {100*(r["A_absorber"]-ref)/ref:+7.3f} %   '
              f'resid {r["energy_residual"]:+.4f}   {r["solve_s"]:6.0f} s')
print('\nSTAGE 09 DONE', flush=True)
