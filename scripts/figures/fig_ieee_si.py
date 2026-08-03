"""IEEE JPV supplementary figures: validation evidence and the disclosures.

Every figure here exists because a reviewer would otherwise have to take a
claim on trust. The set covers the two optical-data replacements, the
periodic-mesh validation, and the three numerical caveats that must be
disclosed (Cu2AgBiI6 sub-gap absorption, Cu2AgBiI6 grid-dependent Voc,
BaZrS3 radiative-coefficient insensitivity).

Run:  python3 build_scripts/fig_ieee_si.py
"""
import sys, os, csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'full3d'))
import f3d_style as S

OUT = os.path.join(ROOT, 'manuscript_ieee', 'figures_si')
os.makedirs(OUT, exist_ok=True)
S.apply()

Q = 1.602176634e-19; H = 6.62607015e-34; C0 = 2.99792458e8
KB = 1.380649e-23; QE = 1.602176634e-19; HP = 6.62607015e-34
ABS = ['FASnI3', 'Cu2AgBiI6', 'BaZrS3', 'Cs2AgBiBr6']
PRETTY = {'FASnI3': r'FASnI$_3$', 'Cu2AgBiI6': r'Cu$_2$AgBiI$_6$',
          'BaZrS3': r'BaZrS$_3$', 'Cs2AgBiBr6': r'Cs$_2$AgBiBr$_6$'}
ASLOT = {'FASnI3': 0, 'Cu2AgBiI6': 1, 'BaZrS3': 2, 'Cs2AgBiBr6': 3}
AREA = (350e-9) ** 2


def p(*a):
    return os.path.join(ROOT, *a)


def lab(ax, s):
    ax.text(-0.17, 1.04, s, transform=ax.transAxes, fontweight='bold',
            fontsize=9, va='bottom', ha='left', color=S.INK)


def spectrum(A):
    rows = list(csv.DictReader(open(p('full3d/results',
                f'f3d_{A}_absorptance_production_planar.csv'))))
    rows.sort(key=lambda r: float(r['lambda_nm']))
    out = {'lambda_nm': np.array([float(r['lambda_nm']) for r in rows])}
    for k in ('A_absorber', 'energy_residual'):
        out[k] = np.array([float(r[k]) for r in rows])
    return out


def am15g():
    d = np.loadtxt(p('data/reference_spectra/AM15G_ASTM_G173_global.csv'),
                   delimiter=',', comments='#')
    return d[:, 0], d[:, 1]


def jflux(lam, A, lo=0.0, hi=1e9):
    ld, irr = am15g()
    phi = irr * (ld * 1e-9) / (H * C0)
    m = (ld >= max(lo, lam.min())) & (ld <= min(hi, lam.max()))
    if not m.any():
        return 0.0
    return Q * np.trapz(np.interp(ld[m], lam, A) * phi[m], ld[m]) / 10.0


def readnk(path):
    d = np.loadtxt(p(path), delimiter=',', comments=('#', '%'), skiprows=1)
    return d[:, 0] * 1e3, d[:, 1], d[:, 2]


def jv(path):
    d = np.loadtxt(p(path), delimiter=',', comments='#')
    if d.shape[0] == 3:
        d = d.T
    V, It = d[:, 0], d[:, 1]
    o = np.argsort(V); V, It = V[o], It[o]
    J = It / AREA * 0.1
    if V.min() < -0.1:
        V = -V; o = np.argsort(V); V, J = V[o], J[o]
    if np.interp(0, V, J) < 0:
        J = -J
    return V, J


# ---------------------------------------------- S1: optical-data replacements
def si_optical_replacement():
    fig, axs = plt.subplots(1, 2, figsize=(S.COL2, 2.5), constrained_layout=True)
    lo, no, ko = readnk('data/optical_constants/FASnI3_nk_Ghimire2017.csv')
    ln, nn, kn = readnk('full3d/data/FASnI3_nk_Ghimire2017_SI.csv')
    m = (lo >= 300) & (lo <= 950); m2 = (ln >= 300) & (ln <= 950)
    axs[0].semilogy(lo[m], np.maximum(ko[m], 1e-4), color=S.INK_2, lw=1.0,
                    dashes=[4, 1.5], label='Digitized figures (previous)')
    axs[0].semilogy(ln[m2], np.maximum(kn[m2], 1e-4), color=S.PALETTE[0],
                    lw=1.2, label='Tabulated SI (this work)')
    axs[0].axvline(729.3, color=S.PALETTE[1], lw=0.8, dashes=[2, 2])
    axs[0].annotate('1.70 eV splice\n($5.8\\times$ step in $k$)', xy=(729, 0.2),
                    xytext=(560, 0.012), fontsize=6, color=S.PALETTE[1],
                    arrowprops=dict(arrowstyle='->', color=S.PALETTE[1], lw=0.6))
    axs[0].set_title(PRETTY['FASnI3'], fontsize=8)

    lo, no, ko = readnk('data/optical_constants/BaZrS3_nk_KK.csv')
    ln, nn, kn = readnk('full3d/data/BaZrS3_nk_Nishigaki2020.csv')
    m = (lo >= 300) & (lo <= 950); m2 = (ln >= 300) & (ln <= 950)
    axs[1].semilogy(lo[m], np.maximum(ko[m], 1e-4), color=S.INK_2, lw=1.0,
                    dashes=[4, 1.5], label='KK of computed $\\varepsilon_2$ (previous)')
    axs[1].semilogy(ln[m2], np.maximum(kn[m2], 1e-4), color=S.PALETTE[2],
                    lw=1.2, label='Measured ellipsometry (this work)')
    axs[1].axvline(690, color=S.PALETTE[1], lw=0.8, dashes=[2, 2])
    axs[1].annotate('hard zero at 690 nm\ninside the absorption range',
                    xy=(690, 0.02), xytext=(430, 0.0015), fontsize=6,
                    color=S.PALETTE[1],
                    arrowprops=dict(arrowstyle='->', color=S.PALETTE[1], lw=0.6))
    axs[1].set_title(PRETTY['BaZrS3'], fontsize=8)
    for a in axs:
        a.set_xlabel('Wavelength (nm)'); a.set_ylabel('Extinction coeff. $k$')
        a.set_xlim(300, 950); a.set_ylim(1e-4, 3); a.grid(True, color=S.GRID, lw=0.4)
        a.legend(frameon=False, fontsize=6, loc='lower left')
    lab(axs[0], '(a)'); lab(axs[1], '(b)')
    S.save(fig, os.path.join(OUT, 'figS1_optical_replacement'))
    plt.close(fig)


# ------------------------------------------------------- S2: energy residuals
def si_validation():
    fig, axs = plt.subplots(1, 2, figsize=(S.COL2, 2.4), constrained_layout=True)
    for A in ABS:
        s = spectrum(A)
        c = S.PALETTE[ASLOT[A]]; d = S.DASHES[ASLOT[A]]
        kw = dict(color=c, lw=1.0)
        if d[0] is not None:
            kw['dashes'] = list(d)
        axs[0].plot(s['lambda_nm'], 100 * s['energy_residual'],
                    label=PRETTY[A], **kw)
    axs[0].axhline(2, color=S.PALETTE[1], lw=0.8, dashes=[2, 2])
    axs[0].axhline(-2, color=S.PALETTE[1], lw=0.8, dashes=[2, 2])
    axs[0].text(0.98, 0.06, 'acceptance band $\\pm2\\%$', transform=axs[0].transAxes,
                ha='right', fontsize=6, color=S.PALETTE[1])
    axs[0].set_xlabel('Wavelength (nm)')
    axs[0].set_ylabel('Energy-budget residual (%)')
    axs[0].set_xlim(300, 900); axs[0].set_ylim(-3, 3)
    axs[0].grid(True, color=S.GRID, lw=0.4)
    axs[0].legend(frameon=False, fontsize=6, ncol=2, loc='upper center')

    # band-seam agreement: same wavelength solved on two independent meshes
    seam = {'FASnI3': (0.070, 0.023), 'Cu2AgBiI6': (0.079, 0.020),
            'BaZrS3': (0.075, 0.020), 'Cs2AgBiBr6': (0.096, 0.000)}
    x = np.arange(len(ABS)); w = 0.36
    axs[1].bar(x - w/2, [seam[A][0] for A in ABS], w, label='400 nm seam',
               color=S.PALETTE[0])
    axs[1].bar(x + w/2, [seam[A][1] for A in ABS], w, label='600 nm seam',
               color=S.PALETTE[2])
    axs[1].set_xticks(x); axs[1].set_xticklabels([PRETTY[A] for A in ABS],
                                                 fontsize=6.5)
    axs[1].set_ylabel('Seam disagreement (%)')
    axs[1].legend(frameon=False, fontsize=6.5)
    axs[1].grid(True, axis='y', color=S.GRID, lw=0.4)
    lab(axs[0], '(a)'); lab(axs[1], '(b)')
    S.save(fig, os.path.join(OUT, 'figS2_validation'))
    plt.close(fig)


# ------------------------------------------- S3: Cu2AgBiI6 sub-gap absorption
def si_subgap():
    s = spectrum('Cu2AgBiI6')
    lam, A = s['lambda_nm'], s['A_absorber']
    lg = 1239.841984 / 2.06
    fig, axs = plt.subplots(1, 2, figsize=(S.COL2, 2.4), constrained_layout=True)
    axs[0].plot(lam, A, color=S.PALETTE[1], lw=1.2)
    axs[0].axvline(lg, color=S.INK_2, lw=0.9, dashes=[3, 2])
    axs[0].fill_between(lam, 0, A, where=(lam >= lg), color=S.PALETTE[1],
                        alpha=0.25)
    axs[0].annotate(f'Tauc gap 2.06 eV\n({lg:.0f} nm)', xy=(lg, 0.85),
                    xytext=(lg + 55, 0.9), fontsize=6, color=S.INK_2,
                    arrowprops=dict(arrowstyle='->', color=S.INK_2, lw=0.6))
    axs[0].set_xlabel('Wavelength (nm)'); axs[0].set_ylabel('Absorber absorptance')
    axs[0].set_xlim(300, 900); axs[0].set_ylim(0, 1)
    axs[0].grid(True, color=S.GRID, lw=0.4)

    segs = [('300-602\nabove gap', 300, lg, 0),
            ('602-700\nUrbach tail', lg, 700, 1),
            ('700-750\nweak tail', 700, 750, 3),
            ('750-886\nflat-$\\alpha$\nartefact', 750, 886, 5)]
    vals = [jflux(lam, A, a, b) for _, a, b, _ in segs]
    tot = jflux(lam, A)
    axs[1].bar(range(len(segs)), vals, 0.62,
               color=[S.PALETTE[s_] for _, _, _, s_ in segs])
    for i, v in enumerate(vals):
        axs[1].text(i, v + 0.15, f'{v:.2f}\n({100*v/tot:.1f}%)', ha='center',
                    fontsize=6, color=S.INK)
    axs[1].set_xticks(range(len(segs)))
    axs[1].set_xticklabels([s_ for s_, _, _, _ in segs], fontsize=5.8)
    axs[1].set_ylabel(r'Photocurrent (mA cm$^{-2}$)')
    axs[1].set_ylim(0, max(vals) * 1.35)
    axs[1].grid(True, axis='y', color=S.GRID, lw=0.4)
    lab(axs[0], '(a)'); lab(axs[1], '(b)')
    S.save(fig, os.path.join(OUT, 'figS3_subgap_cu2agbii6'))
    plt.close(fig)
    print(f'  sub-gap total {sum(vals[1:]):.3f} of {tot:.3f} '
          f'({100*sum(vals[1:])/tot:.1f}%)')


# ------------------------------------------ S4: Cu2AgBiI6 Voc grid dependence
def si_voc_grid():
    fig, axs = plt.subplots(1, 2, figsize=(S.COL2, 2.4), constrained_layout=True)
    runs = [('Mixed 1-25 mV grid (published)',
             'results/jv_cabi_light_base_dense.csv', S.INK_2, [4, 1.5]),
            ('Uniform 1 mV grid', 'results/jv_f3dctrl_cabi_light_base_dense.csv',
             S.PALETTE[1], None)]
    for lbl_, f, c, dsh in runs:
        V, J = jv(f)
        kw = dict(color=c, lw=1.2)
        if dsh:
            kw['dashes'] = dsh
        axs[0].plot(V, J, label=lbl_, **kw); axs[1].plot(V, J, **kw)
    for a in axs:
        a.axhline(0, color=S.GRID, lw=0.5); a.grid(True, color=S.GRID, lw=0.4)
        a.set_xlabel('Voltage (V)')
    axs[0].set_ylabel(r'Current density (mA cm$^{-2}$)')
    axs[0].set_xlim(0, 1.6); axs[0].set_ylim(-1, 16)
    axs[0].legend(frameon=False, fontsize=6, loc='lower left')
    axs[0].annotate('identical through MPP\n($P_{\\max}$ 9.9126, $V_{\\rm mpp}$ 0.786)',
                    xy=(0.786, 12.6), xytext=(0.15, 5.0), fontsize=6,
                    color=S.INK_2,
                    arrowprops=dict(arrowstyle='->', color=S.INK_2, lw=0.6))
    axs[1].set_xlim(1.25, 1.58); axs[1].set_ylim(-0.12, 0.32)
    axs[1].set_ylabel(r'Current density (mA cm$^{-2}$)')
    axs[1].text(0.5, 0.92, 'pre-$V_{oc}$ tail (magnified)',
                transform=axs[1].transAxes, ha='center', fontsize=6.5,
                color=S.INK_2, style='italic')
    for vv, cc in [(1.512, S.INK_2), (1.379, S.PALETTE[1])]:
        axs[1].axvline(vv, color=cc, lw=0.7, dashes=[2, 2])
        axs[1].text(vv, 0.26, f'{vv:.3f} V', rotation=90, fontsize=5.8,
                    color=cc, ha='right', va='top')
    lab(axs[0], '(a)'); lab(axs[1], '(b)')
    S.save(fig, os.path.join(OUT, 'figS4_voc_grid_cu2agbii6'))
    plt.close(fig)


# -------------------------------------------------- S5: BaZrS3 B_rad (VRS)
def si_brad():
    T = 300.0
    def load(path):
        d = np.loadtxt(p(path), delimiter=',', comments=('#', '%'), skiprows=1)
        lam = d[:, 0] * 1e3; n, k = d[:, 1], d[:, 2]
        E = 1239.841984 / lam; a = 4 * np.pi * k / (lam * 1e-7)
        o = np.argsort(E)
        return E[o], a[o], n[o]

    mn, mp, Eg = 0.3, 0.9, 1.88
    Nc = 2.5094e19 * mn ** 1.5; Nv = 2.5094e19 * mp ** 1.5
    ni2 = Nc * Nv * np.exp(-Eg / (8.617333262e-5 * T))

    def vrs(E, a, nr, E_lo):
        Ei = np.linspace(E_lo, 6.0, 4000)
        ai = np.interp(Ei, E, a, left=0.0, right=0.0) * 100.0
        nri = np.interp(Ei, E, nr); EJ = Ei * QE
        ig = (8 * np.pi / (HP ** 3 * C0 ** 2)) * nri ** 2 * EJ ** 2 * ai \
            / np.expm1(EJ / (KB * T))
        return np.trapz(ig, EJ) * 1e-6 / ni2

    fig, axs = plt.subplots(1, 2, figsize=(S.COL2, 2.4), constrained_layout=True)
    Elo = np.linspace(1.70, 2.10, 60)
    for lbl_, path, c, dsh in [
            ('KK of computed $\\varepsilon_2$ (previous)',
             'data/optical_constants/BaZrS3_nk_KK.csv', S.INK_2, [4, 1.5]),
            ('Measured ellipsometry (this work)',
             'full3d/data/BaZrS3_nk_Nishigaki2020.csv', S.PALETTE[2], None)]:
        E, a, nr = load(path)
        b = [vrs(E, a, nr, e) for e in Elo]
        kw = dict(color=c, lw=1.2)
        if dsh:
            kw['dashes'] = dsh
        axs[0].semilogy(Elo, b, label=lbl_, **kw)
    axs[0].axvline(1.88, color=S.PALETTE[1], lw=0.8, dashes=[2, 2])
    axs[0].text(1.885, 3e-9, '$E_g$ used in\n$n_i^2$ (1.88 eV)', fontsize=6,
                color=S.PALETTE[1])
    axs[0].axhline(2.335e-9, color=S.PALETTE[3], lw=0.8, dashes=[1, 1.5])
    axs[0].text(1.71, 3.2e-9, 'published $B_{\\rm rad}$', fontsize=6,
                color=S.PALETTE[3])
    axs[0].set_xlabel('Lower integration limit (eV)')
    axs[0].set_ylabel(r'$B_{\rm rad}$ (cm$^3$ s$^{-1}$)')
    axs[0].grid(True, color=S.GRID, lw=0.4)
    axs[0].legend(frameon=False, fontsize=6, loc='lower left')

    V1, J1 = jv('results/jv_f3d_spiroTE_light_chi4p1_tau1ns.csv')
    V2, J2 = jv('results/jv_f3d_spiroTE_light_chi4p1_tau1ns_Brad.csv')
    axs[1].plot(V1, J1, color=S.INK_2, lw=1.0, dashes=[4, 1.5],
                label='$B_{\\rm rad}=2.335\\times10^{-9}$')
    axs[1].plot(V2, J2, color=S.PALETTE[2], lw=1.2,
                label='$B_{\\rm rad}=5.37\\times10^{-12}$')
    axs[1].axhline(0, color=S.GRID, lw=0.5)
    axs[1].set_xlabel('Voltage (V)')
    axs[1].set_ylabel(r'Current density (mA cm$^{-2}$)')
    axs[1].set_xlim(0, 1.5); axs[1].set_ylim(-0.5, 11)
    axs[1].grid(True, color=S.GRID, lw=0.4)
    axs[1].legend(frameon=False, fontsize=6, loc='lower left')
    axs[1].text(0.5, 0.93, '$435\\times$ change in $B_{\\rm rad}$: $V_{oc}$ moves 3 mV',
                transform=axs[1].transAxes, ha='center', fontsize=6,
                color=S.INK_2, style='italic')
    lab(axs[0], '(a)'); lab(axs[1], '(b)')
    S.save(fig, os.path.join(OUT, 'figS5_brad_bazrs3'))
    plt.close(fig)


if __name__ == '__main__':
    si_optical_replacement(); print('figS1 optical replacement OK')
    si_validation();          print('figS2 validation          OK')
    si_subgap();              print('figS3 sub-gap Cu2AgBiI6   OK')
    si_voc_grid();            print('figS4 Voc grid Cu2AgBiI6  OK')
    si_brad();                print('figS5 B_rad BaZrS3        OK')
    print(f'-> {OUT}')
