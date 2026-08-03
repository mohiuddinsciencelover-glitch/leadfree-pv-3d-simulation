"""Figure style for IEEE Journal of Photovoltaics submission.

IEEE publishes graphics at one column (3.5 in / 21 picas) or two columns
(7.16 in / 43 picas), and requires at least 300 dpi -- 600 dpi for line art.
Figures are therefore drawn AT final printed size, never scaled afterwards:
scaling a figure is what produces the 5 pt axis labels reviewers complain
about. Everything is exported as vector PDF (what to submit) plus a 600 dpi
PNG (for quick viewing and for the docx).

COLOR. The categorical palette is the validated default from the data-viz
reference, used in its fixed slot order, and it was checked with the
validator rather than by eye: 6 slots pass the lightness band, chroma floor,
colour-vision separation and normal-vision floor on a light surface. Three
slots fall below 3:1 contrast against white, which obliges "relief" --
visible labels rather than colour alone. That is satisfied here twice over,
because every series also carries its own DASH PATTERN. The dash is not
decoration: an IEEE paper gets printed in greyscale, and colour-only
encoding does not survive that.

No chart here uses two y-axes. Where two quantities of different scale need
comparing they get stacked panels sharing one x-axis instead.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from cycler import cycler

# ------------------------------------------------------------------ sizes
COL1 = 3.5      # in, IEEE single column (21 picas)
COL2 = 7.16     # in, IEEE double column (43 picas)
DPI = 600       # line art

# ----------------------------------------------------------- categorical
# Validated default palette, fixed slot order. Never cycled, never reordered:
# a series keeps its colour even when other series are added or removed.
PALETTE = ['#2a78d6',   # 1 blue
           '#eb6834',   # 2 orange
           '#1baf7a',   # 3 aqua
           '#eda100',   # 4 yellow
           '#e87ba4',   # 5 magenta
           '#008300']   # 6 green
# Secondary encoding, so identity survives greyscale printing and CVD.
DASHES = [(None, None), (4, 1.5), (1, 1.2), (5, 1.5, 1, 1.5),
          (3, 1, 1, 1, 1, 1), (7, 2)]

INK = '#0b0b0b'          # text-primary
INK_2 = '#52514e'        # text-secondary
GRID = '#d9d8d4'

# Fixed role -> slot map, so the same physical quantity is the same colour in
# every figure of the paper.
ROLE = {
    'absorber':  0,
    'FTO_total': 1,
    'TiO2':      2,
    'HTL':       3,
    'Au':        4,
    'R':         5,
    'textured':  0,
    'planar':    1,
}
LABEL = {
    'absorber':  'Absorber (useful)',
    'FTO_total': 'FTO + texture',
    'TiO2':      r'TiO$_2$ ETL',
    'HTL':       'Spiro HTL',
    'Au':        'Au contact',
    'R':         'Reflected',
    'textured':  'Textured',
    'planar':    'Planar reference',
}


def color(role):
    return PALETTE[ROLE[role] % len(PALETTE)]


def dash(role):
    return DASHES[ROLE[role] % len(DASHES)]


def style_line(role):
    """Colour + dash + width for one series, by role."""
    d = dash(role)
    kw = dict(color=color(role), linewidth=1.1, solid_capstyle='round')
    if d[0] is not None:
        kw['dashes'] = list(d)
    return kw


def apply():
    """Install the rcParams. Call once before creating any figure."""
    plt.rcParams.update({
        # IEEE body text is Times; a serif figure font matches the page.
        'font.family': 'serif',
        'font.serif': ['DejaVu Serif', 'Times New Roman', 'Nimbus Roman',
                       'Liberation Serif'],
        'mathtext.fontset': 'dejavuserif',
        'font.size': 8,
        'axes.labelsize': 8,
        'axes.titlesize': 8,
        'xtick.labelsize': 7,
        'ytick.labelsize': 7,
        'legend.fontsize': 7,
        'figure.dpi': 120,
        'savefig.dpi': DPI,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.02,
        # Recessive frame and grid: the data should be the darkest thing.
        'axes.edgecolor': INK_2,
        'axes.linewidth': 0.6,
        'axes.labelcolor': INK,
        'axes.grid': True,
        'grid.color': GRID,
        'grid.linewidth': 0.4,
        'grid.alpha': 1.0,
        'axes.axisbelow': True,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'xtick.color': INK_2,
        'ytick.color': INK_2,
        'xtick.direction': 'out',
        'ytick.direction': 'out',
        'xtick.major.width': 0.6,
        'ytick.major.width': 0.6,
        'xtick.major.size': 2.5,
        'ytick.major.size': 2.5,
        'legend.frameon': False,
        'legend.handlelength': 2.4,
        'legend.columnspacing': 1.0,
        'legend.labelspacing': 0.3,
        'lines.linewidth': 1.1,
        'lines.markersize': 3.0,
        'axes.prop_cycle': cycler(color=PALETTE),
        'pdf.fonttype': 42,        # embed TrueType; IEEE rejects Type 3
        'ps.fonttype': 42,
    })


def save(fig, path_noext, formats=('pdf', 'png')):
    """Write the figure at final size in submission + preview formats."""
    out = []
    for fmt in formats:
        p = f'{path_noext}.{fmt}'
        fig.savefig(p, format=fmt)
        out.append(p)
    plt.close(fig)
    return out
