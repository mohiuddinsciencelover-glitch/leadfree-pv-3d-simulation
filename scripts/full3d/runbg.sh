#!/usr/bin/env bash
# Run a full3d command detached from the SSH session.
#
# An interactive ssh command dies with the connection, which already cost one
# production solve on this box. Everything long-running goes through here:
# setsid detaches from the controlling terminal, so the job survives the
# session ending, and the PID is recorded so it can be checked or killed.
#
#   ./runbg.sh <jobname> python3 build/f3d_08_sweep_driver.py
#   tail -f logs/<jobname>.log
#   kill $(cat logs/<jobname>.pid)
set -euo pipefail
JOB="$1"; shift
cd "$(dirname "$0")"
source ./env.sh
mkdir -p logs
LOG="logs/${JOB}.log"
PIDF="logs/${JOB}.pid"

if [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; then
  echo "ALREADY RUNNING: ${JOB} pid $(cat "$PIDF")"; exit 3
fi

# Rotate rather than append. Appending once made a killed run's error lines
# look like a live failure to a log watcher; one run per file removes that
# whole class of false alarm.
[ -f "$LOG" ] && mv "$LOG" "${LOG%.log}.$(date +%Y%m%d-%H%M%S).log"
{ echo "===== ${JOB} started $(date -Is) ====="; echo "cmd: $*"; } > "$LOG"
setsid nohup "$@" >> "$LOG" 2>&1 < /dev/null &
echo $! > "$PIDF"
echo "LAUNCHED ${JOB} pid $(cat "$PIDF") -> full3d/${LOG}"
