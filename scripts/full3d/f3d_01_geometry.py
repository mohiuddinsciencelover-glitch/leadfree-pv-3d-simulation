"""FULL-3D stage 01 -- parametric textured geometry.

Builds the planar stack (identical thicknesses to the parent study) plus a
2D-periodic nanocone array on the FTO front surface. One cone per unit cell
+ periodic BCs == an infinite square array of pitch = PITCH.

Object list (7 objects -> 7 domains after Form Union):
    blk_au, blk_htl, blk_abs, blk_etl, blk_fto, cone_tex, air_carved

`air_carved` is built as an explicit boolean Difference (air block MINUS
cone) so that air and cone never overlap. This matters: it keeps every
domain unambiguously identifiable by a coordinate box, which is why this
script uses NAMED COORDINATE SELECTIONS everywhere instead of hard-coded
domain indices. The parent (planar) project hard-codes indices like
ht.selection().set(1,2,3,4,5); that breaks the moment a texture adds a
domain, so it is deliberately not done here.

Idempotent: re-running edits in place rather than duplicating features.
Run:  python3 full3d/build/f3d_01_geometry.py
"""
import sys, os, jpype
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
import mph

C.banner()
os.makedirs(C.MODELS, exist_ok=True)

L = C.LAYERS
T = C.TEXTURE
# z-interfaces of the flat stack
z_au, z_htl = L['h_au'], L['h_au'] + L['h_htl']
z_abs = z_htl + L['h_abs']
z_etl = z_abs + L['h_etl']
z_fto = z_etl + L['h_fto']                 # top of flat FTO = texture base
z_apex = z_fto + T['h']                    # cone apex
z_air = z_apex + C.AIR_CLEARANCE           # top of physical air
z_top = z_air + C.PML_THICKNESS            # top of PML (domain boundary)
print(f'stack z-interfaces (nm): Au {z_au} | HTL {z_htl} | abs {z_abs} | '
      f'ETL {z_etl} | FTO {z_fto} | apex {z_apex} | air {z_air} | '
      f'PML top {z_top}')

client = mph.start(cores=C.CORES)
model = client.create('f3d')
java = model.java
java.component().create('comp1', True)
comp = java.component('comp1')
comp.geom().create('geom1', jpype.JInt(3))
geom = comp.geom('geom1')
geom.lengthUnit('nm')

# ------------------------------------------------------------ parameters
p = java.param()
PARAMS = {
    'pitch':   f'{C.PITCH}[nm]',
    'h_au':    f'{L["h_au"]}[nm]',
    'h_htl':   f'{L["h_htl"]}[nm]',
    'h_abs':   f'{L["h_abs"]}[nm]',
    'h_etl':   f'{L["h_etl"]}[nm]',
    'h_fto':   f'{L["h_fto"]}[nm]',
    'tex_h':   f'{T["h"]}[nm]',
    'tex_rb':  f'{T["r_base"]}[nm]',
    'tex_rt':  f'{T["r_top"]}[nm]',
    'h_clear': f'{C.AIR_CLEARANCE}[nm]',
    'h_pml':   f'{C.PML_THICKNESS}[nm]',
}
for k, v in PARAMS.items():
    p.set(k, v)
print('parameters set:', ', '.join(f'{k}={v}' for k, v in PARAMS.items()))

# -------------------------------------------------------------- geometry
existing = set(str(t) for t in geom.feature().tags())

def block(tag, z0_expr, dz_expr):
    if tag not in existing:
        b = geom.create(tag, 'Block')
    else:
        b = geom.feature(tag)
    b.set('size', ['pitch', 'pitch', dz_expr])
    b.set('pos', ['0', '0', z0_expr])
    return b

block('blk_au',  '0',                              'h_au')
block('blk_htl', 'h_au',                           'h_htl')
block('blk_abs', 'h_au+h_htl',                     'h_abs')
block('blk_etl', 'h_au+h_htl+h_abs',               'h_etl')
block('blk_fto', 'h_au+h_htl+h_abs+h_etl',         'h_fto')
# raw air block (will have the cone carved out of it)
block('blk_air_raw', 'h_au+h_htl+h_abs+h_etl+h_fto', 'tex_h+h_clear')
# PML cap: absorbs every outgoing diffracted order at any angle
block('blk_pml', 'h_au+h_htl+h_abs+h_etl+h_fto+tex_h+h_clear', 'h_pml')

if C.TEXTURED:
    # cone texture, centred laterally, sitting on the FTO top face
    if 'cone_tex' not in existing:
        cone = geom.create('cone_tex', 'Cone')
    else:
        cone = geom.feature('cone_tex')
    cone.set('r', 'tex_rb')
    cone.set('h', 'tex_h')
    # truncated-cone support: r_top=0 -> sharp apex
    try:
        cone.set('specifytop', 'radius')
        cone.set('rtop', 'tex_rt')
    except Exception as e:
        print('  (cone top-radius property fallback:', str(e)[:70], ')')
    cone.set('pos', ['pitch/2', 'pitch/2', 'h_au+h_htl+h_abs+h_etl+h_fto'])
    cone.set('axistype', 'z')

    # carve the cone out of the air so the two never overlap
    if 'air_carved' not in existing:
        dif = geom.create('air_carved', 'Difference')
    else:
        dif = geom.feature('air_carved')
    dif.selection('input').set(['blk_air_raw'])
    dif.selection('input2').set(['cone_tex'])
    dif.set('keepsubtract', True)     # keep the cone as its own object
else:
    # PLANAR REFERENCE: no cone, and therefore nothing to carve out of the
    # air. Everything else -- thicknesses, materials, mesh rule, boundary
    # conditions, solver -- is identical to the textured run, which is the
    # whole point of running the reference in this folder rather than
    # comparing against the parent study.
    for stale in ('air_carved', 'cone_tex'):
        if stale in existing:
            geom.feature().remove(stale)
            print(f'planar variant: removed {stale}')

geom.run()
nd = geom.getNDomains()
expect = 8 if C.TEXTURED else 7
print(f'geometry built: {nd} domains (expect {expect})')

# ------------------------------------------- named coordinate selections
sel = comp.selection()
existing_sel = set(str(t) for t in sel.tags())
EPS = 1.0     # nm tolerance

def box_sel(tag, label, zmin, zmax, xpad=EPS, dim=3):
    """Domain (or boundary) selection by bounding box, 'allvertices' rule:
    an entity is selected only if it lies ENTIRELY inside the box."""
    if tag in existing_sel:
        s = sel(tag) if callable(sel) else sel.get(tag)
    else:
        s = sel.create(tag, 'Box')
    s.label(label)
    s.set('entitydim', jpype.JInt(dim))
    s.set('xmin', -xpad); s.set('xmax', C.PITCH + xpad)
    s.set('ymin', -xpad); s.set('ymax', C.PITCH + xpad)
    s.set('zmin', zmin);  s.set('zmax', zmax)
    s.set('condition', 'allvertices')
    return s

z_apex_eff = z_apex if C.TEXTURED else z_fto     # no cone -> FTO top is the top
box_sel('sel_au',  'Au back contact',   -EPS,        z_au + EPS)
box_sel('sel_htl', 'HTL',               z_au - EPS,  z_htl + EPS)
box_sel('sel_abs', 'Absorber',          z_htl - EPS, z_abs + EPS)
box_sel('sel_etl', 'ETL (TiO2)',        z_abs - EPS, z_etl + EPS)
# FTO selection spans flat FTO *and* the cone (same material). In the planar
# variant it is the flat FTO alone, because the box now stops at the FTO top.
box_sel('sel_fto', 'FTO + cone texture', z_etl - EPS, z_apex_eff + EPS)
# the cone alone, identified by its narrower lateral footprint. In the planar
# variant this selects nothing, which is correct and is handled downstream
# (no cone mesh-size feature, no cone absorptance column).
cone_pad = C.PITCH / 2 - T['r_base'] - EPS      # lateral gap outside cone base
sel_cone = box_sel('sel_cone', 'Cone texture only', z_fto - EPS, z_apex + EPS,
                   xpad=-cone_pad)
# air = everything above the FTO top face, minus the cone
box_sel('sel_air_all', 'Air incl. cone region', z_fto - EPS, z_air + EPS)
box_sel('sel_pml', 'PML cap', z_air - EPS, z_top + EPS)
if 'sel_air' not in existing_sel:
    d = sel.create('sel_air', 'Difference')
else:
    d = sel.get('sel_air')
d.label('Air (cone carved out)')
d.set('entitydim', jpype.JInt(3))
# NB: a Difference *selection* uses add/subtract -- unlike a Difference
# *geometry* feature, which uses input/input2. Easy trap.
d.set('add', ['sel_air_all'])
d.set('subtract', ['sel_cone'])

# boundary selections needed later (port, PEC, periodicity)
box_sel('sel_bnd_top',    'Top boundary (PML outer face)', z_top - EPS, z_top + EPS, dim=2)
box_sel('sel_bnd_bottom', 'Bottom boundary (PEC)',     -EPS,        EPS,        dim=2)
# air/PML interface: flux plane for the independent energy-conservation
# check in stage 05 (net downward Poynting flux here must equal the total
# volume-integrated absorbed power, since the PEC back face blocks
# transmission).
box_sel('sel_bnd_airpml', 'Air/PML interface (flux plane)',
        z_air - EPS, z_air + EPS, dim=2)


def side_sel(tag, label, xr, yr):
    """Side-face selection spanning the whole stack height."""
    if tag in existing_sel:
        s = sel.get(tag)
    else:
        s = sel.create(tag, 'Box')
    s.label(label)
    s.set('entitydim', jpype.JInt(2))
    s.set('xmin', xr[0]); s.set('xmax', xr[1])
    s.set('ymin', yr[0]); s.set('ymax', yr[1])
    s.set('zmin', -EPS);  s.set('zmax', z_top + EPS)
    s.set('condition', 'allvertices')
    return s


FULL = (-EPS, C.PITCH + EPS)
side_sel('sel_bnd_xmin', 'x = 0 faces',     (-EPS, EPS), FULL)
side_sel('sel_bnd_xmax', 'x = pitch faces', (C.PITCH - EPS, C.PITCH + EPS), FULL)
side_sel('sel_bnd_ymin', 'y = 0 faces',     FULL, (-EPS, EPS))
side_sel('sel_bnd_ymax', 'y = pitch faces', FULL, (C.PITCH - EPS, C.PITCH + EPS))

# A COMSOL PeriodicCondition takes ONE selection containing BOTH faces of the
# pair, so union the opposing faces.
for tag, label, parts in [
        ('sel_bnd_xpair', 'x periodic pair', ['sel_bnd_xmin', 'sel_bnd_xmax']),
        ('sel_bnd_ypair', 'y periodic pair', ['sel_bnd_ymin', 'sel_bnd_ymax'])]:
    u = sel.create(tag, 'Union') if tag not in existing_sel else sel.get(tag)
    u.label(label)
    u.set('entitydim', jpype.JInt(2))
    try:
        u.set('input', parts)
    except Exception:
        u.set('add', parts)     # property name differs by selection type

model.save(C.MODEL_PATH)
print(f'saved -> {C.MODEL_PATH}')

# ------------------------------------------------------------ diagnostics
print('\n--- selection contents (domain/boundary indices) ---')
for tag in ['sel_au', 'sel_htl', 'sel_abs', 'sel_etl', 'sel_fto', 'sel_cone',
            'sel_air', 'sel_pml', 'sel_bnd_top', 'sel_bnd_bottom',
            'sel_bnd_airpml',
            'sel_bnd_xpair', 'sel_bnd_ypair']:
    try:
        ents = list(comp.selection(tag).entities(jpype.JInt(
            2 if 'bnd' in tag else 3)))
        print(f'  {tag:16s} -> {ents}')
    except Exception as e:
        print(f'  {tag:16s} -> ERR {str(e)[:60]}')
print('\nSTAGE 01 DONE', flush=True)
