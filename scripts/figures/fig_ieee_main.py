"""IEEE JPV main-text figures, drawn from the refreshed full-wave 3D results.

Everything here reads the result CSVs directly; the only hardcoded numbers are
the device metrics, which are quoted in IEEE_JPV_TASK_CHECKPOINT.md and were
each produced by a run whose control reproduced the published base case.

Figures are drawn AT final printed size (IEEE: 3.5 in one column, 7.16 in two)
and exported as vector PDF + 600 dpi PNG. Never scale them afterwards.

Run:  python3 build_scripts/fig_ieee_main.py
"""
import sys, os, csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'full3d'))
import f3d_style as S

OUT = os.path.join(ROOT, 'manuscript_ieee', 'figures')
os.makedirs(OUT, exist_ok=True)
S.apply()

Q = 1.602176634e-19
H = 6.62607015e-34
C0 = 2.99792458e8

ABS = ['FASnI3', 'Cu2AgBiI6', 'BaZrS3', 'Cs2AgBiBr6']
PRETTY = {'FASnI3': r'FASnI$_3$', 'Cu2AgBiI6': r'Cu$_2$AgBiI$_6$',
          'BaZrS3': r'BaZrS$_3$', 'Cs2AgBiBr6': r'Cs$_2$AgBiBr$_6$'}
# Fixed colour slot per absorber, held across every figure in the paper.
ASLOT = {'FASnI3': 0, 'Cu2AgBiI6': 1, 'BaZrS3': 2, 'Cs2AgBiBr6': 3}

NK = {'FASnI3': 'full3d/data/FASnI3_nk_Ghimire2017_SI.csv',
      'Cu2AgBiI6': 'data/optical_constants/Cu2AgBiI6_nk_Kamppinen2026.csv',
      'BaZrS3': 'full3d/data/BaZrS3_nk_Nishigaki2020.csv',
      'Cs2AgBiBr6': 'data/optical_constants/Cs2AgBiBr6_nk_Eddekkar2024.csv'}

# Device metrics of record. old = published (pre-refresh), new = this work.
# Cu2AgBiI6 is quoted at MATCHED uniform 1 mV continuation grid (see SI).
DEV = {
    'FASnI3':     dict(old=(14.740, 0.987, 0.5173, 7.521), new=(15.811, 0.988, 0.5090, 7.948)),
    'Cu2AgBiI6':  dict(old=(13.856, 1.379, 0.5190, 9.909), new=(15.017, 1.384, 0.5176, 10.757)),
    'BaZrS3':     dict(old=(11.846, 1.341, 0.3398, 5.395), new=(9.883, 1.337, 0.3395, 4.484)),
    'Cs2AgBiBr6': dict(old=(2.010, 1.710, 0.2865, 0.984), new=(2.371, 1.760, 0.2807, 1.170)),
}
JV = {  # control (old G(z)) and treatment (new G(z)) curve files
    'FASnI3':     ('results/jv_f3dctrl_fasni3_light_base.csv', 'results/jv_f3d_fasni3_light_base.csv'),
    'Cu2AgBiI6':  ('results/jv_f3dctrl_cabi_light_base_dense.csv', 'results/jv_f3d_cabi_light_base_dense.csv'),
    'BaZrS3':     ('results/jv_ctrl2_spiroTE_light_chi4p1_tau1ns.csv', 'results/jv_f3d_spiroTE_light_chi4p1_tau1ns.csv'),
    'Cs2AgBiBr6': ('results/jv_f3dctrl_cs_light_base.csv', 'results/jv_f3d_cs_light_base_au80corr.csv'),
}
AREA = (350e-9) ** 2


def p(*a):
    return os.path.join(ROOT, *a)


# Cs2AgBiBr6 uses the thick-Au corrected spectrum (stage 60); the FEM file
# carries the documented back-contact truncation artifact for that absorber.
SPEC_FILE = {A: f'f3d_{A}_absorptance_production_planar.csv' for A in ABS}
SPEC_FILE['Cs2AgBiBr6'] = 'f3d_Cs2AgBiBr6_absorptance_production_planar_au80corr.csv'


def spectrum(A):
    rows = list(csv.DictReader(open(p('full3d/results', SPEC_FILE[A]))))
    rows.sort(key=lambda r: float(r['lambda_nm']))
    out = {'lambda_nm': np.array([float(r['lambda_nm']) for r in rows])}
    for k in ('A_absorber', 'A_FTO_total', 'A_TiO2', 'A_HTL', 'A_Au',
              'R_implied', 'energy_residual'):
        out[k] = np.array([float(r[k]) for r in rows])
    return out


def am15g():
    d = np.loadtxt(p('data/reference_spectra/AM15G_ASTM_G173_global.csv'),
                   delimiter=',', comments='#')
    return d[:, 0], d[:, 1]


def jflux(lam, A):
    ld, irr = am15g()
    phi = irr * (ld * 1e-9) / (H * C0)
    m = (ld >= lam.min()) & (ld <= lam.max())
    return Q * np.trapz(np.interp(ld[m], lam, A) * phi[m], ld[m]) / 10.0


def nk(A):
    d = np.loadtxt(p(NK[A]), delimiter=',', comments=('#', '%'), skiprows=1)
    return d[:, 0] * 1e3, d[:, 1], d[:, 2]      # nm, n, k


def jv(path):
    d = np.loadtxt(p(path), delimiter=',', comments='#')
    if d.shape[0] == 3:
        d = d.T
    V, It = d[:, 0], d[:, 1]
    o = np.argsort(V); V, It = V[o], It[o]
    J = It / AREA * 0.1
    if V.min() < -0.1:                       # forward runs sweep Vapp negative
        V = -V; o = np.argsort(V); V, J = V[o], J[o]
    if np.interp(0, V, J) < 0:
        J = -J
    return V, J


def panel_label(ax, s):
    ax.text(-0.16, 1.04, s, transform=ax.transAxes, fontweight='bold',
            fontsize=9, va='bottom', ha='left', color=S.INK)


# ============================================================ Fig 1: optics in
def fig_optical_inputs():
    fig, axs = plt.subplots(1, 2, figsize=(S.COL2, 2.5), constrained_layout=True)
    for A in ABS:
        lam, n, k = nk(A)
        m = (lam >= 300) & (lam <= 900)
        c = S.PALETTE[ASLOT[A]]; d = S.DASHES[ASLOT[A]]
        kw = dict(color=c, lw=1.1)
        if d[0] is not None:
            kw['dashes'] = list(d)
        axs[0].plot(lam[m], n[m], **kw)
        axs[1].semilogy(lam[m], np.maximum(k[m], 1e-4), label=PRETTY[A], **kw)
    axs[0].set_xlabel('Wavelength (nm)'); axs[0].set_ylabel('Refractive index $n$')
    axs[1].set_xlabel('Wavelength (nm)'); axs[1].set_ylabel('Extinction coeff. $k$')
    axs[1].set_ylim(1e-4, 3)
    axs[1].legend(frameon=False, fontsize=6.5, loc='lower left', ncol=2)
    for a in axs:
        a.set_xlim(300, 900); a.grid(True, color=S.GRID, lw=0.4)
    panel_label(axs[0], '(a)'); panel_label(axs[1], '(b)')
    S.save(fig, os.path.join(OUT, 'fig1_optical_inputs'))
    plt.close(fig)


# ==================================================== Fig 2: absorptance+budget
def fig_absorptance_budget():
    fig = plt.figure(figsize=(S.COL2, 4.3), constrained_layout=True)
    gs = fig.add_gridspec(2, 2)
    axs = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]),
           fig.add_subplot(gs[1, :])]
    for A in ABS:
        s = spectrum(A)
        c = S.PALETTE[ASLOT[A]]; d = S.DASHES[ASLOT[A]]
        kw = dict(color=c, lw=1.1)
        if d[0] is not None:
            kw['dashes'] = list(d)
        axs[0].plot(s['lambda_nm'], s['A_absorber'], label=PRETTY[A], **kw)
        axs[1].plot(s['lambda_nm'], s['R_implied'], **kw)
    axs[0].set_ylabel('Absorber absorptance'); axs[1].set_ylabel('Reflectance')
    for a in axs[:2]:
        a.set_xlabel('Wavelength (nm)'); a.set_xlim(300, 900)
        a.set_ylim(0, 1); a.grid(True, color=S.GRID, lw=0.4)
    axs[0].legend(frameon=False, fontsize=6.5, loc='upper right')

    # stacked loss budget, per absorber
    ch = ['A_absorber', 'A_FTO_total', 'A_Au', 'R_implied']
    lab = ['Absorber (useful)', 'FTO parasitic', 'Au contact', 'Reflected']
    slot = [0, 1, 4, 5]
    x = np.arange(len(ABS)); w = 0.62; bot = np.zeros(len(ABS))
    for ci, (k, lb, sl) in enumerate(zip(ch, lab, slot)):
        v = np.array([jflux(spectrum(A)['lambda_nm'], spectrum(A)[k]) for A in ABS])
        axs[2].bar(x, v, w, bottom=bot, label=lb, color=S.PALETTE[sl],
                   edgecolor='white', linewidth=0.5)
        for xi, (vi, bi) in enumerate(zip(v, bot)):
            if vi > 1.2:
                axs[2].text(xi, bi + vi / 2, f'{vi:.1f}', ha='center',
                            va='center', fontsize=6, color='white',
                            fontweight='bold')
        bot += v
    axs[2].set_xticks(x); axs[2].set_xticklabels([PRETTY[A] for A in ABS])
    axs[2].set_ylabel(r'Photocurrent (mA cm$^{-2}$)')
    axs[2].legend(frameon=False, fontsize=6.5, ncol=4, loc='upper center',
                  bbox_to_anchor=(0.5, 1.16))
    axs[2].grid(True, axis='y', color=S.GRID, lw=0.4)
    panel_label(axs[0], '(a)'); panel_label(axs[1], '(b)')
    axs[2].text(-0.075, 1.04, '(c)', transform=axs[2].transAxes,
                fontweight='bold', fontsize=9, va='bottom', color=S.INK)
    S.save(fig, os.path.join(OUT, 'fig2_absorptance_budget'))
    plt.close(fig)


# ============================================================== Fig 3: G(z)
def fig_generation():
    fig, axs = plt.subplots(1, 2, figsize=(S.COL2, 2.5), constrained_layout=True)
    OLDG = {'FASnI3': 'FASnI3_Gz_profile_AM15G.csv',
            'Cu2AgBiI6': 'Cu2AgBiI6_Gz_profile_AM15G.csv',
            'BaZrS3': 'BaZrS3_Gz_profile_AM15G.csv',
            'Cs2AgBiBr6': 'Cs2AgBiBr6_Gz_profile_AM15G.csv'}
    for A in ABS:
        c = S.PALETTE[ASLOT[A]]; d = S.DASHES[ASLOT[A]]
        kw = dict(color=c, lw=1.1)
        if d[0] is not None:
            kw['dashes'] = list(d)
        o = np.loadtxt(p(OLDG[A]), delimiter=',', skiprows=1)
        axs[0].semilogy((o[:, 0] * 1e9 - 280), o[:, 1], **kw)
        gzf = (f'f3d_{A}_planar_Gz_AM15G_forTransport.csv'
               if A != 'Cs2AgBiBr6' else
               'f3d_Cs2AgBiBr6_planar_Gz_AM15G_au80corr_forTransport.csv')
        nw = np.loadtxt(p('full3d/results', gzf), delimiter=',', skiprows=1)
        axs[1].semilogy((nw[:, 0] * 1e9 - 280), nw[:, 1], label=PRETTY[A], **kw)
    for a, t in zip(axs, ['Previous optics', 'This work']):
        a.set_xlabel('Depth from HTL interface (nm)')
        a.set_xlim(0, 300); a.grid(True, color=S.GRID, lw=0.4)
        a.set_ylim(1e25, 3e28)
        a.text(0.03, 0.06, t, transform=a.transAxes, fontsize=7,
               color=S.INK_2, style='italic')
    axs[0].set_ylabel(r'$G(z)$ (m$^{-3}$ s$^{-1}$)')
    axs[1].legend(frameon=False, fontsize=6.5, loc='upper left')
    panel_label(axs[0], '(a)'); panel_label(axs[1], '(b)')
    S.save(fig, os.path.join(OUT, 'fig3_generation'))
    plt.close(fig)


# ============================================================== Fig 4: J-V
def fig_jv():
    fig, axs = plt.subplots(2, 2, figsize=(S.COL2, 4.2), constrained_layout=True)
    for ax, A in zip(axs.ravel(), ABS):
        c = S.PALETTE[ASLOT[A]]
        fo, fn = JV[A]
        Vo, Jo = jv(fo); Vn, Jn = jv(fn)
        ax.plot(Vo, Jo, color=S.INK_2, lw=1.0, dashes=[4, 1.5],
                label='Previous optics')
        ax.plot(Vn, Jn, color=c, lw=1.3, label='This work')
        ax.axhline(0, color=S.GRID, lw=0.5)
        jo, vo, fo_, po = DEV[A]['old']; jn, vn, fn_, pn = DEV[A]['new']
        ax.set_xlim(0, max(Vo.max(), Vn.max()))
        ax.set_ylim(min(-1.0, -0.05 * max(jo, jn)), 1.18 * max(jo, jn))
        ax.text(0.035, 0.94, PRETTY[A], transform=ax.transAxes, fontsize=8,
                fontweight='bold', va='top')
        ax.text(0.035, 0.80,
                f'PCE {po:.2f}% $\\rightarrow$ {pn:.2f}%',
                transform=ax.transAxes, fontsize=6.5, va='top', color=S.INK_2)
        ax.grid(True, color=S.GRID, lw=0.4)
    for ax in axs[1, :]:
        ax.set_xlabel('Voltage (V)')
    for ax in axs[:, 0]:
        ax.set_ylabel(r'Current density (mA cm$^{-2}$)')
    axs[0, 0].legend(frameon=False, fontsize=6.5, loc='center left')
    for ax, s in zip(axs.ravel(), ['(a)', '(b)', '(c)', '(d)']):
        panel_label(ax, s)
    S.save(fig, os.path.join(OUT, 'fig4_jv'))
    plt.close(fig)


if __name__ == '__main__':
    fig_optical_inputs();      print('fig1 optical inputs      OK')
    fig_absorptance_budget();  print('fig2 absorptance+budget  OK')
    fig_generation();          print('fig3 generation          OK')
    fig_jv();                  print('fig4 J-V                 OK')
    print(f'-> {OUT}')
