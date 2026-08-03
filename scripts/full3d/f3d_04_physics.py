"""FULL-3D stage 04 -- ewfd physics: total field + incident plane wave.

WHY NOT A PERIODIC PORT
-----------------------
A periodic port is the textbook choice here and was tried first. In this
COMSOL 6.2 install it fails with a singular matrix -- "1 void equation for
comp1.ewfd.S1x" -- and the failure REPRODUCES IN A TRIVIAL TWO-BLOCK MODEL
with correct Floquet pairs, a reference point, and both 'UserDefined' and
'FromPeriodicPort' Floquet sources. So it is not a geometry or texture
problem. (Notably the parent planar project's build_3d_stage3.py carries a
fallback list of boundary-condition type names with 'Port' tried LAST,
which suggests the same wall was hit there and worked around.)

WHY NOT SCATTERED-FIELD + PML EITHER
------------------------------------
Tried second, and it SOLVES -- but it is physically invalid here. The
scattered-field formulation requires the background to be an exact solution
of the background problem; a vacuum plane wave is not, in a layered stack.
Symptom: 0.3% absorption in a 300 nm FASnI3 layer at 550 nm, i.e. the wave
never properly entered the stack. Recorded because it fails SILENTLY -- it
converges and returns plausible-looking small numbers.

WHAT IS USED
------------
Total-field formulation with an incident plane wave injected by a Scattering
BC, which is valid with layered media and matches the parent planar study.

LIMITATION, disclosed: a first-order absorbing BC is exact only for normally
incident OUTGOING waves. For lambda > pitch (350 nm) the specular order is
the only propagating order in air, so it is exact over most of the 300-900 nm
grid. Below 350 nm the +/-1 orders propagate (59 deg at 300 nm) and are
partially reflected. Quantify that band rather than ignoring it.

Run:  python3 full3d/build/f3d_04_physics.py
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

p.set('f0', 'c_const/lda0', 'frequency from swept free-space wavelength')

# ------------------------------------------------------------------ PML
# NOT USED -- see the note above on formulation. The extra block above the
# air is simply more air (n=1), which is harmless and increases the
# clearance between the texture near-field and the terminating boundary.
cs = comp.coordSystem()
if 'pml1' in [str(t) for t in cs.tags()]:
    cs.remove('pml1')
    print('removed PML coordinate system (total-field formulation)')

# -------------------------------------------------------------- physics
ptags = set(str(t) for t in comp.physics().tags())
if 'ewfd' not in ptags:
    ewfd = comp.physics().create(
        'ewfd', 'ElectromagneticWavesFrequencyDomain', 'geom1')
else:
    ewfd = comp.physics('ewfd')
ewfd.label('EM Waves, Frequency Domain (textured, scattered-field + PML)')

# remove any port/PEC leftovers from the earlier port-based attempt
for stale in ('port_top',):
    if stale in [str(t) for t in ewfd.feature().tags()]:
        ewfd.feature().remove(stale)
        print(f'removed stale feature: {stale}')

# TOTAL-field formulation. The scattered-field option was tried and is
# INVALID here: it requires the background to be an exact solution of the
# background problem, which a vacuum plane wave is not in a layered stack.
# Using it gave 0.3% absorption in a 300 nm FASnI3 layer at 550 nm (should
# be tens of percent) -- the wave never properly entered the stack.
bg = ewfd.prop('BackgroundField')
bg.set('SolveFor', 'fullField')
print('formulation: total field (scattered-field is invalid for a layered stack)')

ftags = set(str(t) for t in ewfd.feature().tags())

# ------------------------------------------------- Floquet periodic pairs
# Normal incidence -> zero in-plane wavevector, so 'UserDefined' with
# kFloquet = 0 is correct and needs no exciting port.
for tag, selname, label in [
        ('per_x', 'sel_bnd_xpair', 'Floquet periodicity (x)'),
        ('per_y', 'sel_bnd_ypair', 'Floquet periodicity (y)')]:
    f = ewfd.create(tag, 'PeriodicCondition', jpype.JInt(2)) \
        if tag not in ftags else ewfd.feature(tag)
    f.label(label)
    f.selection().named(selname)
    f.set('PeriodicType', 'Floquet')
    f.set('Floquet_source', 'UserDefined')
    f.set('kFloquet', ['0', '0', '0'])
    print(f'{tag}: Floquet (k_in-plane = 0) on {selname}')

# ------------------------------- incident plane wave via scattering BC
# Total-field excitation. Valid with layered media, unlike scattered-field.
# LIMITATION (disclosed): a first-order absorbing BC is exact only for
# normally incident outgoing waves. For lambda > pitch (350 nm) the specular
# order is the ONLY propagating order in air, so this is exact across most
# of the 300-900 nm grid. Below 350 nm the +/-1 orders propagate (at 300 nm,
# theta = 59 deg) and the BC reflects a few percent of them spuriously.
# That band carries little AM1.5G weight and FASnI3 absorbs strongly there,
# but it is a known error term to quantify, not to ignore.
sbc_tag = 'sbc_top'
# NB the feature ID is 'Scattering' in this build, not
# 'ScatteringBoundaryCondition'.
sbc = ewfd.create(sbc_tag, 'Scattering', jpype.JInt(2)) \
    if sbc_tag not in ftags else ewfd.feature(sbc_tag)
sbc.label('Scattering BC + incident plane wave (top)')
sbc.selection().named('sel_bnd_top')
# ORDER MATTERS: WaveType must be set before E0i, otherwise E0i is
# rejected as an invalid property value.
sbc.set('WaveType', 'PlaneWave')
sbc.set('IncidentField', 'EField')
# E0i/kdir reject setIndex and plain Python lists in this build; they need
# an explicit Java String[]. WaveType must also be set before E0i.
JS = jpype.JArray(jpype.JString)
sbc.set('E0i', JS(['1', '0', '0']))
sbc.set('kdir', JS(['0', '0', '-1']))
print(f'{sbc_tag}: incident x-polarised plane wave, 1 V/m, direction -z')

# ------------------------------------------------------------------ PEC
pec_tag = 'pec_bottom'
pec = ewfd.create(pec_tag, 'PerfectElectricConductor', jpype.JInt(2)) \
    if pec_tag not in ftags else ewfd.feature(pec_tag)
pec.label('PEC (Au back face)')
pec.selection().named('sel_bnd_bottom')
print(f'{pec_tag}: PEC on sel_bnd_bottom')

model.save(C.MODEL_PATH)
print('\nphysics configured + saved')

print('\n--- ewfd feature list ---')
for t in [str(x) for x in ewfd.feature().tags()]:
    f = ewfd.feature(t)
    try:
        ents = list(f.selection().entities(jpype.JInt(2)))
    except Exception:
        ents = ''
    print(f'  {t:14s} {str(f.label())[:42]:44s} {ents}')
print('\nSTAGE 04 DONE', flush=True)
