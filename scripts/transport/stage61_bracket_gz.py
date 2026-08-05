"""Stage 61 -- bracketing generation profiles for the Cu2AgBiI6 sub-gap tail.

38.2 % of Cu2AgBiI6's photocurrent comes from sub-gap tail absorption that the
transport model collects like band-to-band generation -- an optimistic
treatment that is currently only disclosed. This script builds two restricted
G(z) profiles from the per-wavelength Qh(z, lambda) shards so transport can be
re-solved on each, turning the disclosure into a quantified bracket:

  abovegap    only bins with lambda <= 600 nm (Tauc gap 2.06 eV = 602 nm).
              LOWER bound: tail contributes nothing.
  noartifact  all bins except 750-880 nm -- the segment where alpha sits at a
              flat ~2.7e3 cm^-1 floor before stepping to zero, a construction
              artifact of the optical file rather than a physical Urbach tail.
              The defensible UPPER bound: real tail kept, artifact removed.

The full-collection number already in the paper is the optimistic ceiling of
the bracket; `abovegap` is its floor.

GATE. The same weighting applied to ALL bins must first reproduce the
existing stage-14 profile (which was built from these same shards); only then
are the restricted variants emitted. Weighting follows stage-14 conventions
exactly: irradiance integrated per bin, outer edges clamped, scale =
irr_bin * 2 Z0, G = sum Qh / E_ph.

Run:  python3 build_scripts/stage61_bracket_gz.py
"""
import sys, os, csv, glob
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'full3d'))
os.environ['F3D_ABSORBER'] = 'Cu2AgBiI6'
os.environ['F3D_PROFILE'] = 'production'
os.environ['F3D_TEXTURE'] = 'off'
import config as C

Q = 1.602176634e-19
H = 6.62607015e-34
C0 = 2.99792458e8
Z0 = 376.730313668
A = 'Cu2AgBiI6'
Z_ABS0 = C.LAYERS['h_au'] + C.LAYERS['h_htl']      # 245 nm
Z_ABS1 = Z_ABS0 + C.LAYERS['h_abs']                # 545 nm


def band_of(l):
    return 0 if l <= 390 else (1 if l <= 590 else 2)


def load_shards():
    rows = []
    for f in glob.glob(os.path.join(
            ROOT, 'full3d/results/shards_planar',
            f'{A}_production_w[0-9][0-9]_Gz.csv')):
        rows += list(csv.DictReader(open(f)))
    rows = [r for r in rows if int(r['band']) == band_of(float(r['lambda_nm']))]
    lam = np.array([float(r['lambda_nm']) for r in rows])
    z = np.array([float(r['z_nm']) for r in rows])
    q = np.array([float(r['Qh_avg_W_m3']) for r in rows])
    L, Zs = np.unique(lam), np.unique(z)
    M = np.full((len(L), len(Zs)), np.nan)
    li = {v: i for i, v in enumerate(L)}
    zi = {v: i for i, v in enumerate(Zs)}
    for a, b, c in zip(lam, z, q):
        M[li[a], zi[b]] = c
    assert not np.isnan(M).any(), 'missing (lambda, z) cells'
    return L, Zs, M


def band_irr(lams):
    d = np.loadtxt(os.path.join(
        ROOT, 'data/reference_spectra/AM15G_ASTM_G173_global.csv'),
        delimiter=',', comments='#')
    ld, irr = d[:, 0], d[:, 1]
    edges = np.empty(len(lams) + 1)
    edges[1:-1] = (lams[1:] + lams[:-1]) / 2.0
    edges[0] = lams[0]; edges[-1] = lams[-1]
    out = []
    for i in range(len(lams)):
        lo, hi = edges[i], edges[i + 1]
        m = (ld > lo) & (ld < hi)
        xs = np.concatenate(([lo], ld[m], [hi]))
        ys = np.concatenate(([np.interp(lo, ld, irr)], irr[m],
                             [np.interp(hi, ld, irr)]))
        out.append(float(np.trapz(ys, xs)))
    return np.array(out)


def profile(L, Zs, M, keep):
    irr = band_irr(L)
    Eph = H * C0 / (L * 1e-9)
    G = np.zeros_like(Zs)
    for i in range(len(L)):
        if keep(L[i]):
            G += M[i] * irr[i] * 2.0 * Z0 / Eph[i]
    return G


def jofG(Zs, G):
    return Q * (np.trapz(G, Zs * 1e-9)
                + G[0] * (Zs.min() - Z_ABS0) * 1e-9
                + G[-1] * (Z_ABS1 - Zs.max()) * 1e-9) / 10.0


def write(Zs, G, name):
    out = os.path.join(ROOT, 'full3d/results',
                       f'f3d_{A}_planar_Gz_AM15G_{name}_forTransport.csv')
    with open(out, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['z_m', 'G_1_per_m3_s'])
        for zz, gg in zip(Zs, G):
            w.writerow([f'{(zz + C.Z_OFFSET_TO_TRANSPORT)*1e-9:.6e}',
                        f'{gg:.6e}'])
    return out


if __name__ == '__main__':
    L, Zs, M = load_shards()
    print(f'{len(L)} wavelengths x {len(Zs)} depths')

    # ---- gate: full reconstruction must reproduce the stage-14 profile
    G_full = profile(L, Zs, M, lambda l: True)
    ref = np.loadtxt(os.path.join(
        ROOT, 'full3d/results',
        f'f3d_{A}_planar_Gz_AM15G_forTransport.csv'),
        delimiter=',', skiprows=1)
    rel = np.abs(G_full - ref[:, 1]) / ref[:, 1].max()
    print(f'GATE: max |dG|/max(G) vs stage-14 profile = {rel.max():.5f}')
    assert rel.max() < 1e-3, 'reconstruction does not reproduce stage 14'
    print(f'      J(full) = {jofG(Zs, G_full):.3f} mA/cm2 '
          f'(paper value 14.731 raw-trapezoid + edge pad)')

    # ---- variants
    G_ag = profile(L, Zs, M, lambda l: l <= 600.0)
    G_na = profile(L, Zs, M, lambda l: not (750.0 <= l <= 880.0))
    for nm, G in [('abovegap', G_ag), ('noartifact', G_na)]:
        out = write(Zs, G, nm)
        print(f'{nm:11s} J = {jofG(Zs, G):7.3f} mA/cm2  -> '
              f'{os.path.basename(out)}')
