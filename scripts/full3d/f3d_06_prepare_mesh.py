"""FULL-3D stage 06 -- build the mesh + study ONCE and save a solve-ready model.

Why this is its own stage
-------------------------
The sweep runs as N independent COMSOL processes. If each built its own
mesh, small mesher differences between processes would show up as jitter in
the absorptance spectrum -- a numerical artefact that looks exactly like
physics. Meshing once and having every worker load the same file removes
that failure mode by construction, and costs one meshing pass instead of N.

Mesh sizing
-----------
Element size is set PER MATERIAL from the wavelength inside that material,
lam_ref/(n_eff*ppw), not from one global hmax. n_eff = |n_complex|, and in
an absorbing material the size is additionally capped at half the skin
depth. That last clamp is what actually resolves the Au contact: at 300 nm
Au has a ~13 nm skin depth, so a global 40 nm mesh would leave the metal
several times too coarse and its parasitic absorption unreliable.

lam_ref is the SHORTEST wavelength in the sweep, so the single mesh is
conservative for every longer wavelength. Element count is therefore set by
the hardest point on the grid, which is the price of one mesh for the whole
sweep.

Run:  python3 full3d/build/f3d_06_prepare_mesh.py [lam_ref_nm]
"""
import sys, os, time, json, jpype
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
import f3d_optics as O
import f3d_mesh as M
import mph

band = int(sys.argv[1]) if len(sys.argv) > 1 else 0
lam_lo, lam_hi = C.BANDS[band]
lam_ref = lam_lo
C.banner()
print(f'mesh band {band}: {lam_lo:.0f}-{lam_hi:.0f} nm, sized at '
      f'{lam_ref:.0f} nm (shortest in band -> conservative throughout)')
print(f'points per wavelength: {C.MESH["ppw"]}\n')

print('per-material element size:')
sizes = O.mesh_sizes(lam_ref, C.MESH['ppw'], C.MESH['hmin'],
                     C.MESH['hmax_cap'], C.MESH['skin_floor'])

client = mph.start(cores=C.CORES)
model = client.load(C.MODEL_PATH)
java = model.java
comp = java.component('comp1')

# ------------------------------------------------------------------ mesh
# Built by f3d_mesh.build so that stage 09's convergence study meshes the
# model exactly the same way -- including the periodic face copy, without
# which the answer is not mesh-convergent at all.
t0 = time.time()
nelem, qmin = M.build(comp, sizes)
dt = time.time() - t0
print(f'\nmesh: {nelem} elements in {dt:.1f} s, min quality {qmin:.4f}')
if qmin < 0.05:
    print('  ** POOR QUALITY -- consider truncating the cone apex **')

# ------------------------------------------------------------------ study
stags = [str(t) for t in java.study().tags()]
if 'std_opt' in stags:
    java.study().remove('std_opt')
std = java.study().create('std_opt')
std.label('Optics: frequency domain')
fr = std.create('freq', 'Frequency')
fr.set('plist', 'f0')
fr.setSolveFor('/physics/ewfd', True)
print('study std_opt created (frequency domain, driven by parameter f0)')

# --------------------------------------------------------------- solver
# COMSOL's auto-generated sequence points the fully-coupled solver at the
# MUMPS DIRECT solver. At this mesh size that is unusable: two concurrent
# solves passed 48 GB and were still climbing, because a direct
# factorisation of a few-million-DOF complex vector-Helmholtz system does
# not fit in any sane memory budget -- and the whole plan here is to run
# many solves at once.
#
# The auto sequence already CONTAINS the right alternative, unused: 'i1',
# GMRES preconditioned by geometric multigrid with SOR-vector smoothing,
# which is the standard recipe for 3D vector Helmholtz. So the fix is to
# point the fully-coupled solver at it rather than to build a solver by
# hand. Memory then scales roughly linearly with DOF instead of with
# fill-in.
sols = java.sol()
for t in [str(x) for x in sols.tags()]:
    sols.remove(t)
sol = sols.create('sol_opt')
sol.study('std_opt')
sol.attach('std_opt')
sol.createAutoSequence('std_opt')
s1 = sol.feature('s1')
s1.feature('fc1').set('linsolver', C.SOLVER['linsolver'])
if C.SOLVER['linsolver'] == 'i1':
    # NB these take Java ints; a bare Python int hits an ambiguous-overload
    # error in JPype and the property is silently left at its default.
    try:
        s1.feature('i1').set('maxlinit', jpype.JInt(C.SOLVER['maxlinit']))
    except Exception as e:
        print('  (maxlinit rejected:', str(e)[:70], ')')
print(f'solver sol_opt: fully-coupled -> {C.SOLVER["linsolver"]} '
      f'({"iterative GMRES + geometric multigrid" if C.SOLVER["linsolver"] == "i1" else "MUMPS direct"})')

# Explicit result dataset. The workers run the solver directly rather than
# study.run(), and only study.run() creates a dataset as a side effect --
# so without this there is nothing for the volume integrals to evaluate on.
# Naming it here also removes the tag-hunting the workers would otherwise do.
dsets = java.result().dataset()
if 'dset_opt' in [str(t) for t in dsets.tags()]:
    dsets.remove('dset_opt')
ds = dsets.create('dset_opt', 'Solution')
ds.set('solution', 'sol_opt')
ds.label('Optics solution')
print('result dataset dset_opt -> sol_opt')

out = C.ready_path(band)
model.save(out)
print(f'\nsolve-ready model -> {out}')

meta = dict(profile=C.PROFILE, variant=C.VARIANT, absorber=C.ABSORBER,
            band=band, band_range=[lam_lo, lam_hi], lam_ref=lam_ref,
            ppw=C.MESH['ppw'], sizes=sizes, n_elem=nelem,
            min_quality=None if qmin != qmin else qmin,
            mesh_seconds=round(dt, 1),
            lambdas=[l for l in C.LAMBDA if lam_lo <= l <= lam_hi])
# The variant belongs in the FILENAME, not just the contents: without it the
# planar run silently overwrote the textured run's mesh provenance. The
# element counts survive in the shard CSVs' n_elem column, but the per-material
# sizes and mesh quality did not.
mp = os.path.join(
    C.RESULTS, f'f3d_{C.ABSORBER}_mesh_{C.VARIANT}_{C.PROFILE}_b{band}.json')
os.makedirs(C.RESULTS, exist_ok=True)
with open(mp, 'w') as fh:
    json.dump(meta, fh, indent=2)
print(f'mesh metadata -> {mp}')
print('\nSTAGE 06 DONE', flush=True)
