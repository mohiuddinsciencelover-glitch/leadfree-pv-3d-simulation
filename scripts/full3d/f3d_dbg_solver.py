"""Diagnostic: dump the solver sequence COMSOL auto-generates for std_opt.

Direct-solver memory growth was what made this necessary. Rather than guess
at the solver API, generate the default sequence, print the whole feature
tree with the properties that decide direct-vs-iterative, and patch from
there.

Run:  python3 full3d/build/f3d_dbg_solver.py [band]
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C
import mph

band = int(sys.argv[1]) if len(sys.argv) > 1 else 2
client = mph.start(cores=2)
model = client.load(C.ready_path(band))
java = model.java

sols = java.sol()
for t in [str(x) for x in sols.tags()]:
    sols.remove(t)
sol = sols.create('sol_dbg')
sol.study('std_opt')
sol.attach('std_opt')
sol.createAutoSequence('std_opt')
print(f'auto sequence created for band {band}\n')


def walk(feat, depth=0):
    pad = '  ' * depth
    for t in [str(x) for x in feat.feature().tags()]:
        f = feat.feature(t)
        try:
            typ = str(f.getType())
        except Exception:
            typ = '?'
        interesting = []
        for prop in ('linsolver', 'prefuntype', 'solver', 'prefun',
                     'nlsolver', 'iter', 'errorchk'):
            try:
                v = str(f.getString(prop))
                if v:
                    interesting.append(f'{prop}={v}')
            except Exception:
                pass
        print(f'{pad}- {t:14s} [{typ}] {" ".join(interesting)}')
        try:
            walk(f, depth + 1)
        except Exception:
            pass


walk(sol)
print('\n--- top-level solver properties ---')
for t in [str(x) for x in sol.feature().tags()]:
    f = sol.feature(t)
    try:
        props = [str(p) for p in f.properties()]
    except Exception:
        props = []
    print(f'{t}: {props[:28]}')
print('\nDBG DONE', flush=True)
