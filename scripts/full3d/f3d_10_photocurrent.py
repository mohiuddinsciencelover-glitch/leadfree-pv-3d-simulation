"""FULL-3D stage 10 -- AM1.5G-weighted photocurrent and the optical loss budget.

Turns an absorptance spectrum into the numbers a photovoltaics paper reports:

    J_ph = q * integral A_absorber(lambda) * Phi_AM15G(lambda) dlambda

with Phi the AM1.5G photon flux, Phi = E_lambda * lambda / (h c). This is the
photocurrent at 100 % carrier collection -- an OPTICAL ceiling, not a device
Jsc, and it must always be quoted as such.

Every other channel is integrated the same way, so the result is a closed
budget: absorber + each parasitic layer + reflectance = the total incident
current. A budget that closes is what makes "the texture gains X" a claim
about physics rather than about one number moving.

INTEGRATION. Absorptance is interpolated onto the AM1.5G file's own dense
grid rather than the spectrum being resampled onto the 10 nm solve grid.
AM1.5G has deep, narrow atmospheric absorption bands; averaging it down to
10 nm bins would smear them and bias the integral. A(lambda) is smooth, so
interpolating it instead is the side that loses nothing.

Run:
  python3 full3d/build/f3d_10_photocurrent.py <absorptance.csv> [label]
  python3 full3d/build/f3d_10_photocurrent.py <textured.csv> <planar.csv> --compare
"""
import sys, os, csv, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import config as C

Q = 1.602176634e-19          # C
H = 6.62607015e-34           # J s
CLIGHT = 2.99792458e8        # m/s

# Band gaps, for the detailed-balance ceiling the result is compared against.
# BaZrS3 is 1.94 eV -- the value reported by the SAME source as its optical
# constants (Nishigaki 2020, measured ellipsometry). The manuscript's earlier
# 1.75 eV assumption is inconsistent with that data, whose absorption onset
# is at 673 nm; quoting a 708 nm ceiling against optics that stop absorbing
# at 673 nm would misstate the headroom.
EG_EV = {'FASnI3': 1.41, 'BaZrS3': 1.94, 'Cs2AgBiBr6': 2.10,
         'Cu2AgBiI6': 2.06}


def photon_flux():
    """AM1.5G spectral photon flux [photons m^-2 s^-1 nm^-1] on its own grid."""
    d = np.loadtxt(C.AM15G, delimiter=',', comments='#')
    lam_nm, irr = d[:, 0], d[:, 1]           # nm, W m^-2 nm^-1
    phi = irr * (lam_nm * 1e-9) / (H * CLIGHT)
    return lam_nm, phi


def load_spectrum(path):
    """Read a merged absorptance CSV into {column: array}, sorted by lambda."""
    rows = list(csv.DictReader(open(path)))
    if not rows:
        raise SystemExit(f'{path} has no data rows')
    rows.sort(key=lambda r: float(r['lambda_nm']))
    out = {'lambda_nm': np.array([float(r['lambda_nm']) for r in rows])}
    for k in rows[0]:
        if k.startswith('A_') or k in ('R_implied', 'energy_residual',
                                       'n_elem', 'solve_s'):
            out[k] = np.array([float(r[k]) if r[k] not in ('', 'nan')
                               else np.nan for r in rows])
    return out


def integrate(lam_grid, values, lam_nm, phi):
    """q * integral(values * phi) over the overlap, in mA/cm^2."""
    m = (lam_nm >= lam_grid.min()) & (lam_nm <= lam_grid.max())
    v = np.interp(lam_nm[m], lam_grid, values)
    return Q * np.trapz(v * phi[m], lam_nm[m]) / 10.0     # A/m^2 -> mA/cm^2


def budget(spec, lam_nm, phi):
    """Per-channel current budget in mA/cm^2."""
    lam = spec['lambda_nm']
    out = {}
    for key in spec:
        if key.startswith('A_') and key not in ('A_from_flux',):
            out[key] = integrate(lam, spec[key], lam_nm, phi)
    if 'R_implied' in spec:
        out['R'] = integrate(lam, spec['R_implied'], lam_nm, phi)
    out['incident'] = integrate(lam, np.ones_like(lam), lam_nm, phi)
    return out


def report(path, label=None):
    spec = load_spectrum(path)
    lam_nm, phi = photon_flux()
    b = budget(spec, lam_nm, phi)
    lam = spec['lambda_nm']
    label = label or os.path.basename(path)

    print(f'\n{"="*72}\n  {label}\n{"="*72}')
    print(f'  wavelengths      : {len(lam)}  ({lam.min():.0f}-{lam.max():.0f} nm)')
    if 'energy_residual' in spec:
        r = spec['energy_residual']
        r = r[~np.isnan(r)]
        if len(r):
            print(f'  energy residual  : mean {r.mean():+.4f}, '
                  f'worst {r[np.argmax(abs(r))]:+.4f}  '
                  f'({"OK" if abs(r).max() < 0.02 else "** CHECK MESH **"})')

    inc = b['incident']
    print(f'\n  {"channel":<22}{"mA/cm2":>10}{"% of incident":>16}')
    print(f'  {"-"*48}')
    order = ['A_absorber', 'A_FTO_total', 'A_TiO2', 'A_HTL', 'A_Au', 'R']
    named = {'A_absorber': f'{C.ABSORBER} (useful)', 'A_FTO_total': 'FTO + texture',
             'A_TiO2': 'TiO2 ETL', 'A_HTL': 'Spiro HTL', 'A_Au': 'Au contact',
             'R': 'reflected'}
    acc = 0.0
    for k in order:
        if k in b:
            acc += b[k]
            print(f'  {named[k]:<22}{b[k]:>10.3f}{100*b[k]/inc:>15.1f}%')
    print(f'  {"-"*48}')
    print(f'  {"sum of channels":<22}{acc:>10.3f}{100*acc/inc:>15.1f}%')
    print(f'  {"incident (300-900)":<22}{inc:>10.3f}{100.0:>15.1f}%')
    print(f'  closure error        {acc-inc:>10.3f} mA/cm2  '
          f'({100*(acc-inc)/inc:+.2f} %)')

    eg = EG_EV.get(C.ABSORBER)
    if eg:
        lam_g = 1239.841984 / eg          # nm
        m = (lam_nm >= lam.min()) & (lam_nm <= lam_g)
        j_max = Q * np.trapz(phi[m], lam_nm[m]) / 10.0
        print(f'\n  detailed-balance ceiling for Eg = {eg:.2f} eV '
              f'(lambda_g = {lam_g:.0f} nm): {j_max:.2f} mA/cm2')
        print(f'  this structure reaches {b["A_absorber"]:.2f} mA/cm2 = '
              f'{100*b["A_absorber"]/j_max:.1f} % of that ceiling')
        if lam.max() < lam_g:
            print(f'  !! grid stops at {lam.max():.0f} nm, short of lambda_g = '
                  f'{lam_g:.0f} nm -- J_ph is UNDERESTIMATED !!')
    return b


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        # RESULT_CSV respects the variant (planar runs carry a _planar
        # suffix); the old hardcoded textured name made no-arg invocations
        # fail silently for planar-only absorbers.
        args = [C.RESULT_CSV]
    if '--compare' in sys.argv and len(args) >= 2:
        bt = report(args[0], 'TEXTURED')
        bp = report(args[1], 'PLANAR REFERENCE')
        print(f'\n{"="*72}\n  TEXTURED vs PLANAR\n{"="*72}')
        print(f'  {"channel":<22}{"planar":>10}{"textured":>11}'
              f'{"delta":>10}{"rel":>9}')
        print(f'  {"-"*62}')
        for k in ['A_absorber', 'A_FTO_total', 'A_TiO2', 'A_HTL', 'A_Au', 'R']:
            if k in bt and k in bp:
                d = bt[k] - bp[k]
                rel = 100 * d / bp[k] if bp[k] else float('nan')
                print(f'  {k:<22}{bp[k]:>10.3f}{bt[k]:>11.3f}'
                      f'{d:>+10.3f}{rel:>+8.1f}%')
        gain = 100 * (bt['A_absorber'] - bp['A_absorber']) / bp['A_absorber']
        print(f'\n  TEXTURE GAIN IN USEFUL PHOTOCURRENT: {gain:+.2f} %  '
              f'({bp["A_absorber"]:.2f} -> {bt["A_absorber"]:.2f} mA/cm2)')
        out = os.path.join(C.RESULTS, f'f3d_{C.ABSORBER}_photocurrent.json')
        json.dump({'textured': bt, 'planar': bp, 'gain_percent': gain},
                  open(out, 'w'), indent=2)
        print(f'\n  -> {out}')
    else:
        for a in args:
            report(a)
