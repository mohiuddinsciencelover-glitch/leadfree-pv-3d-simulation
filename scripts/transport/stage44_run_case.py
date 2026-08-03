"""Stage 44 — generic single-case J-V runner (fresh session, memory-safe).

Usage:
  python3 stage44_run_case.py <model.mph> <case_name> <light:0|1> <rerun_std2:0|1> \
      <heteromode:1|2> [key=value ...]
Each key=value sets a COMSOL parameter (e.g. chi_abs='3.75[V]' tau_srh='123[ns]').
Forward bias sweep (Vapp 0 -> -1.5 V). Saves results/jv_<case_name>.csv.
Model is saved after a successful run.
"""
import mph, numpy as np, traceback, sys, os

MODEL, name, light, rerun_std2, hmode = sys.argv[1:6]
overrides = [a.split('=', 1) for a in sys.argv[6:]]
light = light == '1'; rerun_std2 = rerun_std2 == '1'
OUTDIR = '/home/mohiuddin/Desktop/COMSOL_SOLAR_CELL/results'
os.makedirs(OUTDIR, exist_ok=True)

client = mph.start(cores=2)
model = client.load(MODEL)
m = model.java
p = m.param()
semi = m.component('comp1').physics('semi')
semi.feature('tsrh1').active(True)
semi.feature('udr_rad').active(True)
semi.feature('surf_htl').active(False)
semi.feature('surf_etl').active(False)
semi.feature('hetero1').set('HeteroModelSelection', hmode)
semi.feature('hetero2').set('HeteroModelSelection', hmode)
p.set('ramp', '1e-8')
vend = '-1.5'
vlist = None
for k, v in overrides:
    if k == 'VEND':                 # optional sweep end (e.g. VEND=-1.9)
        vend = v
        print(f'sweep end = {vend} V', flush=True)
        continue
    if k == 'VLIST':                # optional explicit plistarr (denser ramps)
        vlist = v
        print(f'sweep list = {vlist}', flush=True)
        continue
    if k == 'GZ':                   # optional: repoint the G(z) interpolation
        m.func('Gz_fn').set('filename', v)
        print(f'Gz_fn -> {v}', flush=True)
        continue
    p.set(k, v)
    print(f'param {k} = {v}', flush=True)
m.study('std5').feature('stat5').setIndex(
    'plistarr', vlist if vlist else f'range(0,-0.025,{vend})', 1)
for prop, val in [('solnum', 'last'), ('notsolnum', 'last')]:
    try:
        m.study('std5').feature('stat5').set(prop, val)
    except Exception:
        pass

def remove_sols(study):
    while True:
        hit = False
        for stag in [str(t) for t in m.sol().tags()]:
            try:
                if str(m.sol(stag).study()) == study:
                    m.sol().remove(stag); hit = True; break
            except Exception:
                pass
        if not hit:
            return

print(f'=== CASE {name} light={light} rerun_std2={rerun_std2} hmode={hmode} ===', flush=True)
try:
    remove_sols('std3')
    udg1 = semi.feature('udg1')
    if rerun_std2:
        udg1.active(False)
        remove_sols('std2')
        m.study('std2').run()
        print('  std2 ok', flush=True)
    udg1.active(light)
    remove_sols('std5')
    m.study('std5').run()
    print('  std5 ok', flush=True)
    tag = None
    for stag in [str(t) for t in m.sol().tags()]:
        try:
            if str(m.sol(stag).study()) == 'std5' and len(m.sol(stag).feature().tags()) > 0:
                tag = stag
        except Exception:
            pass
    dt = None
    for d in [str(t) for t in m.result().dataset().tags()]:
        ds = m.result().dataset(d)
        try:
            if str(ds.getType()) == 'Solution' and str(ds.getString('solution')) == tag \
               and 'Store' not in str(ds.label()):
                dt = d
        except Exception:
            pass
    nt = [str(t) for t in m.result().numerical().tags()]
    if 'gev_jv' in nt:
        m.result().numerical().remove('gev_jv')
    g = m.result().numerical().create('gev_jv', 'EvalGlobal')
    g.set('data', dt)
    g.set('expr', ['Vapp', 'semi.I0_4', 'semi.I0_3'])
    arr = np.array(g.getReal())
    np.savetxt(f'{OUTDIR}/jv_{name}.csv', arr, delimiter=',',
               header='rows: Vapp_V | I_top_A | I_bottom_A')
    print(f'  saved jv_{name}.csv shape={arr.shape}', flush=True)
    model.save()
    print('  OK', flush=True)
except Exception:
    traceback.print_exc()
    print(f'  CASE {name} FAILED', flush=True)
    sys.exit(1)
