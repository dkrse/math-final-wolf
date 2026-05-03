#!/usr/bin/env bash
#
# launch.sh — runs 3 parallel single-threaded main-csv-static jobs
#             on CPU cores 0, 1, 2 (leaves 17 free for analysis / D-branch).
#
# After completion renames outputs into the ml_data/ convention
# (gaps_N{N}.csv, records_N{N}.csv) and emits sha256 sums.
#
# Expected wall time: ~24 h (limited by the N = 3*10^14 run, observed
# 24 h 40 min on a single core).
#
# Usage:
#   bash run_extension/launch.sh
#   tail -f run_extension/logs/3e14.log   # in another terminal
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$ROOT/main-csv-static"
WORK="$ROOT/run_extension"
LOGDIR="$WORK/logs"
DATA="$ROOT/ml_data"
STATUS="$WORK/STATUS"

mkdir -p "$LOGDIR"

write_status() {
    local state="$1"; shift
    local msg="$*"
    {
        echo "state: $state"
        echo "timestamp: $(date -Is)"
        echo "host: $(hostname)"
        echo "pid_launcher: $$"
        [[ -n "$msg" ]] && echo "note: $msg"
    } > "$STATUS"
}
write_status STARTING "launcher booting"

# Write FAILED on any unexpected exit
trap 'rc=$?; if [[ "$rc" -ne 0 && ! -f "$WORK/.completed_clean" ]]; then write_status FAILED "exit rc=$rc on $(date -Is)"; fi' EXIT

if [[ ! -x "$BIN" ]]; then
    echo "ERROR: $BIN not found or not executable" >&2
    exit 1
fi

# (suffix, N_decimal_string, cpu, target_filename_in_ml_data)
JOBS=(
    "N3e13 30000000000000 0 30000000000000"
    "N1e14 100000000000000 1 100000000000000"
    "N3e14 300000000000000 2 300000000000000"
)

PIDS=()
SUFFIXES=()

cleanup() {
    echo "Caught signal, killing children: ${PIDS[*]}" >&2
    write_status INTERRUPTED "received signal, killed children"
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait
    exit 130
}
trap cleanup INT TERM

cd "$WORK"

# Idempotency: refuse to start if all targets already exist in ml_data/.
ALL_EXIST=1
for spec in "${JOBS[@]}"; do
    read -r suffix N cpu target <<<"$spec"
    [[ -f "$DATA/gaps_N${target}.csv" ]] || ALL_EXIST=0
done
if [[ "$ALL_EXIST" -eq 1 ]]; then
    echo "All 3 target CSVs already exist in $DATA/. Nothing to do." >&2
    write_status DONE "all CSVs already in ml_data/, no run needed"
    touch "$WORK/.completed_clean"
    exit 0
fi

echo "=== Launch $(date -Is) ==="
echo "Binary:  $BIN"
echo "Workdir: $WORK"
echo "Logs:    $LOGDIR"
echo

# --- Spawn jobs ---
for spec in "${JOBS[@]}"; do
    read -r suffix N cpu _target <<<"$spec"
    log="$LOGDIR/${suffix#N}.log"
    echo "  start  ${suffix}  N=${N}  CPU=${cpu}  log=${log}"
    taskset -c "$cpu" "$BIN" -o "$suffix" "$N" \
        >"$log" 2>&1 &
    PIDS+=("$!")
    SUFFIXES+=("$suffix")
done

echo
echo "PIDs: ${PIDS[*]}"
echo "Waiting for completion..."
write_status RUNNING "PIDs=${PIDS[*]}"

# --- Wait and record exit codes ---
MAX_RC=0
for i in "${!PIDS[@]}"; do
    pid="${PIDS[$i]}"
    suffix="${SUFFIXES[$i]}"
    if wait "$pid"; then
        rc=0
    else
        rc=$?
    fi
    echo "  done   ${suffix}  pid=${pid}  rc=${rc}  $(date -Is)"
    [[ "$rc" -gt "$MAX_RC" ]] && MAX_RC="$rc"
done

if [[ "$MAX_RC" -ne 0 ]]; then
    echo "ERROR: at least one job failed (max rc=${MAX_RC})" >&2
    exit "$MAX_RC"
fi

# --- Post-run sanity checks ---
echo
echo "=== Post-run checks ==="
for spec in "${JOBS[@]}"; do
    read -r suffix N cpu _target <<<"$spec"
    log="$LOGDIR/${suffix#N}.log"
    if grep -q "WARNING" "$log"; then
        echo "  WARN   ${suffix}: log contains WARNING (gap overflow?)" >&2
        grep "WARNING" "$log" >&2
    fi
done

# --- Rename into ml_data/ convention ---
echo
echo "=== Renaming into ml_data/ ==="
for spec in "${JOBS[@]}"; do
    read -r suffix N cpu target <<<"$spec"
    src_gaps="$WORK/gaps_${suffix}.csv"
    src_recs="$WORK/records_${suffix}.csv"
    dst_gaps="$DATA/gaps_N${target}.csv"
    dst_recs="$DATA/records_N${target}.csv"

    if [[ -f "$dst_gaps" ]]; then
        echo "  SKIP   ${dst_gaps} already exists (refusing to overwrite)" >&2
        continue
    fi
    mv "$src_gaps" "$dst_gaps"
    [[ -f "$src_recs" ]] && mv "$src_recs" "$dst_recs"
    echo "  moved  ${dst_gaps}"
done

# --- Checksum audit trail ---
echo
echo "=== sha256 ==="
SHA_FILES=()
for spec in "${JOBS[@]}"; do
    read -r suffix N cpu target <<<"$spec"
    SHA_FILES+=("gaps_N${target}.csv")
done
( cd "$DATA" && sha256sum "${SHA_FILES[@]}" 2>/dev/null \
    | tee "$WORK/checksums.sha256" ) || true

# --- Final status ---
ALL_PRESENT=1
for spec in "${JOBS[@]}"; do
    read -r suffix N cpu target <<<"$spec"
    [[ -f "$DATA/gaps_N${target}.csv" ]] || ALL_PRESENT=0
done

if [[ "$ALL_PRESENT" -eq 1 ]]; then
    write_status DONE "all 3 CSVs in ml_data/, sha256 written"
    touch "$WORK/.completed_clean"
    echo
    echo "=== Done $(date -Is) ==="
    echo "Next steps (after SSH-attach):"
    echo "  source .venv/bin/activate"
    echo "  python run_extension/check_ratio.py --all"
else
    write_status PARTIAL "some CSVs missing in ml_data/, see logs"
    echo
    echo "=== Partial $(date -Is) ==="
fi
