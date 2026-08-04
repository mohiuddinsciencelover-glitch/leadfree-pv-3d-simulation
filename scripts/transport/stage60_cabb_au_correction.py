"""Stage 60 -- correct the Cs2AgBiBr6 optics for the Au-truncation artifact.

THE ARTIFACT. The FEM optical model truncates the Au back contact at 45 nm
backed by a perfect electric conductor, justified by Au's 12-17 nm NIR skin
depth. But Au's damping dips in its 450-570 nm interband window (skin depth
~2x longer), and Cs2AgBiBr6 is the one absorber that is nearly transparent
exactly there -- so light reaches the back contact, and the PEC backing
returns an unphysically strong wave. Measured consequence at 510 nm:
R = 0.469 (FEM / PEC-backed TMM, which agree to 4e-4) versus R = 0.292 for
realistically thick Au. The other three absorbers extinguish this window
before it reaches Au and agree with the thick-Au limit to <=0.35 %.

THE FIX. For a laterally uniform stack at normal incidence the 3-D periodic
problem is mathematically equivalent to the 1-D coherent multilayer problem,
and the TMM implementation here is validated against the FEM to 4e-4 on
identical geometry. This script therefore produces the corrected Cs2AgBiBr6
result in the thick-Au (semi-infinite) limit -- which represents the device's
real 80 nm contact to ~1 % round-trip amplitude -- via three steps, each
checked before the next is trusted:

  1. VALIDATE the spectrum path: PEC-geometry TMM vs the FEM absorptance CSV.
  2. VALIDATE the G(z) path: PEC-geometry TMM G(z) vs the FEM G(z) file,
     including the AM1.5G bin weighting (replicating stage 14's conventions).
  3. Only then emit the corrected (thick-Au) spectrum + G(z) + budget, in the
     same schemas, under an explicit `_au80corr` suffix. Raw FEM outputs are
     never overwritten.

Run:  python3 build_scripts/stage60_cabb_au_correction.py
"""
import sys, os, csv
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'full3d'))
os.environ['F3D_ABSORBER'] = 'Cs2AgBiBr6'
os.environ['F3D_PROFILE'] = 'production'
os.environ['F3D_TEXTURE'] = 'off'
import config as C
import f3d_optics as O

Q = 1.602176634e-19
H = 6.62607015e-34
C0 = 2.99792458e8
Z0 = 376.730313668
EPS0 = 8.8541878128e-12

A = 'Cs2AgBiBr6'
L = C.LAYERS
# optical-frame z of the absorber (z = 0 at the bottom of the Au block)
Z_ABS0 = L['h_au'] + L['h_htl']            # 245
Z_ABS1 = Z_ABS0 + L['h_abs']               # 545


def tmm(lam, pec_backed):
    """Solve the stack; return (R, per-layer A, A_substrate, absorber field).

    Layers top-down: FTO, TiO2, absorber, HTL, then either
      pec_backed=True : Au 45 nm as a finite layer over a PEC, or
      pec_backed=False: semi-infinite Au substrate (thick-contact limit).
    Field amplitudes are for a unit (1 V/m) incident wave.
    """
    mats = [('fto', L['h_fto']), ('etl', L['h_etl']), ('abs', L['h_abs']),
            ('htl', L['h_htl'])]
    ns = [1.0 + 0.0j]
    ds = [None]
    for m, th in mats:
        n, k = O.nk(m, lam)
        ns.append(complex(float(np.asarray(n)), float(np.asarray(k))))
        ds.append(th)
    n, k = O.nk('au', lam)
    n_au = complex(float(np.asarray(n)), float(np.asarray(k)))
    if pec_backed:
        ns.append(n_au); ds.append(L['h_au'])
    else:
        ns.append(n_au); ds.append(None)

    N = len(ns)
    r_eff = [None] * N
    r_eff[N - 1] = (-1.0 + 0.0j) if pec_backed else (0.0 + 0.0j)
    for j in range(N - 2, -1, -1):
        r_jk = (ns[j] - ns[j + 1]) / (ns[j] + ns[j + 1])
        if ds[j + 1] is None:
            r_below = 0.0 + 0.0j
        else:
            beta = 2.0 * np.pi * ns[j + 1] * ds[j + 1] / lam
            r_below = r_eff[j + 1] * np.exp(2j * beta)
        r_eff[j] = (r_jk + r_below) / (1.0 + r_jk * r_below)

    E_plus = [None] * N; E_minus = [None] * N
    E_plus[0] = 1.0 + 0.0j; E_minus[0] = r_eff[0]
    for j in range(1, N):
        t = 2.0 * ns[j - 1] / (ns[j - 1] + ns[j])
        r = (ns[j - 1] - ns[j]) / (ns[j - 1] + ns[j])
        if j - 1 == 0:
            eb, mb = E_plus[0], E_minus[0]
        else:
            beta = 2.0 * np.pi * ns[j - 1] * ds[j - 1] / lam
            eb = E_plus[j - 1] * np.exp(1j * beta)
            mb = E_minus[j - 1] * np.exp(-1j * beta)
        if ds[j] is None:
            rho = 0.0 + 0.0j
        else:
            beta_j = 2.0 * np.pi * ns[j] * ds[j] / lam
            rho = r_eff[j] * np.exp(2j * beta_j)
        E_plus[j] = t * eb / (1.0 + r * rho)
        E_minus[j] = E_plus[j] * rho

    flux = []
    for j in range(N):
        S = np.real(np.conj(ns[j]) * (E_plus[j] + E_minus[j])
                    * np.conj(E_plus[j] - E_minus[j]))
        flux.append(S)
    R = 1.0 - flux[0]
    A_layers = [flux[j] - flux[j + 1] for j in range(1, N - 1)]
    A_last = flux[N - 1]                       # into substrate / PEC-backed Au
    j_abs = 3                                  # absorber region index
    return R, A_layers, A_last, (ns[j_abs], E_plus[j_abs], E_minus[j_abs])


def field_in_absorber(lam, absorber_state, d_from_top):
    n_abs, Ep, Em = absorber_state
    ph = 2.0 * np.pi * n_abs * d_from_top / lam
    return Ep * np.exp(1j * ph) + Em * np.exp(-1j * ph)


def qh(lam, absorber_state, d_from_top):
    """Absorbed power density [W/m^3] at depth d for a 1 V/m incident wave."""
    n_abs, _, _ = absorber_state
    E = field_in_absorber(lam, absorber_state, d_from_top)
    eps2 = 2.0 * n_abs.real * n_abs.imag
    omega = 2.0 * np.pi * C0 / (lam * 1e-9)
    return 0.5 * omega * EPS0 * eps2 * abs(E) ** 2


def load_fem_spectrum():
    p = os.path.join(ROOT, 'full3d/results',
                     f'f3d_{A}_absorptance_production_planar.csv')
    rows = sorted(csv.DictReader(open(p)), key=lambda r: float(r['lambda_nm']))
    return rows


def am15g():
    d = np.loadtxt(os.path.join(
        ROOT, 'data/reference_spectra/AM15G_ASTM_G173_global.csv'),
        delimiter=',', comments='#')
    return d[:, 0], d[:, 1]


def jflux(lam, Aval):
    ld, irr = am15g()
    phi = irr * (ld * 1e-9) / (H * C0)
    m = (ld >= lam.min()) & (ld <= lam.max())
    return Q * np.trapz(np.interp(ld[m], lam, Aval) * phi[m], ld[m]) / 10.0


def band_irr(lams):
    """Bin-integrated AM1.5G irradiance, stage-14 conventions exactly:
    edges at midpoints, outer edges clamped to the grid endpoints."""
    ld, irr = am15g()
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


if __name__ == '__main__':
    fem = load_fem_spectrum()
    lams = np.array([float(r['lambda_nm']) for r in fem])

    # ---- step 1: validate the spectrum path on the FEM's own geometry
    print('== step 1: PEC-geometry TMM vs FEM spectrum ==')
    dmax = 0.0
    spec_pec, spec_corr = [], []
    for r in fem:
        lam = float(r['lambda_nm'])
        Rp, Ap, Alast, st_p = tmm(lam, pec_backed=True)
        Rc, Ac, Asub, st_c = tmm(lam, pec_backed=False)
        spec_pec.append((lam, Rp, Ap, Alast, st_p))
        spec_corr.append((lam, Rc, Ac, Asub, st_c))
        dmax = max(dmax, abs(Ap[2] - float(r['A_absorber'])),
                   abs(Rp - float(r['R_implied'])))
    print(f'   max |TMM_pec - FEM| over A_absorber and R: {dmax:.5f}')
    assert dmax < 5e-3, 'PEC-geometry TMM does not reproduce the FEM'

    # ---- step 2: validate the G(z) path against the FEM G(z) file
    print('== step 2: PEC-geometry TMM G(z) vs FEM G(z) ==')
    gfem = np.loadtxt(os.path.join(
        ROOT, 'full3d/results', f'f3d_{A}_planar_Gz_AM15G.csv'),
        delimiter=',', skiprows=1)
    zs_nm = gfem[:, 0] * 1e9                   # native optical frame
    irr_bin = band_irr(lams)
    scale = irr_bin * 2.0 * Z0                 # per unit-field solve
    Eph = H * C0 / (lams * 1e-9)

    def gz_profile(spectra):
        G = np.zeros_like(zs_nm)
        for i, (lam, R_, A_, Al_, st) in enumerate(spectra):
            d_top = (Z_ABS1 - zs_nm) * 1.0     # depth from absorber top, nm
            q = np.array([qh(lam, st, d) for d in d_top])
            G += q * scale[i] / Eph[i]
        return G

    G_pec = gz_profile(spec_pec)
    rel = np.abs(G_pec - gfem[:, 1]) / gfem[:, 1].max()
    J_pec = Q * (np.trapz(G_pec, zs_nm * 1e-9)
                 + G_pec[0] * (zs_nm.min() - Z_ABS0) * 1e-9
                 + G_pec[-1] * (Z_ABS1 - zs_nm.max()) * 1e-9) / 10.0
    J_fem = Q * (np.trapz(gfem[:, 1], zs_nm * 1e-9)
                 + gfem[0, 1] * (zs_nm.min() - Z_ABS0) * 1e-9
                 + gfem[-1, 1] * (Z_ABS1 - zs_nm.max()) * 1e-9) / 10.0
    print(f'   max |dG|/max(G) = {rel.max():.4f};  '
          f'J(G): TMM_pec {J_pec:.3f} vs FEM {J_fem:.3f} mA/cm2')
    assert rel.max() < 0.02, 'G(z) pipeline does not reproduce the FEM'

    # ---- step 3: emit the corrected (thick-Au) results
    print('== step 3: corrected thick-Au results ==')
    out_spec = os.path.join(
        ROOT, 'full3d/results',
        f'f3d_{A}_absorptance_production_planar_au80corr.csv')
    with open(out_spec, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['lambda_nm', 'band', 'n_elem', 'solve_s', 'worker',
                    'A_absorber', 'A_Au', 'A_HTL', 'A_TiO2', 'A_FTO_total',
                    'A_total', 'A_from_flux', 'R_implied', 'energy_residual'])
        for (lam, Rc, Ac, Asub, st), r in zip(spec_corr, fem):
            At = sum(Ac) + Asub
            w.writerow([f'{lam:.1f}', r['band'], 0, 0, 'tmm',
                        f'{Ac[2]:.6f}', f'{Asub:.6f}', f'{Ac[3]:.6f}',
                        f'{Ac[1]:.6f}', f'{Ac[0]:.6f}', f'{At:.6f}',
                        f'{At:.6f}', f'{Rc:.6f}', '0.0'])
    print(f'   -> {os.path.basename(out_spec)}')

    G_corr = gz_profile(spec_corr)
    out_gz = os.path.join(ROOT, 'full3d/results',
                          f'f3d_{A}_planar_Gz_AM15G_au80corr_forTransport.csv')
    with open(out_gz, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['z_m', 'G_1_per_m3_s'])
        for zz, gg in zip(zs_nm, G_corr):
            w.writerow([f'{(zz + C.Z_OFFSET_TO_TRANSPORT)*1e-9:.6e}',
                        f'{gg:.6e}'])
    print(f'   -> {os.path.basename(out_gz)}')

    lam_arr = lams
    A_abs_c = np.array([s[2][2] for s in spec_corr])
    A_fto_c = np.array([s[2][0] for s in spec_corr])
    A_au_c = np.array([s[3] for s in spec_corr])
    R_c = np.array([s[1] for s in spec_corr])
    A_abs_f = np.array([float(r['A_absorber']) for r in fem])
    J_corr = jflux(lam_arr, A_abs_c)
    J_femspec = jflux(lam_arr, A_abs_f)
    J_G = Q * (np.trapz(G_corr, zs_nm * 1e-9)
               + G_corr[0] * (zs_nm.min() - Z_ABS0) * 1e-9
               + G_corr[-1] * (Z_ABS1 - zs_nm.max()) * 1e-9) / 10.0
    inc = jflux(lam_arr, np.ones_like(lam_arr))
    print(f'\n   CORRECTED {A}: J_ph = {J_corr:.3f} mA/cm2 '
          f'(FEM truncated: {J_femspec:.3f}, {100*(J_femspec-J_corr)/J_corr:+.1f}%)')
    print(f'   budget: FTO {jflux(lam_arr, A_fto_c):.3f}  '
          f'Au {jflux(lam_arr, A_au_c):.3f}  R {jflux(lam_arr, R_c):.3f}  '
          f'incident {inc:.3f}')
    print(f'   G(z) cross-check: J from G = {J_G:.3f} '
          f'({100*(J_G-J_corr)/J_corr:+.2f}% vs spectrum)')
    print(f'   parent (prescribed-profile) ceiling was 2.07 -> '
          f'corrected change {100*(J_corr-2.07)/2.07:+.1f}%')
