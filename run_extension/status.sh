#!/usr/bin/env bash
#
# status.sh — one-shot launcher state + per-job progress.
# Usage over SSH:
#   bash run_extension/status.sh
#
# Reports:
#   - current STATUS (state, timestamp, host, pid)
#   - whether the launcher and child processes are alive
#   - per job: last log line, CSV size, whether moved into ml_data/
#   - final verdict: GO (proceed), WAIT (still running), STOP (failed)
#
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$ROOT/run_extension"
LOGDIR="$WORK/logs"
DATA="$ROOT/ml_data"
STATUS="$WORK/STATUS"

SUFFIXES=("N3e13" "N1e14" "N3e14")
TARGETS=(30000000000000 100000000000000 300000000000000)

echo "========================================================"
echo "                LAUNCH B — STATUS"
echo "========================================================"
echo "Host: $(hostname)    Now: $(date -Is)"
echo

if [[ ! -f "$STATUS" ]]; then
    echo "STATUS file not found ($STATUS)."
    echo "Launcher has never been run, or was wiped."
    echo
    echo "VERDICT: NOT_STARTED"
    exit 0
fi

cat "$STATUS"
echo

# Process check
LAUNCH_PID="$(grep -m1 '^pid_launcher:' "$STATUS" | awk '{print $2}')"
if [[ -n "$LAUNCH_PID" ]] && kill -0 "$LAUNCH_PID" 2>/dev/null; then
    LAUNCHER_ALIVE=yes
else
    LAUNCHER_ALIVE=no
fi
echo "Launcher PID $LAUNCH_PID alive? $LAUNCHER_ALIVE"

# Child processes
CHILDREN=$(pgrep -f "main-csv-static -o N" | tr '\n' ' ')
if [[ -n "$CHILDREN" ]]; then
    echo "Child sieves alive: $CHILDREN"
else
    echo "Child sieves alive: none"
fi
echo

# Per-job progress
echo "--- per job ---"
for i in "${!SUFFIXES[@]}"; do
    suf="${SUFFIXES[$i]}"
    tgt="${TARGETS[$i]}"
    log="$LOGDIR/${suf#N}.log"
    csv_work="$WORK/gaps_${suf}.csv"
    csv_data="$DATA/gaps_N${tgt}.csv"

    if [[ -f "$csv_data" ]]; then
        size=$(stat -c %s "$csv_data")
        mtime=$(stat -c %y "$csv_data" | cut -d. -f1)
        printf "  %-6s  done    csv in ml_data/ (%d B, mtime %s)\n" \
               "$suf" "$size" "$mtime"
    elif [[ -f "$csv_work" ]]; then
        size=$(stat -c %s "$csv_work")
        printf "  %-6s  done?   csv in run_extension/ (%d B), not yet moved\n" \
               "$suf" "$size"
    elif [[ -f "$log" ]]; then
        # Try to extract last printed record line
        last=$(tail -3 "$log" | tr -d '\r' | tail -1 | cut -c -80)
        bytes=$(stat -c %s "$log")
        printf "  %-6s  log running (%d B): %s\n" \
               "$suf" "$bytes" "$last"
    else
        printf "  %-6s  not started\n" "$suf"
    fi
done

echo

# Final verdict
STATE="$(grep -m1 '^state:' "$STATUS" | awk '{print $2}')"
case "$STATE" in
    DONE)
        echo "VERDICT: GO  -> you can proceed"
        echo
        echo "Next steps:"
        echo "  source $ROOT/.venv/bin/activate"
        echo "  python $WORK/check_ratio.py --all"
        echo "  jupyter nbconvert --to notebook --execute --inplace \\"
        echo "         09_rev01_alt_forms.ipynb 10_rev01_robustness.ipynb \\"
        echo "         11_rev01_m1_vs_m3.ipynb"
        ;;
    RUNNING|STARTING)
        if [[ "$LAUNCHER_ALIVE" == "yes" ]]; then
            echo "VERDICT: WAIT  -> running, please wait"
        else
            echo "VERDICT: STALE  -> STATUS says RUNNING but launcher is dead"
            echo "          -> probably crashed, check logs: tail -n 100 $LOGDIR/*.log"
        fi
        ;;
    PARTIAL|FAILED|INTERRUPTED)
        echo "VERDICT: STOP  -> something failed, check logs"
        echo "  tail -n 50 $LOGDIR/*.log"
        ;;
    *)
        echo "VERDICT: UNKNOWN  -> state='$STATE'"
        ;;
esac
echo "========================================================"
