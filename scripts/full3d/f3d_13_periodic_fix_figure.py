"""FULL-3D stage 13 -- the periodic-mesh fix, as a figure.

Plots absorber absorptance against mesh size at 700 nm, before and after the
Floquet-paired faces were forced to carry identical meshes. Before the fix the
answer wanders by tens of percent across meshes that differ by ~2 %; after it,
successive meshes agree to 0.03 %. That contrast is the mesh-convergence
evidence for the study and belongs in the supplementary material.

Two series, one y-axis, colour plus dash so it survives greyscale printing.

Run:  python3 full3d/build/f3d_13_periodic_fix_figure.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import matplotlib.pyplot as plt
import config as C
import f3d_style as S

S.apply()
FIGDIR = os.path.join(C.RESULTS, 'figures')
os.makedirs(FIGDIR, exist_ok=True)

BEFORE = os.path.join(C.RESULTS, f'f3d_{C.ABSORBER}_convergence_700nm.csv')
AFTER = os.path.join(C.RESULTS, f'f3d_{C.ABSORBER}_convergence_700nm_fixed.csv')
for p in (BEFORE, AFTER):
    if not os.path.exists(p):
        raise SystemExit(f'missing {p}')

b = np.genfromtxt(BEFORE, delimiter=',', names=True)
a = np.genfromtxt(AFTER, delimiter=',', names=True)

fig, (ax, ax2) = plt.subplots(
    2, 1, figsize=(S.COL1, 3.2), sharex=True,
    gridspec_kw=dict(height_ratios=[1.6, 1], hspace=0.14))

for arr, role, lab in ((b, 'FTO_total', 'Mismatched periodic faces'),
                       (a, 'absorber', 'Identical periodic faces')):
    ax.plot(np.atleast_1d(arr['n_elem']) / 1e3,
            100 * np.atleast_1d(arr['A_absorber']),
            marker='o', markersize=3.2, markeredgewidth=0,
            label=lab, **S.style_line(role))
ax.set_ylabel('Absorber absorptance (%)')
ax.set_ylim(40, 85)
ax.legend(loc='lower left')

for arr, role in ((b, 'FTO_total'), (a, 'absorber')):
    ax2.plot(np.atleast_1d(arr['n_elem']) / 1e3,
             100 * np.atleast_1d(arr['energy_residual']),
             marker='o', markersize=3.2, markeredgewidth=0,
             **S.style_line(role))
ax2.axhline(0, color=S.INK_2, linewidth=0.5)
ax2.set_ylabel('Energy residual (%)')
ax2.set_xlabel(r'Mesh elements ($\times 10^3$)')

# The point the caption has to make: the residual barely moved while the
# absorptance collapsed, so a global conservation check cannot detect this.
ax2.annotate('residual stays ~1 %\nwhile absorptance falls 36 %',
             xy=(0.03, 0.62), xycoords='axes fraction', fontsize=6,
             color=S.INK_2, ha='left', va='center')

out = S.save(fig, os.path.join(FIGDIR, 'figS_periodic_mesh_fix'))
print('wrote:')
for o in out:
    print('  ', o)

print('\nnumbers behind the figure:')
for name, arr in (('mismatched', b), ('identical ', a)):
    aa = 100 * np.atleast_1d(arr['A_absorber'])
    ne = np.atleast_1d(arr['n_elem'])
    spread = (aa.max() - aa.min()) / aa.mean() * 100
    dn = (ne.max() - ne.min()) / ne.mean() * 100
    print(f'  {name}: A_abs {aa.min():.2f}-{aa.max():.2f} %  '
          f'(spread {spread:.2f} % of mean) over a {dn:.2f} % change in '
          f'element count')
print('STAGE 13 DONE', flush=True)
