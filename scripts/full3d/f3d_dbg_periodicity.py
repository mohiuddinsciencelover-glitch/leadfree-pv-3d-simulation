"""Diagnostic: does the solution actually satisfy the periodic condition?

With kFloquet = 0 (normal incidence) the field on x = 0 must equal the field
on x = pitch, point for point, and likewise for y. This samples both faces at
matching coordinates and reports the mismatch.

It is a DIRECT test of the periodic-mesh fix. The convergence study can only
show that the answer stops moving; this shows the boundary condition is being
satisfied, which is the reason it stopped moving. Worth running before
committing to a long production sweep.

Run:  python3 full3d/build/f3d_dbg_periodicity.py [band] [lambda_nm]
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import config as C
import mph

band = int(sys.argv[1]) if len(sys.argv) > 1 else 2
lam = float(sys.argv[2]) if len(sys.argv) > 2 else 700.0
C.banner()
print(f'periodicity check: band {band}, lambda {lam:.0f} nm\n')

L = C.LAYERS
z_stack = L['h_au'] + L['h_htl'] + L['h_abs'] + L['h_etl'] + L['h_fto']
z_hi = z_stack + (C.TEXTURE['h'] if C.TEXTURED else 0.0) + C.AIR_CLEARANCE

# Sample away from the exact edges, where a point can land ambiguously on a
# geometry boundary and evaluate to NaN.
ys = np.linspace(8.0, C.PITCH - 8.0, 21)
zs = np.linspace(5.0, z_hi - 5.0, 61)
Yg, Zg = np.meshgrid(ys, zs, indexing='ij')
n = Yg.size

client = mph.start(cores=C.CORES)
model = client.load(C.ready_path(band))
java = model.java
java.param().set('lda0', f'{lam}[nm]')
t0 = time.time()
java.sol('sol_opt').runAll()
print(f'solved in {time.time()-t0:.0f} s')


def sample(xval, Y, Z, tag):
    ds = java.result().dataset()
    if tag in [str(t) for t in ds.tags()]:
        ds.remove(tag)
    cpt = ds.create(tag, 'CutPoint3D')
    cpt.set('data', 'dset_opt')
    cpt.set('pointx', ' '.join(f'{xval:.6g}' for _ in range(Y.size)))
    cpt.set('pointy', ' '.join(f'{v:.6g}' for v in Y.ravel()))
    cpt.set('pointz', ' '.join(f'{v:.6g}' for v in Z.ravel()))
    num = java.result().numerical()
    etag = 'ev_' + tag
    if etag in [str(t) for t in num.tags()]:
        num.remove(etag)
    ev = num.create(etag, 'EvalPoint')
    ev.set('data', tag)
    ev.set('expr', [EXPR])
    return np.array(ev.getReal(), dtype=float).ravel()


def compare(name, a, b, verdict=True):
    """Report the mismatch both pointwise and normalised by the RMS field.

    A pointwise relative error blows up wherever |E| passes through a node,
    so it alone cannot distinguish a real periodicity violation from a
    near-zero denominator. The RMS-normalised error is the meaningful
    figure of merit; the pointwise max is kept alongside it as a locator.
    """
    m = np.isfinite(a) & np.isfinite(b)
    if not m.any():
        print(f'{name}: no valid sample points')
        return
    a, b = a[m], b[m]
    rms = float(np.sqrt(np.mean(a ** 2)))
    err = np.abs(a - b)
    norm = err / rms if rms > 0 else err
    scale = np.maximum(np.abs(a), np.abs(b))
    good = scale > 1e-12
    rel = np.abs(a[good] - b[good]) / scale[good]
    print(f'{name}: {m.sum()} points')
    print(f'         vs RMS field: max {100*norm.max():.4f} %, '
          f'rms {100*float(np.sqrt(np.mean(norm**2))):.5f} %')
    print(f'         pointwise   : max {100*rel.max():.4f} %, '
          f'median {100*np.median(rel):.5f} %')
    if not verdict:
        print('         (informational only -- includes the normal component, '
              'which is\n          interpolated from one side when sampled '
              'exactly on the face)')
        return
    ok = norm.max() < 0.01           # 1 % of the RMS field anywhere
    print('         -> ' + ('PERIODIC (paired-face meshes match)' if ok else
                            '** NOT PERIODIC -- paired-face meshes mismatched **'))


# The periodic condition constrains the TANGENTIAL field. The normal
# component is not continuous in the same sense and, evaluated exactly on a
# boundary, is interpolated from whichever side the evaluator picks -- so it
# reports a mismatch that is an artefact of sampling, not of the mesh. That
# matters here because the incident wave is x-polarised: E_x is normal at
# precisely the x = 0 / x = pitch pair, which is why those faces looked far
# worse than the y pair even when both copies were exact.
EXPR = 'sqrt(abs(ewfd.Ey)^2+abs(ewfd.Ez)^2)'      # tangential on the x faces
ex0 = sample(0.0, Yg, Zg, 'cpt_x0')
ex1 = sample(C.PITCH, Yg, Zg, 'cpt_x1')
compare('x = 0 vs x = pitch  [tangential Ey,Ez]', ex0, ex1)

EXPR = 'ewfd.normE'
compare('x = 0 vs x = pitch  [|E|, incl. normal Ex]',
        sample(0.0, Yg, Zg, 'cpt_x0n'), sample(C.PITCH, Yg, Zg, 'cpt_x1n'),
        verdict=False)

Xg = Yg      # reuse the same in-plane grid, now as x
ds = java.result().dataset()


def sample_y(yval, X, Z, tag):
    if tag in [str(t) for t in ds.tags()]:
        ds.remove(tag)
    cpt = ds.create(tag, 'CutPoint3D')
    cpt.set('data', 'dset_opt')
    cpt.set('pointx', ' '.join(f'{v:.6g}' for v in X.ravel()))
    cpt.set('pointy', ' '.join(f'{yval:.6g}' for _ in range(X.size)))
    cpt.set('pointz', ' '.join(f'{v:.6g}' for v in Z.ravel()))
    num = java.result().numerical()
    etag = 'ev_' + tag
    if etag in [str(t) for t in num.tags()]:
        num.remove(etag)
    ev = num.create(etag, 'EvalPoint')
    ev.set('data', tag)
    ev.set('expr', [EXPR])       # must follow EXPR, as sample() does
    return np.array(ev.getReal(), dtype=float).ravel()


EXPR = 'sqrt(abs(ewfd.Ex)^2+abs(ewfd.Ez)^2)'      # tangential on the y faces
compare('y = 0 vs y = pitch  [tangential Ex,Ez]',
        sample_y(0.0, Xg, Zg, 'cpt_yy0'), sample_y(C.PITCH, Xg, Zg, 'cpt_yy1'))

EXPR = 'ewfd.normE'
compare('y = 0 vs y = pitch  [|E|, incl. normal Ey]',
        sample_y(0.0, Xg, Zg, 'cpt_yy0n'),
        sample_y(C.PITCH, Xg, Zg, 'cpt_yy1n'), verdict=False)
print('\nDBG PERIODICITY DONE', flush=True)
