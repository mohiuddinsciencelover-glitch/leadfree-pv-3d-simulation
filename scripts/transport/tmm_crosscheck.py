"""Independent transfer-matrix cross-check of the full-wave FEM optics.

WHY. Every result in the paper is planar, and a laterally uniform stack at
normal incidence with periodic lateral boundaries is mathematically equivalent
to a one-dimensional coherent multilayer problem. This script solves that
problem with a scalar transfer-matrix method (TMM) -- a fully independent
implementation sharing NOTHING with the FEM except the optical inputs, which
are read through the same `f3d_optics.nk` the FEM materials were built from --
and compares per-layer absorptance and AM1.5G photocurrent, wavelength by
wavelength, against the FEM result CSVs.

This is the strongest validation in the study: the other two checks (budget
closure, G(z)-vs-spectrum) are different routes through the SAME solve; this
one is a different solver against the analytic planar limit. It also converts
the "why 3-D for a planar stack?" objection into a verification statement.

Stack (matching the FEM): air / FTO 600 / TiO2 50 / absorber 300 / Spiro 200 /
Au (semi-infinite). The FEM truncates Au at 45 nm backed by PEC; that is more
than three skin depths at every wavelength here, so semi-infinite Au is
optically indistinguishable (the FEM's own config documents this; returning
power < 1e-6).

Outputs: per-absorber max/mean |dA| and dJph, a validation summary, and
Fig. S7 (FEM points vs TMM line, per absorber).

Run:  python3 build_scripts/tmm_crosscheck.py
"""
import sys, os, csv, importlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'full3d'))

Q = 1.602176634e-19
H = 6.62607015e-34
C0 = 2.99792458e8

ABS = ['FASnI3', 'Cu2AgBiI6', 'BaZrS3', 'Cs2AgBiBr6']
PRETTY = {'FASnI3': r'FASnI$_3$', 'Cu2AgBiI6': r'Cu$_2$AgBiI$_6$',
          'BaZrS3': r'BaZrS$_3$', 'Cs2AgBiBr6': r'Cs$_2$AgBiBr$_6$'}


def load_fem(A):
    p = os.path.join(ROOT, 'full3d', 'results',
                     f'f3d_{A}_absorptance_production_planar.csv')
    rows = sorted(csv.DictReader(open(p)), key=lambda r: float(r['lambda_nm']))
    return {k: np.array([float(r[k]) for r in rows])
            for k in ('lambda_nm', 'A_absorber', 'A_FTO_total', 'A_Au',
                      'R_implied')}


def tmm_stack(lam, layers, pec=False):
    """Normal-incidence coherent TMM.

    layers: [(n_complex, thickness_nm), ...] between semi-infinite air above
    and a semi-infinite substrate given as the last entry with thickness None.
    Returns R and the absorbed fraction in every finite layer, via the net
    Poynting flux at each interface (exact for absorbing media, unlike
    |E|^2-based shortcuts).
    """
    n0 = 1.0 + 0.0j
    ns = [n0] + [n for n, d in layers]
    ds = [None] + [d for n, d in layers]

    # Backward recursion for interface reflection into each region.
    # r_j: amplitude reflection looking into region j+1 ... substrate.
    N = len(ns)
    r_eff = [None] * N
    r_eff[N - 1] = (-1.0 + 0.0j) if pec else (0.0 + 0.0j)
    for j in range(N - 2, -1, -1):
        r_jk = (ns[j] - ns[j + 1]) / (ns[j] + ns[j + 1])
        if ds[j + 1] is None:                      # substrate: no phase layer
            r_below = 0.0 + 0.0j
        else:
            beta = 2.0 * np.pi * ns[j + 1] * ds[j + 1] / lam
            r_below = r_eff[j + 1] * np.exp(2j * beta)
        r_eff[j] = (r_jk + r_below) / (1.0 + r_jk * r_below)

    # Forward sweep for field amplitudes at the top of each region.
    # E_plus[j], E_minus[j]: amplitudes just below interface j (top of region j).
    E_plus = [None] * N
    E_minus = [None] * N
    E_plus[0] = 1.0 + 0.0j
    E_minus[0] = r_eff[0]
    for j in range(1, N):
        t_jk = 2.0 * ns[j - 1] / (ns[j - 1] + ns[j])
        r_jk = (ns[j - 1] - ns[j]) / (ns[j - 1] + ns[j])
        # amplitude at bottom of region j-1
        if ds[j - 1] is None or j - 1 == 0:
            Ep_bot, Em_bot = E_plus[j - 1], E_minus[j - 1]
        else:
            beta = 2.0 * np.pi * ns[j - 1] * ds[j - 1] / lam
            Ep_bot = E_plus[j - 1] * np.exp(1j * beta)
            Em_bot = E_minus[j - 1] * np.exp(-1j * beta)
        # transmit across interface j-1|j:  E+ below = (Ep_bot + r*Em_bot... )
        # use S-matrix relation: Ep_j = t * Ep_bot / (1 + r_jk * rho_j) with
        # rho_j the effective reflection below -- equivalently solve directly:
        if ds[j] is None:
            rho = 0.0 + 0.0j
        else:
            beta_j = 2.0 * np.pi * ns[j] * ds[j] / lam
            rho = r_eff[j] * np.exp(2j * beta_j)
        Ep = t_jk * Ep_bot / (1.0 + r_jk * rho)
        E_plus[j] = Ep
        E_minus[j] = Ep * rho
    # Net Poynting flux (normalized to incident) at the TOP of each region.
    S_inc = np.real(n0)
    flux = []
    for j in range(N):
        Ep, Em = E_plus[j], E_minus[j]
        S = np.real(np.conj(ns[j]) * (Ep + Em) * np.conj(Ep - Em))
        flux.append(S / S_inc)
    R = 1.0 - flux[0]
    A_layers = [flux[j] - flux[j + 1] for j in range(1, N - 1)]
    A_sub = flux[N - 1]
    return R, A_layers, A_sub


def run_absorber(A, substrate='pec45'):
    os.environ['F3D_ABSORBER'] = A
    os.environ['F3D_PROFILE'] = 'production'
    os.environ['F3D_TEXTURE'] = 'off'
    for m in [m for m in list(sys.modules) if m in ('config', 'f3d_optics')]:
        del sys.modules[m]
    import config as C
    import f3d_optics as O

    fem = load_fem(A)
    lams = fem['lambda_nm']
    out = {k: [] for k in ('R', 'A_fto', 'A_etl', 'A_abs', 'A_htl', 'A_au')}
    L = C.LAYERS
    for lam in lams:
        stack = []
        for mat, key, th in [('fto', 'A_fto', L['h_fto']),
                             ('etl', 'A_etl', L['h_etl']),
                             ('abs', 'A_abs', L['h_abs']),
                             ('htl', 'A_htl', L['h_htl'])]:
            n, k = O.nk(mat, lam)
            stack.append((complex(float(np.asarray(n)),
                                  float(np.asarray(k))), th))
        n, k = O.nk('au', lam)
        n_au = complex(float(np.asarray(n)), float(np.asarray(k)))
        if substrate == 'pec45':                  # the FEM's actual geometry
            stack.append((n_au, L['h_au']))
            R, A_layers, A_sub = tmm_stack(lam, stack, pec=True)
        else:                                     # thick-contact limit
            stack.append((n_au, None))
            R, A_layers, A_sub = tmm_stack(lam, stack, pec=False)
        out['R'].append(R)
        out['A_fto'].append(A_layers[0])
        out['A_etl'].append(A_layers[1])
        out['A_abs'].append(A_layers[2])
        out['A_htl'].append(A_layers[3])
        out['A_au'].append(A_sub)
    return lams, fem, {k: np.array(v) for k, v in out.items()}


def jph(lam, Aval):
    d = np.loadtxt(os.path.join(
        ROOT, 'data/reference_spectra/AM15G_ASTM_G173_global.csv'),
        delimiter=',', comments='#')
    ld, irr = d[:, 0], d[:, 1]
    phi = irr * (ld * 1e-9) / (H * C0)
    m = (ld >= lam.min()) & (ld <= lam.max())
    return Q * np.trapz(np.interp(ld[m], lam, Aval) * phi[m], ld[m]) / 10.0


if __name__ == '__main__':
    sys.path.insert(0, os.path.join(ROOT, 'full3d'))
    import f3d_style as S
    S.apply()
    fig, axs = plt.subplots(2, 2, figsize=(S.COL2, 4.2),
                            constrained_layout=True)
    print(f'{"absorber":12s} {"max|dA_abs|":>12} {"mean|dA_abs|":>13} '
          f'{"max|dR|":>9} {"Jph FEM":>9} {"Jph TMM":>9} {"dJph":>8}')
    worst = 0.0
    for ax, A in zip(axs.ravel(), ABS):
        lams, fem, tmm = run_absorber(A, 'pec45')
        dA = tmm['A_abs'] - fem['A_absorber']
        dR = tmm['R'] - fem['R_implied']
        jf = jph(lams, fem['A_absorber'])
        jt = jph(lams, tmm['A_abs'])
        worst = max(worst, np.abs(dA).max())
        print(f'{A:12s} {np.abs(dA).max():12.5f} {np.abs(dA).mean():13.5f} '
              f'{np.abs(dR).max():9.5f} {jf:9.3f} {jt:9.3f} '
              f'{100*(jt-jf)/jf:+7.2f}%')
        sl = {'FASnI3': 0, 'Cu2AgBiI6': 1, 'BaZrS3': 2, 'Cs2AgBiBr6': 3}[A]
        ax.plot(lams, tmm['A_abs'], color=S.PALETTE[sl], lw=1.1,
                label='TMM, FEM geometry')
        ax.plot(lams, fem['A_absorber'], 'o', ms=2.2, mfc='none',
                mec=S.INK, mew=0.5, label='FEM (this work)')
        if A == 'Cs2AgBiBr6':
            _, _, corr = run_absorber(A, 'thick')
            ax.plot(lams, corr['A_abs'], color=S.PALETTE[5], lw=1.0,
                    dashes=[3, 1.5], label='TMM, thick-Au (corrected)')
            ax.legend(frameon=False, fontsize=5.8, loc='upper right')
        ax.set_xlim(300, 900); ax.set_ylim(0, 1)
        ax.grid(True, color=S.GRID, lw=0.4)
        ax.text(0.03, 0.93, PRETTY[A], transform=ax.transAxes, fontsize=8,
                fontweight='bold', va='top')
        ax.text(0.03, 0.80, f'max $|\\Delta A|$ = {np.abs(dA).max():.4f}',
                transform=ax.transAxes, fontsize=6.5, va='top', color=S.INK_2)
    for ax in axs[1, :]:
        ax.set_xlabel('Wavelength (nm)')
    for ax in axs[:, 0]:
        ax.set_ylabel('Absorber absorptance')
    axs[0, 0].legend(frameon=False, fontsize=6.5, loc='center right')
    for ax, s in zip(axs.ravel(), ['(a)', '(b)', '(c)', '(d)']):
        ax.text(-0.16, 1.04, s, transform=ax.transAxes, fontweight='bold',
                fontsize=9, va='bottom', color=S.INK)
    out = os.path.join(ROOT, 'manuscript_ieee', 'figures_si',
                       'figS7_tmm_crosscheck')
    S.save(fig, out)
    print(f'\nWORST |dA_absorber| across all four: {worst:.5f}')
    print(f'-> {out}.pdf')
