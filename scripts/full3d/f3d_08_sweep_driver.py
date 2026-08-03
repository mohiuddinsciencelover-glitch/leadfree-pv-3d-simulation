"""FULL-3D stage 08 -- launch the parallel wavelength sweep and merge results.

The sweep is embarrassingly parallel across wavelengths, and COMSOL's
shared-memory scaling on a single 3D vector-Helmholtz solve saturates well
below this machine's core count. So the throughput lever is N independent
COMSOL processes on disjoint wavelength slices, not one large solve.

Tasks are dealt out ROUND-ROBIN over a band-ordered list, not in contiguous
blocks. Solve cost rises steeply towards the blue end -- finer mesh, more
oscillations per cell -- so contiguous blocks would leave one worker holding
the whole blue band long after the rest had finished. Round-robin gives every
worker a comparable mix of cheap and expensive points.

Each worker owns its own shard CSV, so there is no write contention and no
lock. Merging is separate and re-runnable: `--merge-only` rebuilds the
combined CSV from whatever shards exist, which makes partial results usable
while the sweep is still running.

Run:
    python3 full3d/build/f3d_08_sweep_driver.py              # launch + wait
    python3 full3d/build/f3d_08_sweep_driver.py --overlap    # band-seam check
    python3 full3d/build/f3d_08_sweep_driver.py --merge-only
"""
import sys, os, csv, time, glob, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as C

HERE = os.path.dirname(os.path.abspath(__file__))
WORKER = os.path.join(HERE, 'f3d_07_sweep_worker.py')
MERGED = C.RESULT_CSV


def shard_rows():
    rows, fields = [], None
    for shard in sorted(glob.glob(os.path.join(
            C.SHARDS, f'{C.ABSORBER}_{C.PROFILE}_w[0-9][0-9].csv'))):
        with open(shard) as f:
            r = csv.DictReader(f)
            if r.fieldnames:
                fields = r.fieldnames
            rows.extend(list(r))
    return rows, fields


def merge():
    """Combine shards into one wavelength-sorted CSV of the owning band.

    A wavelength solved on a NON-owning band is an overlap/QC point, kept in
    the shards but excluded here so the published spectrum comes from one
    consistent mesh rule.
    """
    rows, fields = shard_rows()
    if not rows:
        print('no shard rows yet')
        return 0
    uniq = {}
    for row in rows:
        lam = float(row['lambda_nm'])
        if int(row['band']) != C.band_of(lam):
            continue                      # overlap check point, not the record
        uniq[lam] = row                   # a re-run wins over the earlier row
    ordered = [uniq[k] for k in sorted(uniq)]
    os.makedirs(C.RESULTS, exist_ok=True)
    with open(MERGED, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(ordered)
    print(f'merged {len(ordered)} wavelengths -> {MERGED}')
    return len(ordered)


def launch(tasks, tag):
    """Round-robin `tasks` [(band, lam)] over workers and wait for them."""
    W = min(C.N_WORKERS, len(tasks))
    buckets = [tasks[i::W] for i in range(W)]
    print(f'{W} workers x {C.CORES_PER_WORKER} cores = '
          f'{W * C.CORES_PER_WORKER} cores requested')
    for i, b in enumerate(buckets):
        pts = [f'{int(l)}' for _, l in b[:6]]
        print(f'  w{i:02d}: {len(b):2d} pts  {pts}{" ..." if len(b) > 6 else ""}')

    os.makedirs(C.LOGS, exist_ok=True)
    os.makedirs(C.SHARDS, exist_ok=True)
    procs = []
    for i, b in enumerate(buckets):
        if not b:
            continue
        log = os.path.join(C.LOGS, f'sweep_{C.PROFILE}_{tag}_w{i:02d}.log')
        cmd = [sys.executable, WORKER, str(i)] + [f'{bd}:{l:g}' for bd, l in b]
        # Rotate, don't append. A killed worker leaves a session-cleanup
        # traceback behind, and appending makes that stale text look like a
        # live failure to anything watching the logs -- which it duly did.
        if os.path.exists(log):
            os.replace(log, f'{log[:-4]}.{time.strftime("%Y%m%d-%H%M%S")}.log')
        fh = open(log, 'w')
        fh.write(f'===== launched {time.strftime("%Y-%m-%d %H:%M:%S")} '
                 f'({len(b)} tasks) =====\n')
        fh.flush()
        procs.append((i, subprocess.Popen(cmd, stdout=fh,
                                          stderr=subprocess.STDOUT), fh))
        # Stagger: each worker boots its own Comsol server, and starting them
        # simultaneously makes the JVM startup and licence handshake contend.
        time.sleep(8)

    print(f'\n{len(procs)} workers launched; waiting...', flush=True)
    t0 = time.time()
    alive = {i for i, _, _ in procs}
    while alive:
        time.sleep(30)
        for i, p, _ in procs:
            if i in alive and p.poll() is not None:
                alive.discard(i)
                print(f'[{time.time()-t0:7.0f}s] worker {i:02d} exited '
                      f'rc={p.returncode} ({len(alive)} still running)',
                      flush=True)
        n = merge()
        print(f'[{time.time()-t0:7.0f}s] {n}/{len(C.LAMBDA)} wavelengths done',
              flush=True)
    for _, _, fh in procs:
        fh.close()
    print(f'\n{tag} finished in {(time.time()-t0)/60:.1f} min')


def main():
    if '--merge-only' in sys.argv:
        merge()
        return

    C.banner()
    rows, _ = shard_rows()
    have = {(int(r['band']), float(r['lambda_nm'])) for r in rows}

    if '--overlap' in sys.argv:
        # Band-seam check: solve the first wavelength of each band on the
        # PREVIOUS (finer) band's mesh too. The difference measures the
        # discretisation error introduced by changing mesh across the seam --
        # the number a reviewer will ask for, rather than an assurance.
        tasks = [(C.band_of(l) - 1, l) for l in C.BAND_OVERLAP_CHECK
                 if C.band_of(l) > 0]
        tasks = [t for t in tasks if t not in have]
        print(f'band-overlap check: {tasks}')
        if tasks:
            launch(tasks, 'overlap')
        else:
            print('overlap points already solved')
        return

    tasks = [(C.band_of(l), l) for l in C.LAMBDA]
    # F3D_ONLY_BANDS restricts the run to some bands. Band 0 (the blue end) is
    # meshed at 300 nm and is several times larger than band 2, so N workers
    # all sitting in band 0 at once is the peak-memory case for the whole
    # study. Running the cheap bands at full width and then band 0 with fewer
    # workers keeps that peak bounded without slowing the bulk of the sweep.
    only = os.environ.get('F3D_ONLY_BANDS', '')
    if only:
        keep = {int(x) for x in only.split(',') if x.strip() != ''}
        tasks = [t for t in tasks if t[0] in keep]
        print(f'restricted to bands {sorted(keep)}')
    todo = [t for t in tasks if t not in have]
    print(f'{len(tasks)} wavelengths on the grid, {len(tasks)-len(todo)} '
          f'already solved, {len(todo)} to go')
    for i, (lo, hi) in enumerate(C.BANDS):
        n = len([1 for b, _ in todo if b == i])
        print(f'  band {i} ({lo:.0f}-{hi:.0f} nm): {n} to solve')
    if not todo:
        merge()
        return

    missing = [C.ready_path(b) for b in sorted({b for b, _ in todo})
               if not os.path.exists(C.ready_path(b))]
    if missing:
        print('MISSING solve-ready models -- run stage 06 per band first:')
        for m in missing:
            print('   ', m)
        sys.exit(1)

    launch(todo, 'main')
    merge()
    print('STAGE 08 DONE', flush=True)


# Guarded so the module can be imported (e.g. to test merge()) without
# launching a sweep as an import side effect.
if __name__ == '__main__':
    main()
