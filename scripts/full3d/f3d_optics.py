"""Optical constants of every layer, evaluated in numpy -- outside COMSOL.

Two jobs:

1. MESH SIZING. Element size must be set per material from the wavelength
   IN that material, lam/(n*ppw), so the mesh is driven by real dispersion
   rather than one global hmax. That needs n,k in Python before the model
   is built.

2. VERIFICATION. Project memory records that model.evaluate() misreports
   interpolation state, so anything that needs to be trusted is read from
   the source CSVs here instead of asked of COMSOL.

Every material defined in f3d_03_materials.py has an entry here, and the
definitions are kept deliberately identical to that script -- if one is
edited the other must be too.
"""
import os
import numpy as np

import config as C

_CACHE = {}


def _table(path):
    """Load a (lambda_um, n, k) CSV, tolerating a header line."""
    if path not in _CACHE:
        d = np.loadtxt(path, delimiter=',', comments=('#', '%'), skiprows=1)
        _CACHE[path] = d
    return _CACHE[path]


def _interp_nk(path, lam_nm):
    d = _table(path)
    lam_um = np.asarray(lam_nm, dtype=float) / 1000.0
    # 'const' extrapolation, matching the COMSOL interpolation functions
    n = np.interp(lam_um, d[:, 0], d[:, 1])
    k = np.interp(lam_um, d[:, 0], d[:, 2])
    return n, k


def tio2_sellmeier(lam_nm):
    """Devore 1951 Sellmeier, clamped below C.TIO2_LAMBDA_MIN.

    The pole is at 283 nm, so evaluating the raw expression at the 300 nm
    end of the grid gives n = 5.58 -- about double any measured anatase
    value, and far outside the fit's validity. Clamping the argument at
    400 nm holds n at 3.00 below that, matching the 'const' extrapolation
    COMSOL applies to every tabulated material in this model. The COMSOL
    expression in f3d_03_materials.py applies the SAME clamp; the two must
    be edited together.

    k = 0 throughout still ignores TiO2's own absorption below ~380 nm, an
    approximation inherited from the planar study and disclosed as such.
    """
    lam = np.maximum(np.asarray(lam_nm, dtype=float), C.TIO2_LAMBDA_MIN)
    lam_um2 = (lam / 1000.0) ** 2
    return np.sqrt(5.913 + 0.2441 / (lam_um2 - 0.0803))


def nk(material, lam_nm):
    """Complex refractive index (n, k) of a named material at lam [nm]."""
    if material == 'au':
        return _interp_nk(C.AU_NK, lam_nm)
    if material == 'abs':
        return _interp_nk(C.NK[C.ABSORBER], lam_nm)
    if material == 'etl':
        return tio2_sellmeier(lam_nm), np.zeros_like(np.asarray(lam_nm, float))
    if material == 'fto':
        if not C.FTO_IS_PLACEHOLDER:
            return _interp_nk(C.FTO_NK_CSV, lam_nm)
        o = np.ones_like(np.asarray(lam_nm, dtype=float))
        return C.FTO_PLACEHOLDER['n'] * o, C.FTO_PLACEHOLDER['k'] * o
    if material == 'htl':
        o = np.ones_like(np.asarray(lam_nm, dtype=float))
        return C.SPIRO['n'] * o, C.SPIRO['k'] * o
    if material in ('air', 'pml'):
        o = np.ones_like(np.asarray(lam_nm, dtype=float))
        return o, np.zeros_like(o)
    raise KeyError(material)


def n_eff(material, lam_nm):
    """|n_complex| -- the quantity that sets the local wavelength scale.

    Using sqrt(n^2 + k^2) rather than Re(n) matters for the Au contact,
    where k dominates: the field there varies on the skin-depth scale, not
    on lam/Re(n), so Re(n) alone would badly under-refine the metal.
    """
    n, k = nk(material, lam_nm)
    return float(np.sqrt(np.asarray(n) ** 2 + np.asarray(k) ** 2))


def skin_depth(material, lam_nm):
    """Field 1/e depth, nm. Infinite for a lossless material."""
    _, k = nk(material, lam_nm)
    k = float(np.asarray(k))
    if k <= 1e-12:
        return float('inf')
    return float(lam_nm) / (4.0 * np.pi * k)


# Which named selection each material occupies. sel_fto covers the flat FTO
# AND the cone, because they are one material by construction.
SELECTIONS = {
    'au':  'sel_au',
    'htl': 'sel_htl',
    'abs': 'sel_abs',
    'etl': 'sel_etl',
    'fto': 'sel_fto',
    'air': 'sel_air',
    'pml': 'sel_pml',
}

# Only the transparent superstrate is size-capped. Everything else follows the
# points-per-wavelength criterion, so ppw genuinely controls accuracy where the
# absorbed power is computed.
CAPPED_MATERIALS = {'air', 'pml'}

# Finite layer thicknesses [nm]; air/PML are open regions and excluded.
LAYER_THICKNESS = {
    'au':  C.LAYERS['h_au'],
    'htl': C.LAYERS['h_htl'],
    'abs': C.LAYERS['h_abs'],
    'etl': C.LAYERS['h_etl'],
    'fto': C.LAYERS['h_fto'],
}
MIN_ELEM_PER_LAYER = 3


def mesh_sizes(lam_ref_nm, ppw, hmin, hmax_cap, skin_floor=0.0, verbose=True):
    """Per-material hmax [nm] from lam/(n_eff*ppw), with clamps.

    Clamps exist for three reasons:
      * hmax_cap keeps the near-lossless, optically thick air/PML region
        from being refined for no benefit;
      * in an absorbing material the field decays on the skin depth, so the
        size is additionally capped at delta/2. That is what resolves the Au
        contact -- lam/(n_eff*ppw) alone leaves the metal several times too
        coarse;
      * skin_floor bounds how far that second clamp may go. Free tets are
        ISOTROPIC, so a size chosen to resolve decay along z is also applied
        across x and y -- and these layers are laterally uniform, with
        lateral field structure no finer than the 350 nm pitch. Without the
        floor, Au alone asks for ~6 nm elements and several hundred thousand
        tets to resolve a direction that does not need it.
    """
    out = {}
    for mat in SELECTIONS:
        ne = n_eff(mat, lam_ref_nm)
        h = lam_ref_nm / (ne * ppw)
        why = 'lam/(n*ppw)'
        delta = skin_depth(mat, lam_ref_nm)
        if delta / 2.0 < h:
            h = max(delta / 2.0, skin_floor)
            why = 'skin depth/2' if delta / 2.0 >= skin_floor else 'skin floor'
        # The cap applies ONLY to the transparent superstrate. Applying it to
        # every material silently overrode the ppw criterion in the layers
        # that matter -- at 700 nm it pinned the absorber to the cap for every
        # ppw below ~6, which would have made a convergence study compare
        # three identical meshes and 'prove' convergence that was never tested.
        if mat in CAPPED_MATERIALS and h > hmax_cap:
            h = hmax_cap
            why = 'hmax cap'
        # A layer spanned by one or two elements cannot represent the field
        # through its thickness no matter what the wave criterion says, and a
        # 50 nm ETL is thinner than the wavelength-derived size at every ppw
        # here. Require at least MIN_ELEM_PER_LAYER elements across each
        # finite layer.
        t = LAYER_THICKNESS.get(mat)
        if t and h > t / MIN_ELEM_PER_LAYER:
            h = t / MIN_ELEM_PER_LAYER
            why = f'{MIN_ELEM_PER_LAYER}/layer thickness'
        if h < hmin:
            h = hmin
            why = 'hmin floor'
        out[mat] = round(float(h), 3)
        if verbose:
            d = 'inf' if delta == float('inf') else f'{delta:7.1f}'
            print(f'    {mat:4s} n_eff={ne:6.3f}  delta={d} nm'
                  f'   -> hmax {out[mat]:7.2f} nm   [{why}]')
    return out
