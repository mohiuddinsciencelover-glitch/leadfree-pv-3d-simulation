"""Central configuration for the FULL-3D (textured) study.

ONE file controls dry-run-vs-production. Moving to the 24-core machine =
change PROFILE (or set F3D_PROFILE=production in the environment).
Nothing else in the pipeline hard-codes core counts, mesh density, or
wavelength grids.

Why this study exists
---------------------
The planar study (parent folder) is laterally uniform, so its 3D solve is
mathematically degenerate with 1D -- the "3D" claim is cosmetic. Adding a
2D-periodic surface texture makes the full-wave 3D solve physically
necessary (diffraction into oblique/guided orders cannot be captured in
1D) AND raises J_ph, which is the fix for the FASnI3 "intrinsic ceiling
below experiment" problem (11.64% ceiling vs 14.51% certified device).

Design decision (deliberate): TEXTURE THE OPTICS, PLANARIZE THE TRANSPORT.
The texture lives at the air/FTO front surface only; every electrical
junction below it stays flat. This mirrors real textured-TCO superstrates
(e.g. Asahi U-type) and avoids re-opening the drift-diffusion convergence
work, which took days to stabilise and which branch-switches on curved
heterojunctions (see archive/abandoned_interface_recombination_attempt_*).
"""
import os

# ---------------------------------------------------------------- profile
PROFILE = os.environ.get('F3D_PROFILE', 'dryrun')       # 'dryrun' | 'production'
assert PROFILE in ('dryrun', 'production')

# ---------------------------------------------------------------- machine
# NOTE the dry-run box is RAM-limited, not core-limited: 7 GB total / ~3 GB
# free. 3D vector-Helmholtz with a free-tet mesh is memory-hungry, so the
# dryrun profile is tuned to stay solvable there, NOT to be accurate.
# Dry runs exist to prove the pipeline runs end-to-end and to measure cost.
MACHINE = {
    'dryrun':     dict(cores=3,  label='4-core/7GB dev box'),
    'production': dict(cores=96, label='96-core/251GB EPYC 9754 server'),
}[PROFILE]
# F3D_CORES overrides the per-COMSOL-process core count. In the parallel
# sweep this is cores PER WORKER, not the machine total -- see PARALLEL below.
CORES = int(os.environ.get('F3D_CORES', MACHINE['cores']))

# ------------------------------------------------------------- parallelism
# A wavelength sweep is embarrassingly parallel and COMSOL's shared-memory
# scaling on a single 3D vector-Helmholtz solve saturates far below 96 cores.
# So the machine is used as N_WORKERS independent COMSOL processes, each on
# CORES_PER_WORKER cores, each owning a disjoint slice of the wavelength grid.
# Wall-clock then scales with the number of workers, not with intra-solve
# speedup, which is where the real gain is.
N_WORKERS = int(os.environ.get('F3D_WORKERS', 8))
CORES_PER_WORKER = int(os.environ.get('F3D_CORES_PER_WORKER', 10))

# ------------------------------------------------------------- absorber
# Start with FASnI3: largest optical headroom (J_ph 18.27 vs >30 mA/cm2
# allowed at Eg=1.41 eV) and the material whose planar "ceiling" embarrasses
# the paper. Texture gains should be biggest and most meaningful here.
ABSORBER = os.environ.get('F3D_ABSORBER', 'FASnI3')

# ------------------------------------------------------------- geometry
# Layer thicknesses identical to the planar study so planar-vs-textured is a
# controlled comparison (nm; z=0 at the bottom of the Au back contact).
LAYERS = dict(h_au=45.0, h_htl=200.0, h_abs=300.0, h_etl=50.0, h_fto=600.0)
# h_au is the only thickness that differs from the planar study's 80 nm, and
# it is an OPTICAL truncation, not a change to the device. Au's skin depth
# across 300-900 nm is 12-17 nm, so 45 nm is more than three skin depths and
# the back face is PEC: the field reaching the truncation plane is below 1e-3
# in power, and what returns from it below 1e-6. Optically 45 nm of
# PEC-backed Au is indistinguishable from 80 nm or from semi-infinite Au,
# while free tets in the metal -- which must be refined to the skin depth in
# z and therefore also in x and y -- were the single largest item in the
# element budget. The planar reference uses the identical value, so the
# comparison stays controlled. The transport model is untouched: this study
# textures the optics and planarises the transport.

# Lateral cell = texture pitch (periodic BCs make one feature per cell an
# infinite square array). 350 nm matches the planar cell, and sits in the
# diffractive regime across the visible.
PITCH = 350.0

# Texture (front surface, protruding from FTO into air).
# 'cone' is the most parametric primitive (r_base -> r_top over h).
# r_top = 0 gives a sharp nanocone; r_top > 0 gives a truncated cone.
TEXTURE = dict(
    shape='cone',
    h=250.0,          # texture height
    r_base=165.0,     # base radius (330 nm dia < 350 pitch -> small flat gap)
    r_top=0.0,        # 0 = sharp apex
)

# F3D_TEXTURE=off builds the PLANAR REFERENCE: the identical stack, materials,
# mesh rule, boundary conditions and solver, with the cone simply absent.
# This is what makes "the texture gains X" a controlled statement. Comparing
# instead against the parent planar study would confound the texture with a
# different mesh strategy (swept vs free tet) and a different boundary
# condition (scattering vs periodic port), so the two runs live here, side by
# side, differing in one thing.
TEXTURED = os.environ.get('F3D_TEXTURE', 'on').lower() not in ('off', '0',
                                                               'false')
VARIANT = 'textured' if TEXTURED else 'planar'
# Air clearance above the tallest texture point, so the PML begins in
# uniform air well away from the texture near-field.
AIR_CLEARANCE = 300.0

# Upper air block, between the flux plane and the terminating boundary. The
# name is historical: stage 04 established that the periodic-port and
# scattered-field formulations both fail here, and the PML coordinate system
# was removed with them, so this block is simply more air (n = 1). It was
# 500 nm, sized for a PML that no longer exists; that made ~20 % of the
# domain height empty space carrying mesh for no physics. The only real
# requirement is separation between the flux plane and the boundary
# condition, and the worst-case evanescent order decays with a ~60 nm length,
# so 150 nm is several decay lengths of margin.
PML_THICKNESS = 150.0

# --------------------------------------------------------------- optics
# hmax in a material = lambda / (n * PPW). PPW = points per wavelength.
# Production PPW=8 is the usual accuracy floor for 2nd-order vector
# elements; dryrun PPW=3 is deliberately too coarse to trust -- it exists
# only to make the solve fit in 3 GB.
# hmax_cap bounds the near-lossless air/PML region, where refining past the
# wave scale buys nothing; hmax_tex is a GEOMETRIC floor for the cone, which
# has to be resolved as a shape, not just as a wave.
# hmax_tex is a GEOMETRIC floor for the cone: it must resolve the cone as a
# SHAPE, which for a 165 nm base radius means ~40 segments round the
# circumference, i.e. ~25 nm -- not the lambda/8 the wave criterion would ask
# for. hmax_cap bounds the near-lossless air, where refining past the wave
# scale buys nothing. ppw is set from the stage 09 convergence study rather
# than assumed.
MESH = {
    'dryrun':     dict(ppw=5.0, hmax_tex=22.0, hmax_bulk=48.0, hmax_cap=48.0,
                       hmin=5.0,  skin_floor=16.0),
    'production': dict(ppw=5.0, hmax_tex=20.0, hmax_bulk=40.0, hmax_cap=40.0,
                       hmin=2.0,  skin_floor=10.0),
}[PROFILE]
MESH['skin_floor'] = float(os.environ.get('F3D_SKIN_FLOOR',
                                          MESH['skin_floor']))
MESH['ppw'] = float(os.environ.get('F3D_PPW', MESH['ppw']))

# Wavelength grid (nm). Production matches the planar study's 10 nm grid so
# J_ph is directly comparable; dryrun uses a handful of probe points.
_STEP = float(os.environ.get('F3D_LAMBDA_STEP', 10.0))
LAMBDA = {
    'dryrun':     [400.0, 550.0, 700.0, 850.0],
    # 300-900 nm. 10 nm matches the planar study, so J_ph is directly
    # comparable. The step is settable because the thin-film fringe spacing
    # here is broad (lambda^2/2nd is ~215 nm in the FTO and ~290 nm in the
    # absorber), so 20 nm still samples the spectrum well above Nyquist and
    # halves the cost if the converged mesh turns out expensive.
    'production': [300.0 + _STEP*i
                   for i in range(int(round(600.0/_STEP)) + 1)],
}[PROFILE]

# ----------------------------------------------------------- mesh bands
# Element size scales as lambda, so element COUNT scales as lambda^-3. One
# mesh sized at the blue end would make every red wavelength pay for
# resolution it cannot use -- and the red end is where most of the
# photocurrent is. Meshing per band instead makes the 600-900 nm half of the
# grid roughly 8x cheaper than the 300 nm mesh, for identical accuracy in
# points-per-wavelength terms, which is the criterion that actually matters.
#
# Each band is meshed at its SHORTEST wavelength, so it is conservative
# everywhere inside the band. The cost is a possible discontinuity at band
# edges, which is why BAND_OVERLAP_CHECK exists: those wavelengths get solved
# on the neighbouring finer mesh too, turning the seam into a measured number
# instead of an assumption.
BANDS = [(300.0, 390.0), (400.0, 590.0), (600.0, 900.0)]
BAND_OVERLAP_CHECK = [400.0, 600.0]      # first lambda of bands 1 and 2


def band_of(lam):
    """Index of the mesh band that owns wavelength `lam` [nm]."""
    for i, (lo, hi) in enumerate(BANDS):
        if lo - 1e-9 <= lam <= hi + 1e-9:
            return i
    raise ValueError(f'wavelength {lam} nm falls outside every mesh band')

# Diffraction orders for the periodic port. A textured surface scatters into
# oblique orders; a plain Scattering BC would spuriously reflect them, which
# is the single biggest correctness upgrade over the planar model.
# COMSOL can auto-generate orders; this caps how many are requested.
MAX_DIFFRACTION_ORDER = 2

# --------------------------------------------------------------- solver
# 'i1' is the iterative sub-feature of COMSOL's auto-generated sequence
# (GMRES + geometric multigrid, SOR-vector smoothing); 'd1' is MUMPS direct.
# Direct is unusable at this mesh size -- see f3d_06_prepare_mesh.py -- but
# is kept selectable because it is the reference a small case can be checked
# against.
SOLVER = dict(linsolver=os.environ.get('F3D_LINSOLVER', 'i1'),
              maxlinit=1000, rhob=400)

# ---------------------------------------------------------------- paths
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                    # parent (planar) project
MODELS = os.path.join(HERE, 'models')
RESULTS = os.path.join(HERE, 'results')
LOGS = os.path.join(HERE, 'logs')

# Optical constants are REUSED from the planar project (not duplicated), EXCEPT
# where the parent file is defective.
#
# FASnI3 now uses the TABULATED dielectric function from the supplementary
# material of the same paper (Ghimire et al., AIP Adv 7, 075108 (2017)), not
# the figure digitization. The parent file was spliced at 1.70 eV from two
# pixel-traced figures and k jumped 5.8x across the join (0.4263 -> 0.0792 at
# 725 -> 730 nm), suppressing absorption over a band carrying ~10 mA/cm2. The
# SI table settles it: BOTH digitized segments were wrong by roughly 2x, in
# OPPOSITE directions -- too absorbing above the splice, not absorbing enough
# below it. The tabulated data is a point-by-point numerical inversion of the
# measured ellipsometric spectra, so it is measurement, not a fit.
#
# To fall back to the parent digitization for comparison:
#   F3D_ABSORBER_NK=../data/optical_constants/FASnI3_nk_Ghimire2017.csv
# BaZrS3 now uses the MEASURED dielectric function: Tauc-Lorentz parameters
# fitted to spectroscopic ellipsometry (Nishigaki et al., Solar RRL 4, 1900555
# (2020), SI Table S2), evaluated analytically in
# build/f3d_bazrs3_tauc_lorentz.py. The parent file, BaZrS3_nk_KK.csv, is a
# Kramers-Kronig transform of DFT/BSE-COMPUTED eps2 (its own header says so)
# and hard-zeroes k at 690 nm, inside its own absorption range. Measurement
# beats calculation. CONSEQUENCE: the measured data's own band gap is 1.94 eV
# (edge 639 nm), not the manuscript's assumed 1.75 eV -- the transport model's
# Eg, band alignments and VRS-derived B_rad must be reconciled before any
# BaZrS3 DEVICE number is quoted against these optics.
NK = {
    'FASnI3':     os.path.join(HERE, 'data/FASnI3_nk_Ghimire2017_SI.csv'),
    'BaZrS3':     os.path.join(HERE, 'data/BaZrS3_nk_Nishigaki2020.csv'),
    'Cs2AgBiBr6': os.path.join(ROOT, 'data/optical_constants/Cs2AgBiBr6_nk_Eddekkar2024.csv'),
    'Cu2AgBiI6':  os.path.join(ROOT, 'data/optical_constants/Cu2AgBiI6_nk_Kamppinen2026.csv'),
}
# Per-absorber override, e.g. to reproduce a run against the old digitization.
if os.environ.get('F3D_ABSORBER_NK'):
    NK[ABSORBER] = os.path.abspath(
        os.path.join(HERE, os.environ['F3D_ABSORBER_NK']))

AU_NK = os.path.join(ROOT, 'data/optical_constants/Au_McPeak2015_nk.csv')
AM15G = os.path.join(ROOT, 'data/reference_spectra/AM15G_ASTM_G173_global.csv')

# FTO optics: REAL DISPERSION as of 2026-07-31, replacing the flat n=1.9,
# k=0.02 placeholder the planar study disclosed as a limitation. A front
# texture geometrically amplifies front-surface parasitic absorption, so
# fabricated FTO data would have been the dominant error source here -- this
# was a hard blocker on publishable numbers.
#
# Source: K. von Rottkay & M. Rubin, "Optical Indices of Pyrolytic Tin-Oxide
# Glass", MRS Proc. 426, 449 (1996), doi:10.1557/PROC-426-449 (= LBNL-38586).
# Commercial pyrolytic-CVD SnO2:F on Libbey-Owens-Ford TEC15, by variable-
# angle spectroscopic ellipsometry, fitted to a Drude-Lorentz model. The CSV
# is an exact analytic evaluation of that published model (its own figures
# are plots of the same model), not a digitization -- see the CSV header.
#
# The placeholder was wrong in BOTH directions, which a flat k always is:
# ~2x too absorbing at 400-600 nm (real k ~ 0.010), but UNDER-absorbing
# beyond ~710 nm where free-carrier absorption takes k past 0.02 and rising
# (0.041 at 900 nm). The near-IR end is exactly where FASnI3 is weakest and
# parasitic TCO loss competes hardest for photons.
FTO_NK_CSV = os.environ.get(
    'F3D_FTO_NK', os.path.join(HERE, 'data/FTO_nk_vonRottkay1996.csv'))
FTO_IS_PLACEHOLDER = not os.path.exists(FTO_NK_CSV)
FTO_PLACEHOLDER = dict(n=1.9, k=0.02)     # fallback only, if the CSV is absent

SPIRO = dict(n=1.75, k=0.0)   # still a placeholder, but back-side -> low stakes

# TiO2 ETL: Devore 1951 Sellmeier, k = 0, as the planar study used. Its pole
# sits at 283 nm, so evaluating it at the 300 nm end of the grid returns
# n = 5.58 -- roughly double any measured value for anatase, and an
# extrapolation well outside the fit's validity. It is therefore clamped at
# TIO2_LAMBDA_MIN, giving n = 3.00 below that, which is both physically
# sane and consistent with the 'const' extrapolation COMSOL already applies
# to every tabulated material here. Applied identically to the textured and
# planar-reference runs, so the comparison stays controlled.
TIO2_LAMBDA_MIN = 400.0       # nm

# ------------------------------------------------- transport hand-off
# The parent drift-diffusion model keeps the FULL 80 nm Au contact, so its
# absorber sits at z = 280-580 nm while this optical model's -- with Au
# truncated to 45 nm -- sits at 245-545 nm. Its UDGeneration feature evaluates
# an interpolation function as Gz_fn(z) against ITS OWN coordinate, so a G(z)
# table exported in this model's frame would be shifted 35 nm and would land
# partly outside the absorber. Stage 14 emits a second, offset table for that
# consumer; this is the only place the offset is defined.
TRANSPORT_H_AU = 80.0         # nm, the parent model's Au thickness
Z_OFFSET_TO_TRANSPORT = TRANSPORT_H_AU - LAYERS['h_au']    # nm, +35

MODEL_PATH = os.path.join(MODELS, f'f3d_{ABSORBER}_{VARIANT}.mph')
SHARDS = os.path.join(RESULTS, f'shards_{VARIANT}')
# The textured run keeps the unsuffixed result name; the planar reference is
# suffixed, which is what f3d_11_figures.py looks for.
RESULT_CSV = os.path.join(
    RESULTS, f'f3d_{ABSORBER}_absorptance_{PROFILE}'
             f'{"" if TEXTURED else "_planar"}.csv')


def ready_path(band):
    """Solve-ready model (mesh + study baked in) for one mesh band.

    Mesh and study are baked in by stage 06; sweep workers load it read-only.
    """
    return os.path.join(
        MODELS, f'f3d_{ABSORBER}_{VARIANT}_{PROFILE}_b{band}_ready.mph')


def banner():
    """Print the active configuration so every log records what it ran."""
    print('=' * 68)
    print(f'  FULL-3D STUDY [{VARIANT.upper()}]   profile={PROFILE}   '
          f'({MACHINE["label"]})')
    print(f'  absorber={ABSORBER}   cores={CORES}')
    if TEXTURED:
        print(f'  pitch={PITCH:.0f}nm  texture={TEXTURE["shape"]} '
              f'h={TEXTURE["h"]:.0f} r_base={TEXTURE["r_base"]:.0f}')
    else:
        print(f'  pitch={PITCH:.0f}nm  NO TEXTURE (planar reference: same '
              f'stack, mesh rule, BCs and solver)')
    print(f'  mesh ppw={MESH["ppw"]}  hmax_tex={MESH["hmax_tex"]}nm   '
          f'lambda pts={len(LAMBDA)}')
    if PROFILE == 'dryrun':
        print('  ** DRY RUN -- mesh is deliberately too coarse to trust. **')
        print('  ** Purpose: prove the pipeline runs + measure cost.      **')
    if FTO_IS_PLACEHOLDER:
        print('  !! FTO n,k IS A PLACEHOLDER (flat k=0.02).               !!')
        print('  !! Front texture amplifies this -> replace before        !!')
        print('  !! any production run is used in the manuscript.         !!')
    else:
        print(f'  FTO n,k: {os.path.basename(FTO_NK_CSV)} (real dispersion)')
    print(f'  TiO2 Sellmeier clamped below {TIO2_LAMBDA_MIN:.0f} nm')
    print('=' * 68, flush=True)
