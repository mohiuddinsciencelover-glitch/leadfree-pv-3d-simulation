"""FULL-3D stage 12 -- absorbed-power maps on a vertical cut through the cone.

The point of a textured 3D study is that the field is NOT laterally uniform.
This extracts the resistive loss density ewfd.Qh on an (x, z) plane through
the middle of the cell and writes it as a CSV, so the figure can be drawn in
matplotlib in the same style as every other figure in the paper rather than
as a Comsol screenshot in a different font.

Extraction goes through a CutPoint3D dataset and EvalPoint, i.e. the field is
sampled at coordinates chosen here, not at mesh nodes. That keeps the output
grid independent of the mesh, so textured and planar maps are directly
comparable pixel for pixel even though their meshes differ.

Run:  python3 full3d/build/f3d_12_fieldmap.py [lambda_nm] [nx] [nz]
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import config as C
import mph

lam = float(sys.argv[1]) if len(sys.argv) > 1 else 700.0
NX = int(sys.argv[2]) if len(sys.argv) > 2 else 141
NZ = int(sys.argv[3]) if len(sys.argv) > 3 else 301
band = C.band_of(lam)
C.banner()
print(f'field map at {lam:.0f} nm (band {band}), grid {NX} x {NZ}')

L = C.LAYERS
z_top_stack = (L['h_au'] + L['h_htl'] + L['h_abs'] + L['h_etl'] + L['h_fto'])
z_max = z_top_stack + (C.TEXTURE['h'] if C.TEXTURED else 0.0) + 150.0
xs = np.linspace(0.0, C.PITCH, NX)
zs = np.linspace(0.0, z_max, NZ)
X, Z = np.meshgrid(xs, zs, indexing='ij')
Y = np.full(X.size, C.PITCH / 2.0)      # cut through the cone axis

client = mph.start(cores=C.CORES)
model = client.load(C.ready_path(band))
java = model.java
java.param().set('lda0', f'{lam}[nm]')
t0 = time.time()
java.sol('sol_opt').runAll()
print(f'solved in {time.time()-t0:.0f} s')


def fmt(a):
    return ' '.join(f'{v:.6g}' for v in a)


ds = java.result().dataset()
if 'cpt_map' in [str(t) for t in ds.tags()]:
    ds.remove('cpt_map')
cpt = ds.create('cpt_map', 'CutPoint3D')
cpt.set('data', 'dset_opt')
cpt.set('pointx', fmt(X.ravel()))
cpt.set('pointy', fmt(Y))
cpt.set('pointz', fmt(Z.ravel()))

num = java.result().numerical()
if 'pev_map' in [str(t) for t in num.tags()]:
    num.remove('pev_map')
ev = num.create('pev_map', 'EvalPoint')
ev.set('data', 'cpt_map')
ev.set('expr', ['ewfd.Qh'])
raw = np.array(ev.getReal(), dtype=float).ravel()
print(f'evaluated {raw.size} points '
      f'({np.count_nonzero(np.isnan(raw))} outside the geometry -> NaN)')

Q = raw.reshape(X.shape)                 # W/m^3
out = os.path.join(C.RESULTS,
                   f'f3d_{C.ABSORBER}_{C.VARIANT}_Qmap_{int(lam)}nm.npz')
os.makedirs(C.RESULTS, exist_ok=True)
np.savez_compressed(out, x_nm=xs, z_nm=zs, Qh=Q, lam_nm=lam,
                    variant=C.VARIANT, layers=np.array(
                        [L['h_au'], L['h_htl'], L['h_abs'], L['h_etl'],
                         L['h_fto']]))
print(f'-> {out}')
finite = Q[np.isfinite(Q)]
if finite.size:
    print(f'Qh range {finite.min():.3g} to {finite.max():.3g} W/m^3')
print('STAGE 12 DONE', flush=True)
