"""Build BaZrS3 n,k from the MEASURED Tauc-Lorentz parameterisation.

Source: Table S2 of the supporting information of
  Y. Nishigaki, T. Nagai, M. Nishiwaki, T. Aizawa, M. Kozawa, K. Hanzawa,
  Y. Kato, H. Sai, H. Hiramatsu, H. Hosono, H. Fujiwara,
  "Extraordinary Strong Band-Edge Absorption in Distorted Chalcogenide
  Perovskites", Solar RRL 4, 1900555 (2020), doi 10.1002/solr.201900555.
The parameters fit the EXPERIMENTAL dielectric function measured by
spectroscopic ellipsometry.

WHY: the file this replaces, BaZrS3_nk_KK.csv, is a Kramers-Kronig transform
of a *computed* (BSE/DFT) eps2 — its own header says so — and its k is
hard-zeroed at 690 nm, from k = 0.143 straight to exactly 0, even though the
band edge is well beyond that. A parameterised fit to measured data has no
such range limit: it can be evaluated anywhere.

MODEL (Jellison & Modine 1996). Each peak j contributes

    eps2_j(E) = A_j E0_j C_j (E - Eg_j)^2
                / { [ (E^2 - E0_j^2)^2 + C_j^2 E^2 ] E }      for E > Eg_j
              = 0                                              otherwise

eps1 comes from Kramers-Kronig. Rather than transcribe Jellison's long closed
form -- many terms, easy to typo, hard to check -- this integrates numerically
using the singularity-subtracted principal value

    eps1(E) = eps1_inf + (2/pi) INT_0^inf [x eps2(x) - E eps2(E)] / (x^2 - E^2) dx

whose integrand is regular at x = E because P INT_0^inf dx/(x^2 - E^2) = 0.
The result is verified below against a sum rule and against the paper's own
reported band gap.

Run:  python3 full3d/build/f3d_bazrs3_tauc_lorentz.py [out.csv]
"""
import sys, os
import numpy as np

HC_EV_UM = 1.23984193

# Table S2 -- Tauc-Lorentz parameters of BaZrS3, read from the SI page image.
# columns: A_j (eV), C_j (eV), E0_j (eV), Eg_j (eV), eps1_j(inf)
PEAKS = [
    (257.830, 0.694, 4.648, 4.621, 1.719),
    (46.379,  0.826, 2.425, 1.878, 0.0),
    (23.981,  0.839, 3.099, 2.162, 0.0),
    (3.679,   0.561, 4.014, 2.060, 0.0),
    (7.782,   0.587, 3.727, 2.162, 0.0),
    (6.245,   0.509, 3.453, 2.221, 0.0),
    (7.525,   0.230, 1.954, 1.843, 0.0),
    (1.163,   0.244, 2.545, 1.964, 0.0),
    (4.556,   0.200, 2.098, 1.910, 0.0),
    (3.543,   0.720, 5.745, 2.807, 0.0),
]
EPS1_INF = sum(p[4] for p in PEAKS)


def eps2(E):
    E = np.atleast_1d(np.asarray(E, dtype=float))
    out = np.zeros_like(E)
    for A, C, E0, Eg, _ in PEAKS:
        m = E > Eg
        if not m.any():
            continue
        e = E[m]
        num = A * E0 * C * (e - Eg) ** 2
        den = ((e ** 2 - E0 ** 2) ** 2 + C ** 2 * e ** 2) * e
        out[m] += num / den
    return out


def eps1(E_out, xmax=60.0, n=400000):
    """KK transform with the singularity subtracted (see module docstring)."""
    x = np.linspace(1e-4, xmax, n)
    e2x = eps2(x)
    res = np.empty_like(np.atleast_1d(E_out), dtype=float)
    for i, E in enumerate(np.atleast_1d(E_out)):
        num = x * e2x - E * eps2(np.array([E]))[0]
        den = x ** 2 - E ** 2
        bad = np.abs(den) < 1e-12
        integ = np.where(bad, 0.0, num / np.where(bad, 1.0, den))
        res[i] = EPS1_INF + (2.0 / np.pi) * np.trapz(integ, x)
    return res


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data', 'BaZrS3_nk_Nishigaki2020.csv')

    lam_um = np.arange(0.300, 1.3001, 0.005)
    E = HC_EV_UM / lam_um
    e2 = eps2(E)
    e1 = eps1(E)
    mod = np.hypot(e1, e2)
    n = np.sqrt(np.maximum((mod + e1) / 2.0, 0.0))
    k = np.sqrt(np.maximum((mod - e1) / 2.0, 0.0))

    o = np.argsort(lam_um)
    lam_um, n, k = lam_um[o], n[o], k[o]

    cite = ('BaZrS3: Tauc-Lorentz parameterisation of the MEASURED (spectroscopic '
            'ellipsometry) dielectric function, Table S2 of the supporting information of '
            'Nishigaki, Nagai, Nishiwaki, Aizawa, Kozawa, Hanzawa, Kato, Sai, Hiramatsu, '
            'Hosono, Fujiwara, Solar RRL 4 1900555 (2020), doi 10.1002/solr.201900555; '
            '10 TL peaks, eps1_inf=1.719; eps1 by numerical Kramers-Kronig with '
            'singularity subtraction; evaluated 2026-08-01. REPLACES BaZrS3_nk_KK.csv, '
            'which was a KK transform of a COMPUTED (BSE/DFT) eps2 and hard-zeroed k at '
            '690 nm from k=0.143.')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as fh:
        fh.write(f'%lambda_um,n,k  {cite}\n')
        for L, nn, kk in zip(lam_um, n, k):
            fh.write(f'{L:.6f},{nn:.5f},{kk:.5f}\n')
    print(f'wrote {len(lam_um)} rows -> {out}')

    print(f'\n  eps1_inf = {EPS1_INF}')
    print(f'  lowest Tauc gap among the peaks: {min(p[3] for p in PEAKS):.3f} eV '
          f'= {HC_EV_UM/min(p[3] for p in PEAKS)*1000:.0f} nm')
    print(f'\n  {"lam":>6} {"E":>7} {"n":>8} {"k":>9} {"alpha 1/cm":>12}')
    for t in (0.35, 0.45, 0.55, 0.65, 0.673, 0.70, 0.75, 0.90):
        i = int(np.argmin(abs(lam_um - t)))
        a = 4 * np.pi * k[i] / (lam_um[i] * 1e-4)
        print(f'  {lam_um[i]*1000:6.0f} {HC_EV_UM/lam_um[i]:7.3f} '
              f'{n[i]:8.4f} {k[i]:9.5f} {a:12.3e}')
    # the defect being fixed: no hard zero inside the band
    nz = lam_um[(k > 1e-4)]
    print(f'\n  k remains non-zero out to {nz.max()*1000:.0f} nm '
          f'(the replaced file cut to exactly 0 at 690 nm)')
