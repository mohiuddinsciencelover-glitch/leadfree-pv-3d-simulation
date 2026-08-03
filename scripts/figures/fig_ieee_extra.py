"""Two additional figures: the band-alignment diagram and the G(z, lambda) maps.

WHY THESE TWO.

The cliff taxonomy is the paper's central mechanistic claim and had no figure
at all -- it was carried entirely in prose. A band diagram is the natural way
to show it, and it makes the two classes visible at a glance rather than
asking the reader to hold four sets of offsets in their head. That goes in the
MAIN text (Fig. 5).

The depth-and-wavelength generation map explains a result the broadband G(z)
curve cannot: why FASnI3 loses collection efficiency when its optics improve
while Cs2AgBiBr6 does not. It is supporting evidence rather than a headline,
so it goes in the SUPPLEMENTARY (Fig. S6).

Run:  python3 build_scripts/fig_ieee_extra.py
"""
import sys, os, csv, glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.patches import Rectangle, FancyArrowPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'full3d'))
import f3d_style as S

OUT_MAIN = os.path.join(ROOT, 'manuscript_ieee', 'figures')
OUT_SI = os.path.join(ROOT, 'manuscript_ieee', 'figures_si')
os.makedirs(OUT_MAIN, exist_ok=True); os.makedirs(OUT_SI, exist_ok=True)
S.apply()

ABS = ['FASnI3', 'Cu2AgBiI6', 'BaZrS3', 'Cs2AgBiBr6']
PRETTY = {'FASnI3': r'FASnI$_3$', 'Cu2AgBiI6': r'Cu$_2$AgBiI$_6$',
          'BaZrS3': r'BaZrS$_3$', 'Cs2AgBiBr6': r'Cs$_2$AgBiBr$_6$'}
ASLOT = {'FASnI3': 0, 'Cu2AgBiI6': 1, 'BaZrS3': 2, 'Cs2AgBiBr6': 3}

# Electron affinity and gap, in eV. Absorber values are the base cases of the
# device runs; transport-layer values are the fixed literature set.
CHI = {'FASnI3': 3.50, 'Cu2AgBiI6': 3.22, 'BaZrS3': 4.10, 'Cs2AgBiBr6': 4.00}
EG = {'FASnI3': 1.41, 'Cu2AgBiI6': 2.06, 'BaZrS3': 1.88, 'Cs2AgBiBr6': 2.32}
CHI_ETL, EG_ETL = 4.15, 3.2          # TiO2
CHI_HTL, EG_HTL = 2.15, 2.9          # Spiro-OMeTAD

# Sequential ramps for the gradient fills: light at the band edge, saturating
# into the layer colour. Built from the validated categorical palette so the
# figure keeps the paper's colour identity.
def ramp(hex_to, name):
    return LinearSegmentedColormap.from_list(name, ['#ffffff', hex_to])


def p(*a):
    return os.path.join(ROOT, *a)


def grad_band(ax, x0, x1, ytop, ybot, color, alpha=0.85, vertical=True):
    """Fill a band region with a vertical gradient, light at the band edge."""
    n = 128
    g = np.linspace(0, 1, n).reshape(-1, 1)
    ax.imshow(g, extent=[x0, x1, ybot, ytop], aspect='auto', origin='lower',
              cmap=ramp(color, 'r'), alpha=alpha, zorder=1,
              interpolation='bilinear')


# ============================================================ Fig 5: bands
def fig_band_alignment():
    fig, axs = plt.subplots(1, 4, figsize=(S.COL2, 2.9), sharey=True,
                            constrained_layout=True)
    # layer x-extents (arbitrary units, drawn to suggest the stack order)
    xs = {'ETL': (0.0, 1.0), 'ABS': (1.0, 2.6), 'HTL': (2.6, 3.6)}
    E_FLOOR = -7.85

    for ax, A in zip(axs, ABS):
        cb_a, vb_a = -CHI[A], -(CHI[A] + EG[A])
        cb_e, vb_e = -CHI_ETL, -(CHI_ETL + EG_ETL)
        cb_h, vb_h = -CHI_HTL, -(CHI_HTL + EG_HTL)

        for key, (cb, vb, col) in {
                'ETL': (cb_e, vb_e, '#8a8a8a'),
                'ABS': (cb_a, vb_a, S.PALETTE[ASLOT[A]]),
                'HTL': (cb_h, vb_h, '#8a8a8a')}.items():
            x0, x1 = xs[key]
            # conduction band: gradient downward from the edge
            grad_band(ax, x0, x1, cb + 0.55, cb, col, alpha=0.75)
            # valence band: gradient upward from the edge
            grad_band(ax, x0, x1, vb, vb - 0.55, col, alpha=0.75)
            ax.plot([x0, x1], [cb, cb], color=S.INK, lw=1.1, zorder=3)
            ax.plot([x0, x1], [vb, vb], color=S.INK, lw=1.1, zorder=3)

        # the two offsets that define the taxonomy
        dEc = cb_a - cb_e          # negative => cliff at the electron contact
        dEv = vb_a - vb_h          # negative => cliff at the hole contact
        etl_limited = abs(dEc) > abs(dEv)
        for x, dE, cb1, cb2, is_c in [(1.0, dEc, cb_e, cb_a, True),
                                      (2.6, dEv, vb_a, vb_h, False)]:
            is_lim = is_c == etl_limited
            col = S.PALETTE[1] if is_lim else S.INK_2
            if is_lim:
                # the offset that limits the device: full double arrow
                ax.annotate('', xy=(x, cb2), xytext=(x, cb1),
                            arrowprops=dict(arrowstyle='<->', color=col, lw=1.6,
                                            shrinkA=0, shrinkB=0), zorder=4)
                ax.text(x + 0.10, (cb1 + cb2) / 2, f'{abs(dE):.2f}',
                        fontsize=7, color=col, va='center', ha='left',
                        fontweight='bold', zorder=5)
            else:
                # the other offset is small; an arrow would be arrowheads only,
                # so mark it with a plain tick and label placed clear of it
                ax.plot([x, x], [cb1, cb2], color=col, lw=0.9, zorder=4)
                ax.text(x + 0.10, (cb1 + cb2) / 2 - 0.30, f'{abs(dE):.2f}',
                        fontsize=6, color=col, va='center', ha='left', zorder=5)

        ax.set_xlim(-0.05, 3.75); ax.set_ylim(E_FLOOR, -1.15)
        ax.set_xticks([0.5, 1.8, 3.1])
        ax.set_xticklabels([r'TiO$_2$', 'absorber', 'Spiro'], fontsize=6)
        ax.tick_params(axis='x', length=0)
        ax.set_title(PRETTY[A], fontsize=8, pad=12)
        cls = 'ETL cliff' if etl_limited else 'HTL cliff'
        ax.text(0.5, 1.005, cls, transform=ax.transAxes, ha='center',
                va='bottom', fontsize=6.5, color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.22', fc=S.PALETTE[1], ec='none'))
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
    axs[0].set_ylabel('Energy vs. vacuum (eV)')
    for ax, s in zip(axs, ['(a)', '(b)', '(c)', '(d)']):
        ax.text(-0.02, 1.06, s, transform=ax.transAxes, fontweight='bold',
                fontsize=9, va='bottom', ha='left', color=S.INK)
    S.save(fig, os.path.join(OUT_MAIN, 'fig5_band_alignment'))
    plt.close(fig)
    for A in ABS:
        dEc = -CHI[A] + CHI_ETL
        dEv = -(CHI[A] + EG[A]) + (CHI_HTL + EG_HTL)
        print(f'  {A:11s} dEc={dEc:+.2f}  dEv={dEv:+.2f}  -> '
              f'{"ETL" if abs(dEc) > abs(dEv) else "HTL"} limited')


# ==================================================== Fig S6: G(z, lambda)
def gz_map(A):
    rows = []
    for f in glob.glob(p('full3d/results/shards_planar',
                         f'{A}_production_w[0-9][0-9]_Gz.csv')):
        rows += list(csv.DictReader(open(f)))
    if not rows:
        return None
    def band_of(l):
        return 0 if l <= 390 else (1 if l <= 590 else 2)
    rows = [r for r in rows if int(r['band']) == band_of(float(r['lambda_nm']))]
    lam = np.array([float(r['lambda_nm']) for r in rows])
    z = np.array([float(r['z_nm']) for r in rows])
    q = np.array([float(r['Qh_avg_W_m3']) for r in rows])
    L, Z = np.unique(lam), np.unique(z)
    M = np.full((len(L), len(Z)), np.nan)
    li = {v: i for i, v in enumerate(L)}; zi = {v: i for i, v in enumerate(Z)}
    for a, b, c in zip(lam, z, q):
        M[li[a], zi[b]] = c
    return L, Z, M


def fig_generation_map():
    fig, axs = plt.subplots(1, 4, figsize=(S.COL2, 2.5), sharey=True,
                            constrained_layout=True)
    ims = []
    for ax, A in zip(axs, ABS):
        got = gz_map(A)
        if got is None:
            ax.text(0.5, 0.5, 'no data', transform=ax.transAxes, ha='center')
            continue
        L, Z, M = got
        M = np.maximum(np.nan_to_num(M, nan=1e-3), 1e-3)
        # depth measured from the illuminated (ETL) face
        depth = Z.max() - Z
        im = ax.pcolormesh(L, depth, M.T, cmap='magma',
                           norm=LogNorm(vmin=1e1, vmax=4.5e4), shading="gouraud")
        ims.append(im)
        ax.set_xlim(300, 900); ax.set_ylim(depth.max(), 0)
        ax.set_xlabel('Wavelength (nm)')
        ax.set_title(PRETTY[A], fontsize=8, pad=3)
    axs[0].set_ylabel('Depth from illuminated face (nm)')
    if ims:
        cb = fig.colorbar(ims[-1], ax=axs, pad=0.012, fraction=0.028)
        cb.set_label(r'$Q_h$ (W m$^{-3}$, unit incident field)', fontsize=6.5)
        cb.ax.tick_params(labelsize=6)
    for ax, s in zip(axs, ['(a)', '(b)', '(c)', '(d)']):
        ax.text(-0.02, 1.06, s, transform=ax.transAxes, fontweight='bold',
                fontsize=9, va='bottom', ha='left', color=S.INK)
    S.save(fig, os.path.join(OUT_SI, 'figS6_generation_map'))
    plt.close(fig)


if __name__ == '__main__':
    fig_band_alignment();  print('fig5  band alignment (MAIN)   OK')
    fig_generation_map();  print('figS6 G(z,lambda) map (SI)    OK')
