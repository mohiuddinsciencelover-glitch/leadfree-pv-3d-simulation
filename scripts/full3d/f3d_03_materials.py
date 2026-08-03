"""FULL-3D stage 03 -- materials + dispersive optical constants.

Assignment is BY NAMED SELECTION (sel_au, sel_htl, ...), never by domain
index. This is what makes the texture safe: the cone is domain 7 and is
picked up automatically by sel_fto = [5,7], so FTO and its texture always
share one material by construction.

Optical constants are REUSED from the parent planar study (same CSVs, same
provenance) so that planar-vs-textured is a controlled optical comparison.
All CSVs are: col1 = wavelength [um], col2 = n, col3 = k.

Run:  python3 full3d/build/f3d_03_materials.py
"""
import sys, os, jpype
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
import mph

C.banner()
client = mph.start(cores=C.CORES)
model = client.load(C.MODEL_PATH)
java = model.java
comp = java.component('comp1')
p = java.param()

# free-space wavelength driver, swept by the study (matches parent project)
p.set('lda0', '550[nm]', 'free-space wavelength (swept by the optics study)')

mats = comp.material()
existing = set(str(t) for t in mats.tags())


def refractive_group(m):
    """A freshly-created 'Common' material has no RefractiveIndex group --
    only 'def'. Create it on demand (idempotent)."""
    if 'RefractiveIndex' not in [str(t) for t in m.propertyGroup().tags()]:
        m.propertyGroup().create('RefractiveIndex', 'Refractive index')
    return m.propertyGroup('RefractiveIndex')


def tabulated(tag, label, selname, csv, prefix):
    """Material with dispersive n,k from a 3-column CSV (um, n, k).

    Two COMSOL API traps handled here:
      * the interpolation function container hangs off the PROPERTY GROUP
        (rin.func()), not off the material object;
      * the callable name is the one declared in 'funcs', so tag and
        function name are kept identical to remove any ambiguity.
    'piecewisecubic' matches the parent planar study exactly, so the
    planar-vs-textured comparison stays controlled.
    """
    m = mats.create(tag, 'Common') if tag not in existing else mats.get(tag)
    m.label(label)
    m.selection().named(selname)
    rin = refractive_group(m)
    fc = rin.func()
    ftags = set(str(t) for t in fc.tags())
    # NB the 'funcs' position index counts FUNCTION columns (after the
    # argument column), not absolute file columns. For a (lambda, n, k) file
    # that is n->'1', k->'2'. Using '2'/'3' makes COMSOL demand a 4th column.
    for suffix, col in (('n', '1'), ('k', '2')):
        fname = f'{prefix}_{suffix}'
        f = fc.create(fname, 'Interpolation') if fname not in ftags else fc.get(fname)
        f.set('source', 'file')
        f.set('filename', csv)
        f.set('nargs', jpype.JInt(1))
        f.set('funcs', [[fname, col]])
        f.set('interp', 'piecewisecubic')
        f.set('extrap', 'const')     # clamp outside the tabulated range
    rin.set('n', [f'{prefix}_n(lda0/1[um])'])
    rin.set('ki', [f'{prefix}_k(lda0/1[um])'])
    return m


def constant(tag, label, selname, n, k):
    """Non-dispersive material (placeholders + air)."""
    m = mats.create(tag, 'Common') if tag not in existing else mats.get(tag)
    m.label(label)
    m.selection().named(selname)
    rin = refractive_group(m)
    rin.set('n', [str(n)])
    rin.set('ki', [str(k)])
    return m


# --- Au back contact: measured n,k (McPeak 2015)
tabulated('mat_au', 'Au back contact [EXP McPeak2015]', 'sel_au', C.AU_NK, 'Au')

# --- absorber: measured/derived n,k, per-material provenance
tabulated('mat_abs', f'{C.ABSORBER} absorber', 'sel_abs',
          C.NK[C.ABSORBER], 'Abs')

# --- TiO2 ETL: Devore 1951 Sellmeier, k = 0 (as parent study), but with the
#     argument CLAMPED at TIO2_LAMBDA_MIN. The Sellmeier pole is at 283 nm,
#     so the unclamped expression returns n = 5.58 at the 300 nm end of the
#     grid -- roughly double any measured anatase value and well outside the
#     fit's validity. The clamp holds n at 3.00 below 400 nm, consistent with
#     the 'const' extrapolation used for every tabulated material here.
#     f3d_optics.tio2_sellmeier() implements the identical clamp for mesh
#     sizing; the two must be kept in step.
m_etl = constant('mat_etl', f'TiO2 ETL [Devore 1951 Sellmeier, clamped '
                            f'<{C.TIO2_LAMBDA_MIN:.0f}nm]', 'sel_etl', 1, 0)
refractive_group(m_etl).set(
    'n', [f'sqrt(5.913+0.2441/((max(lda0,{C.TIO2_LAMBDA_MIN}[nm])/1[um])^2'
          f'-0.0803))'])
refractive_group(m_etl).set('ki', ['0'])

# --- FTO + cone texture: real SnO2:F dispersion (von Rottkay & Rubin 1996,
#     MRS Proc. 426, 449 / LBNL-38586). This replaced the flat n=1.9,
#     k=0.02 placeholder, which was a hard blocker: a front texture
#     geometrically amplifies front-surface parasitic absorption, so
#     fabricated TCO data would have driven the headline result.
if C.FTO_IS_PLACEHOLDER:
    print('!! FTO n,k CSV missing -- falling back to the PLACEHOLDER !!')
    constant('mat_fto', 'FTO + texture [PLACEHOLDER n=1.9 k=0.02]', 'sel_fto',
             C.FTO_PLACEHOLDER['n'], C.FTO_PLACEHOLDER['k'])
else:
    tabulated('mat_fto', 'FTO + texture [EXP vonRottkay1996 SnO2:F TEC15]',
              'sel_fto', C.FTO_NK_CSV, 'FTO')

# --- Spiro HTL: placeholder, back side -> lower stakes
constant('mat_htl', 'Spiro-OMeTAD HTL [PLACEHOLDER]', 'sel_htl',
         C.SPIRO['n'], C.SPIRO['k'])

# --- air superstrate
constant('mat_air', 'Air', 'sel_air', 1, 0)

# --- PML cap: same medium as air; the PML coordinate system (stage 04)
#     supplies the complex stretching, not the material.
constant('mat_pml', 'PML (air-like medium)', 'sel_pml', 1, 0)

model.save(C.MODEL_PATH)
print('materials assigned + saved\n')

# ------------------------------------------------------------ verification
print('--- material -> domain mapping ---')
for tag in ['mat_au', 'mat_htl', 'mat_abs', 'mat_etl', 'mat_fto', 'mat_air',
            'mat_pml']:
    m = mats.get(tag)
    try:
        ents = list(m.selection().entities(jpype.JInt(3)))
    except Exception:
        ents = '(named sel)'
    print(f'  {tag:9s} {str(m.label()):46s} -> {ents}')

# Independent n,k check: read the CSVs in numpy rather than asking COMSOL.
# (Project memory records that model.evaluate() misreports interpolation
# state, so it is deliberately not trusted here.)
import numpy as np
print('\n--- n,k source data spot check (read independently of COMSOL) ---')
_checks = [('Au', C.AU_NK), (C.ABSORBER, C.NK[C.ABSORBER])]
if not C.FTO_IS_PLACEHOLDER:
    _checks.append(('FTO', C.FTO_NK_CSV))
for label, csv in _checks:
    d = np.loadtxt(csv, delimiter=',', comments=('#', '%'), skiprows=1)
    print(f'  {label:10s} {csv.split("/")[-1]:34s} '
          f'lam {d[0,0]*1000:.0f}-{d[-1,0]*1000:.0f}nm, {len(d)} pts')
    for target in (0.400, 0.600, 0.800):
        i = int(np.argmin(abs(d[:, 0] - target)))
        print(f'      lam={d[i,0]*1000:5.0f}nm  n={d[i,1]:.4f}  k={d[i,2]:.4f}')
    if (d[:, 2] < 0).any():
        print('      !! negative k present in source data !!')

model.save(C.MODEL_PATH)
print('\nSTAGE 03 DONE', flush=True)
