"""FULL-3D stage 02 -- meshability probe + visual confirmation.

Run BEFORE investing in materials/physics. Two risks are checked here:

 1. SHARP APEX. TEXTURE['r_top']=0 makes a geometric singularity. Free-tet
    meshers generate sliver elements there, which wreck vector-Helmholtz
    conditioning. If quality is bad, truncate the cone slightly (r_top
    10-25 nm) -- physically negligible, numerically a big improvement.
 2. ELEMENT COUNT SCALING. The parent planar study used a mapped+swept mesh
    (~3875 elements) which is impossible on a textured geometry. This
    measures what free-tet actually costs, so the 24-core run can be sized.

Exports a mesh image for eyeball confirmation that the texture is real and
sitting where it should.

Run:  python3 full3d/build/f3d_02_mesh_probe.py [hmax_tex_nm] [hmax_bulk_nm]
"""
import sys, os, time, jpype
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
import mph

hmax_tex = float(sys.argv[1]) if len(sys.argv) > 1 else C.MESH['hmax_tex']
hmax_bulk = float(sys.argv[2]) if len(sys.argv) > 2 else C.MESH['hmax_bulk']
C.banner()
print(f'probe: hmax_tex={hmax_tex} nm  hmax_bulk={hmax_bulk} nm')

client = mph.start(cores=C.CORES)
model = client.load(C.MODEL_PATH)
java = model.java
comp = java.component('comp1')

# ------------------------------------------------------------------ mesh
meshes = comp.mesh()
if 'mesh1' in [str(t) for t in meshes.tags()]:
    meshes.remove('mesh1')
mesh = meshes.create('mesh1', 'geom1')

# global (bulk) size. NB COMSOL auto-creates a default 'size' feature with
# every new mesh, so fetch it rather than create it.
sz = mesh.feature('size')
sz.set('custom', 'on')
sz.set('hmax', hmax_bulk)
sz.set('hmin', C.MESH['hmin'])

# finer size restricted to the texture + the air/FTO region around it,
# so the flat bulk below stays cheap
szt = mesh.create('size_tex', 'Size')
szt.selection().geom('geom1', jpype.JInt(3))
szt.selection().named('sel_cone')
szt.set('custom', 'on')
szt.set('hmax', hmax_tex)
szt.set('hmin', C.MESH['hmin'])

ftet = mesh.create('ftet1', 'FreeTet')

t0 = time.time()
mesh.run()
dt = time.time() - t0
nelem = int(mesh.getNumElem())
print(f'\nMESH OK: {nelem} elements in {dt:.1f} s')

# ------------------------------------------------------- element quality
try:
    qmin = float(mesh.getMinQuality())
    print(f'min element quality = {qmin:.4f}   '
          f'({"OK" if qmin > 0.05 else "POOR -> truncate the cone apex"})')
except Exception as e:
    print('quality query failed:', str(e)[:80])

# rough DOF estimate for 2nd-order vector (edge) elements in 3D:
# ~ 20 DOF per tet is a reasonable working number for quadratic curl elements
print(f'rough DOF estimate  ~ {nelem*20/1e6:.2f} M  '
      f'(direct solve needs roughly 1-3 GB per M DOF -> watch RAM)')

# ----------------------------------------------------------- mesh image
try:
    res = java.result()
    if 'pg_mesh' in [str(t) for t in res.tags()]:
        res.remove('pg_mesh')
    pg = res.create('pg_mesh', 'PlotGroup3D')
    pg.set('data', 'none')
    mp = pg.create('mesh1', 'Mesh')
    mp.set('meshdomain', 'volume')
    img = os.path.join(C.LOGS, 'f3d_mesh_probe.png')
    pg.run()
    ex = res.export().create('img1', 'Image3D')
    ex.set('plotgroup', 'pg_mesh')
    ex.set('filename', img)
    ex.set('imagetype', 'png')
    ex.set('width', '1400'); ex.set('height', '1100')
    # NB 'background' rejects 'white' here; 'color'/'currentcolor' are the
    # accepted values in this COMSOL build. Left unset -> viewer default.
    ex.run()
    print(f'mesh image -> {img}')
except Exception as e:
    print('image export failed (non-fatal):', str(e)[:160])

print('\nSTAGE 02 PROBE DONE', flush=True)
