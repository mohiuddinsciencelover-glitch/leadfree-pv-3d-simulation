"""FULL-3D stage 11 -- IEEE JPV figures from the absorptance sweep.

Drawn at final printed size (3.5 in single column / 7.16 in double) so nothing
is scaled afterwards, and exported as vector PDF for submission plus 600 dpi
PNG for preview. Style, palette and the fixed role->colour map live in
f3d_style.py.

Figures
  1  layer-resolved absorptance of the textured cell -- where every photon goes
  2  textured vs planar absorber absorptance, with the difference below
  3  AM1.5G-weighted current budget, planar vs textured
  4  energy-conservation residual vs wavelength   (QC / supplementary)
  5  mesh convergence                             (QC / supplementary)

Figures 2 and 3 are skipped when the planar reference has not been run yet, so
this is safe to call on partial results while the sweep is still going.

Run:  python3 full3d/build/f3d_11_figures.py
"""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import matplotlib.pyplot as plt
import config as C
import f3d_style as S
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f3d_10_photocurrent import load_spectrum, photon_flux, budget

S.apply()
FIGDIR = os.path.join(C.RESULTS, 'figures')
os.makedirs(FIGDIR, exist_ok=True)

TEX = os.path.join(C.RESULTS, f'f3d_{C.ABSORBER}_absorptance_{C.PROFILE}.csv')
PLN = os.path.join(C.RESULTS,
                   f'f3d_{C.ABSORBER}_absorptance_{C.PROFILE}_planar.csv')
ABS_LABEL = {'FASnI3': r'FASnI$_3$', 'BaZrS3': r'BaZrS$_3$',
             'Cs2AgBiBr6': r'Cs$_2$AgBiBr$_6$',
             'Cu2AgBiI6': r'Cu$_2$AgBiI$_6$'}.get(C.ABSORBER, C.ABSORBER)
written = []


def fig1_layers(spec):
    """Where every incident photon ends up, wavelength by wavelength."""
    fig, ax = plt.subplots(figsize=(S.COL1, 2.5))
    lam = spec['lambda_nm']
    series = [('absorber', 'A_absorber'), ('FTO_total', 'A_FTO_total'),
              ('TiO2', 'A_TiO2'), ('HTL', 'A_HTL'), ('Au', 'A_Au'),
              ('R', 'R_implied')]
    for role, col in series:
        if col not in spec:
            continue
        lab = (f'{ABS_LABEL} (useful)' if role == 'absorber'
               else S.LABEL[role])
        ax.plot(lam, 100 * spec[col], label=lab, **S.style_line(role))
    ax.set_xlabel('Wavelength (nm)')
    ax.set_ylabel('Fraction of incident power (%)')
    ax.set_xlim(lam.min(), lam.max())
    ax.set_ylim(0, 100)
    ax.legend(ncol=2, loc='upper center', bbox_to_anchor=(0.5, 1.32))
    written.extend(S.save(fig, os.path.join(FIGDIR, 'fig1_layer_absorptance')))


def fig2_compare(t, p):
    """Textured vs planar, with the difference in its own panel.

    Two panels sharing one x-axis rather than a second y-axis: absorptance
    and its change have different scales, and a dual-axis plot invites the
    reader to compare two arbitrary scalings as if they were one.
    """
    fig, (ax, ax2) = plt.subplots(
        2, 1, figsize=(S.COL1, 3.1), sharex=True,
        gridspec_kw=dict(height_ratios=[2.4, 1], hspace=0.12))
    for role, spec in (('planar', p), ('textured', t)):
        ax.plot(spec['lambda_nm'], 100 * spec['A_absorber'],
                label=S.LABEL[role], **S.style_line(role))
    ax.set_ylabel(f'{ABS_LABEL} absorptance (%)')
    ax.set_ylim(0, 100)
    ax.legend(loc='lower left')

    lam = t['lambda_nm']
    pa = np.interp(lam, p['lambda_nm'], p['A_absorber'])
    d = 100 * (t['A_absorber'] - pa)
    ax2.axhline(0, color=S.INK_2, linewidth=0.5)
    ax2.plot(lam, d, color=S.color('textured'), linewidth=1.1)
    ax2.fill_between(lam, 0, d, color=S.color('textured'), alpha=0.16,
                     linewidth=0)
    ax2.set_ylabel('Gain (pp)')
    ax2.set_xlabel('Wavelength (nm)')
    ax2.set_xlim(lam.min(), lam.max())
    written.extend(S.save(fig, os.path.join(FIGDIR, 'fig2_textured_vs_planar')))


def fig3_budget(bt, bp):
    """AM1.5G-weighted current budget: a closed accounting of the photons."""
    keys = ['A_absorber', 'A_FTO_total', 'A_TiO2', 'A_HTL', 'A_Au', 'R']
    roles = ['absorber', 'FTO_total', 'TiO2', 'HTL', 'Au', 'R']
    labels = [f'{ABS_LABEL}\n(useful)', 'FTO +\ntexture', r'TiO$_2$',
              'Spiro', 'Au', 'Reflected']
    x = np.arange(len(keys))
    w = 0.38
    fig, ax = plt.subplots(figsize=(S.COL1, 2.3))
    # A 2 pt surface gap between adjacent bars, per the mark spec.
    ax.bar(x - w / 2 - 0.012, [bp.get(k, 0) for k in keys], w,
           label='Planar', color=S.color('planar'), linewidth=0)
    ax.bar(x + w / 2 + 0.012, [bt.get(k, 0) for k in keys], w,
           label='Textured', color=S.color('textured'), linewidth=0)
    for xi, k in zip(x, keys):
        v = bt.get(k, 0)
        ax.text(xi + w / 2 + 0.012, v, f'{v:.1f}', ha='center', va='bottom',
                fontsize=6, color=S.INK)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=6.5)
    ax.set_ylabel(r'Equivalent current (mA cm$^{-2}$)')
    ax.legend(loc='upper right')
    ax.grid(axis='x', visible=False)
    written.extend(S.save(fig, os.path.join(FIGDIR, 'fig3_current_budget')))


def fig4_residual(spec):
    """Energy conservation vs wavelength -- the study's own accuracy metric."""
    if 'energy_residual' not in spec:
        return
    fig, ax = plt.subplots(figsize=(S.COL1, 1.9))
    lam, r = spec['lambda_nm'], 100 * spec['energy_residual']
    ax.axhspan(-2, 2, color=S.GRID, alpha=0.6, linewidth=0,
               label='acceptance band')
    ax.axhline(0, color=S.INK_2, linewidth=0.5)
    ax.plot(lam, r, color=S.color('absorber'), linewidth=1.1,
            marker='o', markersize=2.2, markeredgewidth=0)
    ax.set_xlabel('Wavelength (nm)')
    ax.set_ylabel('Energy residual (%)')
    ax.set_xlim(lam.min(), lam.max())
    lim = max(2.5, 1.25 * np.nanmax(np.abs(r)))
    ax.set_ylim(-lim, lim)
    ax.legend(loc='upper right')
    written.extend(S.save(fig, os.path.join(FIGDIR, 'fig4_energy_residual')))


def fig5_convergence():
    """Absorber absorptance vs mesh density, per wavelength studied."""
    import re
    files = sorted(glob.glob(os.path.join(
        C.RESULTS, f'f3d_{C.ABSORBER}_convergence_*.csv')))
    # Convergence data recorded BEFORE the periodic-mesh fix is not
    # convergence data -- it is the bug, and it lives in its own figure
    # (f3d_13). Mixing it in here put two series a wavelength apart on the
    # same axes, both legended "700 nm", which reads as one condition giving
    # two answers. Prefer the post-fix files whenever any exist.
    fixed = [f for f in files if '_fixed' in os.path.basename(f)]
    if fixed:
        superseded = [os.path.basename(f) for f in files if f not in fixed]
        if superseded:
            print(f'  fig5: using post-fix convergence only; ignoring '
                  f'{superseded} (pre-periodic-fix)')
        files = fixed
    if not files:
        return
    fig, ax = plt.subplots(figsize=(S.COL1, 2.2))
    for i, f in enumerate(files):
        d = np.genfromtxt(f, delimiter=',', names=True)
        if d.size < 2:
            continue
        m = re.search(r'_(\d+)nm', os.path.basename(f))
        lam = m.group(1) if m else '?'
        role = ['absorber', 'FTO_total', 'TiO2', 'HTL'][i % 4]
        ref = d['A_absorber'][-1]
        ax.plot(d['n_elem'] / 1e3, 100 * (d['A_absorber'] - ref) / ref,
                marker='o', markersize=3, markeredgewidth=0,
                label=f'{lam} nm', **S.style_line(role))
    ax.axhline(0, color=S.INK_2, linewidth=0.5)
    ax.axhspan(-1, 1, color=S.GRID, alpha=0.6, linewidth=0,
               label=r'$\pm$1 % band')
    ax.set_xlabel(r'Mesh elements ($\times 10^3$)')
    ax.set_ylabel('Deviation from finest (%)')
    # Keep the +/-1 % acceptance band visible even when the data sits on zero,
    # which is the point of the figure once the model is converged.
    lo, hi = ax.get_ylim()
    ax.set_ylim(min(lo, -1.6), max(hi, 1.6))
    ax.legend(loc='best')
    written.extend(S.save(fig, os.path.join(FIGDIR, 'fig5_mesh_convergence')))


def fig6_fieldmap(lam=700):
    """Absorbed power on a vertical cut -- the evidence that this is 3D.

    Sequential data, so a single hue light->dark, never a rainbow: the
    quantity is magnitude with no meaningful midpoint. Plotted on a shared
    log-normalised scale when both variants exist, because the two maps are
    only comparable if the colour means the same thing in each.
    """
    from matplotlib.colors import LogNorm
    maps = []
    for variant in ('planar', 'textured'):
        p = os.path.join(C.RESULTS,
                         f'f3d_{C.ABSORBER}_{variant}_Qmap_{int(lam)}nm.npz')
        if os.path.exists(p):
            maps.append((variant, np.load(p, allow_pickle=True)))
    if not maps:
        return
    finite = np.concatenate([d['Qh'][np.isfinite(d['Qh'])].ravel()
                             for _, d in maps])
    finite = finite[finite > 0]
    if finite.size == 0:
        return
    vmax = np.percentile(finite, 99.8)
    norm = LogNorm(vmin=max(vmax / 1e4, finite.min()), vmax=vmax)

    fig, axes = plt.subplots(1, len(maps), figsize=(S.COL1, 2.4),
                             sharey=True, constrained_layout=True)
    axes = np.atleast_1d(axes)
    for ax, (variant, d) in zip(axes, maps):
        Q = np.ma.masked_invalid(d['Qh']).T
        im = ax.pcolormesh(d['x_nm'], d['z_nm'], Q, norm=norm,
                           cmap='magma', shading='nearest', rasterized=True)
        # Layer boundaries, so the reader can see WHICH layer is absorbing.
        z = 0.0
        for t in d['layers']:
            z += float(t)
            ax.axhline(z, color='w', linewidth=0.4, alpha=0.55)
        ax.set_title(S.LABEL[variant], fontsize=7)
        ax.set_xlabel('x (nm)')
        ax.set_xticks([0, C.PITCH / 2, C.PITCH])
        ax.grid(False)
    axes[0].set_ylabel('z (nm)')
    cb = fig.colorbar(im, ax=list(axes), shrink=0.9, pad=0.02)
    cb.set_label(r'Absorbed power density (W m$^{-3}$)', fontsize=7)
    cb.ax.tick_params(labelsize=6)
    written.extend(S.save(fig, os.path.join(FIGDIR, f'fig6_qmap_{int(lam)}nm')))


def fig7_generation():
    """Broadband G(z) through the absorber -- the hand-off to transport.

    This is the quantity the drift-diffusion model actually consumes, so it is
    where an optical gain either does or does not become a device gain. Depth
    runs with the optical path: light arrives through the FTO/ETL at the top of
    the stack, so generation is highest on the ETL side and decays towards the
    HTL.
    """
    curves = []
    for variant in ('planar', 'textured'):
        p = os.path.join(C.RESULTS,
                         f'f3d_{C.ABSORBER}_{variant}_Gz_AM15G.csv')
        if os.path.exists(p):
            d = np.genfromtxt(p, delimiter=',', names=True)
            if d.size > 1:
                curves.append((variant, d))
    if not curves:
        return

    fig, ax = plt.subplots(figsize=(S.COL1, 2.4))
    for variant, d in curves:
        # Plot depth measured from the illuminated (ETL) face, which is how a
        # device physicist reads a generation profile.
        z_nm = d['z_m'] * 1e9
        depth = z_nm.max() - z_nm
        ax.plot(depth, d['G_1_per_m3_s'], label=S.LABEL[variant],
                **S.style_line(variant))
    ax.set_xlabel('Depth into absorber from the illuminated face (nm)')
    ax.set_ylabel(r'Generation rate (m$^{-3}$ s$^{-1}$)')
    ax.set_yscale('log')
    ax.set_xlim(0, C.LAYERS['h_abs'])
    ax.legend(loc='upper right')
    written.extend(S.save(fig, os.path.join(FIGDIR, 'fig7_generation_profile')))


if __name__ == '__main__':
    if not os.path.exists(TEX):
        raise SystemExit(f'no textured spectrum yet: {TEX}')
    t = load_spectrum(TEX)
    lam_nm, phi = photon_flux()
    fig1_layers(t)
    fig4_residual(t)
    fig5_convergence()
    for lam in (700, 550, 850):
        fig6_fieldmap(lam)
    fig7_generation()
    if os.path.exists(PLN):
        p = load_spectrum(PLN)
        fig2_compare(t, p)
        fig3_budget(budget(t, lam_nm, phi), budget(p, lam_nm, phi))
    else:
        print(f'planar reference not found ({PLN}); '
              f'skipping the comparison figures')
    print('wrote:')
    for w in written:
        print('  ', w)
    print('STAGE 11 DONE', flush=True)
