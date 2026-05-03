#!/usr/bin/env bash
#
# start.sh — start the launcher in the background via setsid + nohup.
# Survives log-out, terminal close, and SSH disconnect.
#
# This script exits immediately after spawning; the launcher keeps running.
#
# Monitoring from SSH later:
#   bash run_extension/status.sh        # quick status (state, GO/WAIT/STOP)
#   tail -f run_extension/logs/launcher.log     # live launcher
#   tail -f run_extension/logs/3e14.log         # specific job
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT/run_extension/launch.sh"
LOGDIR="$ROOT/run_extension/logs"
LOG="$LOGDIR/launcher.log"
STATUS="$ROOT/run_extension/STATUS"

mkdir -p "$LOGDIR"

# Refuse double-launch
if [[ -f "$STATUS" ]]; then
    state="$(grep -m1 '^state:' "$STATUS" | awk '{print $2}')"
    case "$state" in
        STARTING|RUNNING)
            echo "Launcher already running (STATUS state=$state)." >&2
            echo "Status:  bash run_extension/status.sh" >&2
            echo "Stop:    pkill -f main-csv-static  (and pkill launch.sh manually)" >&2
            exit 1
            ;;
    esac
fi

# Idempotent: refuse to launch if all 3 CSVs already exist
all_present=1
for n in 30000000000000 100000000000000 300000000000000; do
    [[ -f "$ROOT/ml_data/gaps_N${n}.csv" ]] || all_present=0
done
if [[ "$all_present" -eq 1 ]]; then
    echo "All 3 CSVs already exist in ml_data/. Nothing to launch." >&2
    echo "To re-run, rename or remove them first." >&2
    exit 1
fi

# Detach: setsid makes the process a session leader -> ignores SIGHUP
# stdin /dev/null, stdout and stderr to log, & in background
setsid nohup bash "$SCRIPT" > "$LOG" 2>&1 < /dev/null &
LAUNCH_PID=$!

# Detach from child shell (extra safety)
disown "$LAUNCH_PID" 2>/dev/null || true

# Brief wait so the launcher has time to write STATUS
sleep 2

echo "============================================================"
echo "  Launcher started in background (PID $LAUNCH_PID)"
echo "============================================================"
echo
echo "Survives log-out, terminal close, and SSH disconnect."
echo
if [[ -f "$STATUS" ]]; then
    echo "STATUS file:"
    cat "$STATUS"
    echo
fi
echo "Monitoring:"
echo "  bash $ROOT/run_extension/status.sh"
echo "  tail -f $LOG"
echo "  tail -f $LOGDIR/3e14.log"
echo
echo "From SSH later:"
echo "  ssh $(whoami)@$(hostname)"
echo "  cd $ROOT"
echo "  bash run_extension/status.sh"
echo
echo "Early stop:"
echo "  pkill -f 'main-csv-static -o N'"
echo "  pkill -f 'bash.*launch.sh'"
echo "============================================================"
