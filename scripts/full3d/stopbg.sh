#!/usr/bin/env bash
# Stop a job started by runbg.sh -- INCLUDING its children.
#
# runbg.sh uses setsid, which puts the job in its own process group. Killing
# just the recorded pid therefore leaves the sweep workers running as orphans
# (ppid 1), still holding cores and memory and still writing results. That
# happened once here: five orphaned workers kept solving alongside a restarted
# run, put 10 concurrent solves on the machine, and wrote into a directory that
# had already been deleted. Signalling the whole process group with a negative
# pid is what actually stops the job.
#
#   ./stopbg.sh <jobname>          graceful (TERM), then KILL if needed
set -u
cd "$(dirname "$0")"
JOB="${1:?usage: $0 <jobname>}"
PIDF="logs/${JOB}.pid"
[ -f "$PIDF" ] || { echo "no pid file for '${JOB}'"; exit 1; }
PID=$(cat "$PIDF")

if ! kill -0 "$PID" 2>/dev/null; then
  echo "${JOB} (pid ${PID}) is not running"
else
  echo "stopping ${JOB}: process group ${PID}"
  kill -TERM -- "-${PID}" 2>/dev/null || kill -TERM "$PID" 2>/dev/null
  for _ in $(seq 1 15); do
    kill -0 "$PID" 2>/dev/null || break
    sleep 1
  done
  kill -0 "$PID" 2>/dev/null && { echo "  still up; sending KILL"; \
    kill -KILL -- "-${PID}" 2>/dev/null || kill -KILL "$PID" 2>/dev/null; }
fi

sleep 3
STRAY=$(ps -eo pid,ppid,args --no-headers -u "$USER" \
        | grep -E 'f3d_0[0-9]_|sweep_worker|sweep_driver' | grep -v grep \
        | awk '$2 == 1 {print $1}')
if [ -n "$STRAY" ]; then
  echo "orphaned f3d processes still present (ppid 1): $STRAY"
  echo "  -> killing them and their Comsol children"
  for p in $STRAY; do
    for kid in $(pgrep -P "$p"); do
      for gk in $(pgrep -P "$kid"); do kill -9 "$gk" 2>/dev/null; done
      kill -9 "$kid" 2>/dev/null
    done
    kill -9 "$p" 2>/dev/null
  done
fi
echo "done. remaining:"
ps -eo pid,args --no-headers -u "$USER" | grep -E 'f3d_0[0-9]_|sweep_' \
  | grep -v grep | cut -c1-90 || true
