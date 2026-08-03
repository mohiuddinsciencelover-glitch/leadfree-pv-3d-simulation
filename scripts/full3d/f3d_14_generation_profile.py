"""FULL-3D stage 14 -- broadband generation profile G(z) for the transport model.

Turns the per-wavelength, laterally averaged absorbed-power profiles the sweep
workers emit into the single AM1.5G-weighted generation profile the existing
drift-diffusion model consumes. This is the hand-off that makes the study a
DEVICE result rather than only an optical one:

    G(z) = sum_lambda  Qh_avg(z, lambda) / E_photon(lambda)
                       * Phi_AM15G(lambda) / (P_inc / A_cell) * dlambda

The workers solve with a 1 V/m incident plane wave, so each wavelength's Qh
carries the *shape* of the absorption profile and its magnitude relative to
that unit excitation. Rescaling by the AM1.5G irradiance in each wavelength
bin and dividing by the photon energy converts W/m^3 into carriers/m^3/s.

The lateral average is what lets a textured 3D optical result drive a
planar-in-z transport model: it conserves absorbed power per unit depth,
which is exactly what sets the generation rate. It does discard lateral
structure -- fine here, because the texture is at the front surface and the
junctions below it are flat by design.

SANITY CHECK: integrating G(z) over the absorber thickness must reproduce the
absorber photocurrent obtained independently from the absorptance spectrum in
stage 10. Those are two different routes through the same data -- a volume
integral of a depth profile versus a spectral integral of layer absorptance --
so agreement is a real check, and it is printed every run.

Run:  python3 full3d/build/f3d_14_generation_profile.py [variant]
"""
import sys, os, csv, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import config as C

Q = 1.602176634e-19
H = 6.62607015e-34
CLIGHT = 2.99792458e8
Z0 = 376.730313668

variant = sys.argv[1] if len(sys.argv) > 1 else C.VARIANT
shards = os.path.join(C.RESULTS, f'shards_{variant}')
# Absorber-specific glob: the shard directory is shared across absorbers, so a
# bare '*_Gz.csv' would silently blend FASnI3 profiles into a BaZrS3 G(z).
files = sorted(glob.glob(os.path.join(
    shards, f'{C.ABSORBER}_{C.PROFILE}_w[0-9][0-9]_Gz.csv')))
if not files:
    raise SystemExit(f'no G(z) shards in {shards}')

rows = []
for f in files:
    with open(f) as fh:
        rows.extend(list(csv.DictReader(fh)))
if not rows:
    raise SystemExit('G(z) shards are empty')

# Drop band-overlap QC points. Those wavelengths are deliberately re-solved on
# a NEIGHBOURING band's mesh to measure the seam, so the shards can hold two
# profiles for the same wavelength. Keying only on wavelength would let the
# non-owning one overwrite the record silently -- the merge in stage 08
# filters the spectrum the same way, and the profiles must match it.
n_all = len(rows)
rows = [r for r in rows if int(r['band']) == C.band_of(float(r['lambda_nm']))]
if len(rows) != n_all:
    print(f'  dropped {n_all - len(rows)} rows from band-overlap check points '
          f'(kept the owning band, as the spectrum merge does)')

lam = np.array([float(r['lambda_nm']) for r in rows])
z = np.array([float(r['z_nm']) for r in rows])
qh = np.array([float(r['Qh_avg_W_m3']) for r in rows])

lams = np.unique(lam)
zs = np.unique(z)
print(f'{variant}: {len(lams)} wavelengths x {len(zs)} depths '
      f'({lams.min():.0f}-{lams.max():.0f} nm, z {zs.min():.1f}-{zs.max():.1f} nm)')

Qh = np.full((len(lams), len(zs)), np.nan)
li = {v: i for i, v in enumerate(lams)}
zi = {v: i for i, v in enumerate(zs)}
for L, Z, V in zip(lam, z, qh):
    Qh[li[L], zi[Z]] = V
missing = int(np.isnan(Qh).sum())
if missing:
    print(f'  {missing} missing (lambda, z) cells -- filling by depth-wise '
          f'interpolation across wavelength')
    for j in range(Qh.shape[1]):
        col = Qh[:, j]
        m = np.isnan(col)
        if m.any() and (~m).any():
            col[m] = np.interp(lams[m], lams[~m], col[~m])

# AM1.5G irradiance INTEGRATED over each wavelength bin [W m^-2], not sampled
# at the bin centre and multiplied by the bin width.
#
# AM1.5G is full of narrow atmospheric absorption lines. Sampling it at the
# 10 nm solve points and scaling by 10 nm therefore misses real structure,
# and it made this stage disagree with stage 10 -- which integrates on the
# spectrum's own dense grid -- by ~10 % for reasons that were pure quadrature
# and nothing to do with the physics. Integrating the dense data over each
# bin makes the two routes consistent AND more accurate, so their remaining
# difference actually measures what the cross-check claims to measure.
d = np.loadtxt(C.AM15G, delimiter=',', comments='#')
lam_d, irr_d = d[:, 0], d[:, 1]

# Bins partition EXACTLY [lam_min, lam_max]; the outer edges are clamped to
# the grid endpoints rather than extended half a bin beyond them. Extending
# them would integrate the spectrum over a wider range than stage 10 does and
# make the cross-check compare two different questions -- on a 5-point grid
# that alone was a +23 % gap. Clamping makes the first and last bins
# half-width, which is exactly the trapezoid convention stage 10 uses.
edges = np.empty(len(lams) + 1)
edges[1:-1] = (lams[1:] + lams[:-1]) / 2.0
edges[0] = lams[0]
edges[-1] = lams[-1]


def band_irradiance(lo, hi):
    """Integral of AM1.5G irradiance over [lo, hi] on the spectrum's own grid."""
    m = (lam_d > lo) & (lam_d < hi)
    xs = np.concatenate(([lo], lam_d[m], [hi]))
    ys = np.concatenate(([np.interp(lo, lam_d, irr_d)], irr_d[m],
                         [np.interp(hi, lam_d, irr_d)]))
    return float(np.trapz(ys, xs))


irr_bin = np.array([band_irradiance(edges[i], edges[i + 1])
                    for i in range(len(lams))])          # W m^-2 per bin

# The solve used |E0| = 1 V/m, i.e. an incident intensity of 1/(2 Z0) W/m^2.
# Scale each wavelength's profile by the ratio of the AM1.5G power in its bin
# to that unit-field intensity.
scale = irr_bin * (2.0 * Z0)                        # per unit-field solve
E_ph = H * CLIGHT / (lams * 1e-9)                   # J

G = np.zeros_like(zs)                               # carriers m^-3 s^-1
for i in range(len(lams)):
    G += Qh[i] * scale[i] / E_ph[i]

out = os.path.join(C.RESULTS, f'f3d_{C.ABSORBER}_{variant}_Gz_AM15G.csv')
with open(out, 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['z_m', 'G_1_per_m3_s'])
    for zz, gg in zip(zs, G):
        w.writerow([f'{zz*1e-9:.6e}', f'{gg:.6e}'])
print(f'-> {out}   (this model frame: absorber at '
      f'{zs.min():.0f}-{zs.max():.0f} nm)')

# Second table in the PARENT transport model's coordinate frame. Its
# UDGeneration evaluates Gz_fn(z) against its own geometry, where the Au
# contact is the full 80 nm rather than the 45 nm this optical model uses --
# so the same numbers must be re-labelled, or the profile lands 35 nm off and
# partly outside the absorber. Same column names and units as the parent's
# existing G(z) files, so it is a drop-in replacement.
out_t = os.path.join(C.RESULTS,
                     f'f3d_{C.ABSORBER}_{variant}_Gz_AM15G_forTransport.csv')
with open(out_t, 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['z_m', 'G_1_per_m3_s'])
    for zz, gg in zip(zs, G):
        w.writerow([f'{(zz + C.Z_OFFSET_TO_TRANSPORT)*1e-9:.6e}',
                    f'{gg:.6e}'])
print(f'-> {out_t}')
print(f'   shifted +{C.Z_OFFSET_TO_TRANSPORT:.0f} nm into the transport frame '
      f'(absorber {zs.min()+C.Z_OFFSET_TO_TRANSPORT:.0f}-'
      f'{zs.max()+C.Z_OFFSET_TO_TRANSPORT:.0f} nm, parent expects 280-580)')

# The sampled depths stop a small pad short of each interface (points landing
# exactly on a material boundary evaluate ambiguously), so the trapezoid over
# them misses a thin slab at each end. Extend the end values to the true
# interfaces rather than silently under-reporting by that fraction -- without
# it the cross-check below carries a ~1 % bias that is bookkeeping, not physics.
z_abs0 = C.LAYERS['h_au'] + C.LAYERS['h_htl']
z_abs1 = z_abs0 + C.LAYERS['h_abs']
J_from_G = (np.trapz(G, zs * 1e-9)
            + G[0] * (zs.min() - z_abs0) * 1e-9
            + G[-1] * (z_abs1 - zs.max()) * 1e-9)
J_from_G = Q * J_from_G / 10.0                      # mA/cm^2
print(f'\n  G(z) range      : {G.min():.3e} to {G.max():.3e} m^-3 s^-1')
# Light enters through the FTO/ETL at the TOP of the stack, so the illuminated
# face of the absorber is the high-z (ETL) side and generation decays towards
# the HTL. Report the decay in that direction, which is how it is read.
print(f'  illuminated face (z={zs.max():.0f} nm, ETL side): {G[-1]:.3e}')
print(f'  back face        (z={zs.min():.0f} nm, HTL side): {G[0]:.3e}')
print(f'  front-to-back decay: {G[-1]/G[0]:.1f}x')
print(f'  J from integral of G(z): {J_from_G:.3f} mA/cm2  '
      f'(100 % collection ceiling)')

spec = os.path.join(C.RESULTS, f'f3d_{C.ABSORBER}_absorptance_{C.PROFILE}'
                               f'{"" if variant == "textured" else "_planar"}.csv')
if os.path.exists(spec):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from f3d_10_photocurrent import load_spectrum, photon_flux, integrate
    s = load_spectrum(spec)
    lam_nm, phi = photon_flux()
    J_from_A = integrate(s['lambda_nm'], s['A_absorber'], lam_nm, phi)
    diff = 100 * (J_from_G - J_from_A) / J_from_A if J_from_A else float('nan')
    print(f'  J from absorptance spectrum: {J_from_A:.3f} mA/cm2')
    print(f'  CROSS-CHECK (two independent routes): {diff:+.2f} %  '
          f'{"OK" if abs(diff) < 5 else "** INVESTIGATE **"}')
    print('    (a depth integral of G(z) vs a spectral integral of layer\n'
          '     absorptance -- they share the solve but nothing else)')
else:
    print(f'  (absorptance spectrum not found at {spec}; cross-check skipped)')
print('\nSTAGE 14 DONE', flush=True)
