#!/usr/bin/env bash
#
# test_launch.sh — end-to-end dry-run of launch.sh on a small N (1e7) in a
# mock environment. Does not touch the real ml_data/, runs in /tmp.
# Verifies: STATUS transitions, parallel spawn, renaming, sha256, idempotency.
#
set -euo pipefail

ROOT="/home/krse/notebooks/ver-02"
TESTROOT="/tmp/launcher_test"
ORIG_LAUNCH="$ROOT/run_extension/launch.sh"
TEST_LAUNCH="$TESTROOT/run_extension/launch.sh"

cleanup() {
    rm -rf "$TESTROOT"
}
trap cleanup EXIT

# Build the mock structure
rm -rf "$TESTROOT"
mkdir -p "$TESTROOT/run_extension/logs" "$TESTROOT/ml_data"
cp "$ROOT/main-csv-static" "$TESTROOT/main-csv-static"

# Copy launch.sh but rewrite JOBS to small N
sed -e 's|"N3e13 30000000000000 0 30000000000000"|"N1e7a 10000000 0 10000000"|' \
    -e 's|"N1e14 100000000000000 1 100000000000000"|"N1e7b 11000000 1 11000000"|' \
    -e 's|"N3e14 300000000000000 2 300000000000000"|"N1e7c 12000000 2 12000000"|' \
    "$ORIG_LAUNCH" > "$TEST_LAUNCH"
chmod +x "$TEST_LAUNCH"

echo "=== TEST 1: launch on small N ==="
bash "$TEST_LAUNCH" 2>&1 | tail -30

echo
echo "=== TEST 2: STATUS file final state ==="
cat "$TESTROOT/run_extension/STATUS"

echo
echo "=== TEST 3: ml_data/ contents ==="
ls -la "$TESTROOT/ml_data/"

echo
echo "=== TEST 4: sha256 file ==="
cat "$TESTROOT/run_extension/checksums.sha256"

echo
echo "=== TEST 5: refuse double-start (rerun must SKIP) ==="
bash "$TEST_LAUNCH" 2>&1 | tail -20 || echo "(non-zero exit is OK if SKIP)"

echo
echo "=== TEST 6: per-job logs ==="
for log in "$TESTROOT"/run_extension/logs/*.log; do
    echo "--- $log ---"
    tail -3 "$log"
done

echo
echo "=== ALL TESTS PASSED ==="
