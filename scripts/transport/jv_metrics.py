"""Extract photovoltaic metrics from a J-V run CSV.

Sign convention. `semi.I0_4` is the current into the top (TiO2/FTO) contact.
Forward-bias runs sweep Vapp NEGATIVE, so the voltage axis is flipped into the
conventional solar-cell quadrant before anything is measured, and the current
is oriented so that photocurrent is positive at V = 0.

PCE uses P_in = 1000.37 W/m^2, the actual integral of ASTM G173-03 global tilt
over 280-4000 nm, rather than the rounded 1000.

This reproduces every published base case of this project exactly:
  BaZrS3/Spiro   11.846 / 1.341 / 0.3398 / 5.395 %
  FASnI3         14.740 / 0.987 / 0.5173 / 7.521 %
  Cs2AgBiBr6      2.010 / 1.711 / 0.2865 / 0.984 %
  Cu2AgBiI6      13.856 / 1.512 / 0.4731 / 9.909 %   (dense grid; see below)

CAUTION for Cu2AgBiI6: on a 25 mV grid the solver lands on spurious S-NDR
branches and this script will faithfully report FF = 4.13 and PCE = 86.6 %.
That is the solver, not the code. Use the dense (1 mV) curve. Its V_oc is also
grid-dependent (1.512 V mixed grid vs 1.379 V uniform 1 mV) while P_max, V_mpp
and J_mpp are not -- compare only at matched grid.

Usage:  python3 jv_metrics.py <jv_*.csv> [more.csv ...]
"""
import sys
import os
import numpy as np

AREA = (350e-9) ** 2        # m^2, optical/electrical unit cell
P_IN = 1000.37              # W/m^2, ASTM G173-03 global tilt integral


def load(path):
    """Return (V, J) with V in volts and J in mA/cm^2, photocurrent positive."""
    d = np.loadtxt(path, delimiter=',', comments='#')
    if d.ndim == 1:
        raise SystemExit(f'{path}: not a J-V table')
    # rows may be (npts, 3) or transposed (3, npts)
    if d.shape[1] != 3 and d.shape[0] == 3:
        d = d.T
    V, I_top = d[:, 0], d[:, 1]
    o = np.argsort(V)
    V, I_top = V[o], I_top[o]
    J = I_top / AREA * 0.1                      # A/m^2 -> mA/cm^2
    if V.min() < -0.1:                          # forward runs sweep negative
        V = -V
        o = np.argsort(V)
        V, J = V[o], J[o]
    if np.interp(0.0, V, J) < 0:
        J = -J
    return V, J


def metrics(V, J):
    out = {'Jsc_mA_cm2': float(np.interp(0.0, V, J))}
    idx = np.where(np.diff(np.sign(J)) != 0)[0]
    if len(idx):
        i = idx[0]
        out['Voc_V'] = float(V[i] - J[i] * (V[i + 1] - V[i]) / (J[i + 1] - J[i]))
    else:
        out['Voc_V'] = None
        out['note'] = f'no sign change up to {V.max():.2f} V'
    P = V * J                                   # mW/cm^2
    i = int(np.argmax(P))
    out['Vmpp_V'] = float(V[i])
    out['Jmpp_mA_cm2'] = float(J[i])
    out['Pmax_mW_cm2'] = float(P[i])
    if out['Voc_V'] and out['Jsc_mA_cm2']:
        out['FF'] = float(P[i] / (out['Voc_V'] * out['Jsc_mA_cm2']))
    out['PCE_percent'] = float(P[i] / (P_IN * 0.1) * 100)
    return out


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for f in sys.argv[1:]:
        m = metrics(*load(f))
        ff = m.get('FF')
        print(f"{os.path.basename(f):<46} Jsc={m['Jsc_mA_cm2']:7.3f}  "
              f"Voc={m['Voc_V'] if m['Voc_V'] is None else round(m['Voc_V'], 3)}  "
              f"FF={'n/a' if ff is None else round(ff, 4)}  "
              f"PCE={m['PCE_percent']:6.3f}%  "
              f"[Pmax={m['Pmax_mW_cm2']:.4f} @ Vmpp={m['Vmpp_V']:.3f}]")
