"""Convert a tabulated dielectric function (E, eps1, eps2) into an n,k CSV.

Written for the Ghimire et al. AIP Advances 7, 075108 (2017) supplementary
tables, which give eps1/eps2 versus photon energy in DESCENDING eV — the
replacement for the spliced FASnI3 digitization. It is generic enough for any
(E, eps1, eps2) table.

    n = sqrt( (|eps| + eps1) / 2 )      k = sqrt( (|eps| - eps1) / 2 )
    lambda_um = 1.23984193 / E_eV

Output matches the sibling optical-constant files: one '%' header line
carrying the full citation and provenance, then `wavelength_um,n,k` ascending
in wavelength.

WHY THIS EXISTS: the current FASnI3 file is spliced from two digitized figures
at 1.70 eV and k jumps 5.8x across that join, which suppresses absorption over
a band carrying ~10 mA/cm2. The paper's own SI has the tabulated numbers; this
converts them once they are downloaded.

Run:
  python3 full3d/build/f3d_convert_eps_to_nk.py <input.txt> <out.csv> \
      --cite "..." [--skiprows N] [--ecol 0 --e1col 1 --e2col 2]
      [--lam-min 0.30] [--lam-max 1.30]
"""
import sys, os, argparse
import numpy as np

HC_EV_UM = 1.23984193          # h*c in eV*um


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('infile')
    ap.add_argument('outfile')
    ap.add_argument('--cite', required=True,
                    help='full citation + provenance for the % header line')
    ap.add_argument('--skiprows', type=int, default=2,
                    help='header lines to skip (Ghimire SI tables use 2)')
    ap.add_argument('--ecol', type=int, default=0)
    ap.add_argument('--e1col', type=int, default=1)
    ap.add_argument('--e2col', type=int, default=2)
    ap.add_argument('--lam-min', type=float, default=None, help='um')
    ap.add_argument('--lam-max', type=float, default=None, help='um')
    a = ap.parse_args()

    d = np.genfromtxt(a.infile, skip_header=a.skiprows, comments='#')
    d = d[~np.isnan(d).any(axis=1)]
    E, e1, e2 = d[:, a.ecol], d[:, a.e1col], d[:, a.e2col]

    mod = np.hypot(e1, e2)
    n = np.sqrt(np.maximum((mod + e1) / 2.0, 0.0))
    k = np.sqrt(np.maximum((mod - e1) / 2.0, 0.0))
    lam = HC_EV_UM / E

    o = np.argsort(lam)                      # ascending wavelength
    lam, n, k = lam[o], n[o], k[o]
    if a.lam_min is not None:
        m = lam >= a.lam_min; lam, n, k = lam[m], n[m], k[m]
    if a.lam_max is not None:
        m = lam <= a.lam_max; lam, n, k = lam[m], n[m], k[m]

    os.makedirs(os.path.dirname(os.path.abspath(a.outfile)), exist_ok=True)
    with open(a.outfile, 'w') as fh:
        fh.write(f'%lambda_um,n,k  {a.cite}\n')
        for L, nn, kk in zip(lam, n, k):
            fh.write(f'{L:.6f},{nn:.5f},{kk:.5f}\n')

    print(f'wrote {len(lam)} rows -> {a.outfile}')
    print(f'  E     {E.min():.3f}-{E.max():.3f} eV')
    print(f'  lambda {lam.min()*1000:.0f}-{lam.max()*1000:.0f} nm')
    for t in (0.4, 0.55, 0.7, 0.73, 0.8, 0.879):
        if lam.min() <= t <= lam.max():
            i = int(np.argmin(abs(lam - t)))
            print(f'  {lam[i]*1000:6.1f} nm  n={n[i]:.4f}  k={k[i]:.5f}')

    # The whole point: verify the 1.70 eV splice discontinuity is GONE.
    rel = np.abs(np.diff(k)) / np.maximum(k[:-1], 1e-9)
    bad = [(lam[i]*1000, lam[i+1]*1000, k[i], k[i+1])
           for i in range(len(rel)) if rel[i] > 0.4 and k[i] > 0.03]
    print()
    if bad:
        print('  !! single-step drops in k >40 % while still absorbing:')
        for lo, hi, k0, k1 in bad:
            print(f'     {lo:.0f}->{hi:.0f} nm : {k0:.4f} -> {k1:.4f}')
        print('     (the old file failed exactly this test at 725->730 nm)')
    else:
        print('  no >40 % single-step drops in k -- the splice defect is gone.')


if __name__ == '__main__':
    main()
