#!/usr/bin/env bash
#
# post_launch.sh — runs sanity check + notebook re-execution after the B-run.
# Run after status.sh reports VERDICT: GO.
#
# Usage from SSH:
#   cd /home/krse/notebooks/ver-02
#   bash run_extension/post_launch.sh
#
# Steps:
#   1. check_ratio.py --all       — sanity: 3 new N values vs previous
#   2. nbconvert --execute 09     — alt-form ranking on 28 N values
#   3. nbconvert --execute 10     — robustness (filter, weights, bootstrap)
#   4. nbconvert --execute 11     — M1* vs M3 formal comparison
#   5. nbconvert --execute 12     — disjoint-range out-of-sample replication
#
# Total runtime is on the order of 2-5 minutes. Writes to
# outputs/results/{rev01_*,disjoint_replication}.json.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -d "$ROOT/.venv" ]]; then
    echo "ERROR: .venv not found in $ROOT" >&2
    exit 1
fi

# shellcheck source=/dev/null
source "$ROOT/.venv/bin/activate"

STATUS="$ROOT/run_extension/STATUS"
if [[ -f "$STATUS" ]]; then
    state="$(grep -m1 '^state:' "$STATUS" | awk '{print $2}')"
    if [[ "$state" != "DONE" ]]; then
        echo "STATUS state=$state, expected DONE." >&2
        echo "Check first: bash run_extension/status.sh" >&2
        exit 1
    fi
fi

echo "============================================================"
echo "  Post-launch validation pipeline"
echo "============================================================"
echo

echo "--- Step 1/4: sanity check (Wolf-corrected ratios) ---"
if ! python "$ROOT/run_extension/check_ratio.py" --all; then
    echo "Sanity check FAILED -- notebook re-execution skipped." >&2
    exit 1
fi
echo

NB_DIR="$ROOT"
for nb in 09_rev01_alt_forms 10_rev01_robustness 11_rev01_m1_vs_m3 \
          12_disjoint_replication; do
    echo "--- Re-run: ${nb}.ipynb ---"
    if jupyter nbconvert --to notebook --execute --inplace \
            "$NB_DIR/${nb}.ipynb" 2>&1 | tail -5; then
        echo "  done: ${nb}"
    else
        echo "  FAILED: ${nb}" >&2
        exit 1
    fi
    echo
done

echo "============================================================"
echo "  All done. Outputs:"
echo "============================================================"
ls -la "$ROOT/outputs/results/" 2>/dev/null
echo
echo "Next steps:"
echo "  - Review outputs/results/rev01_*.json (new coefs, AIC, etc.)"
echo "  - Write notebook 12 (disjoint-replication) per scenario B+D"
echo "  - Begin branch D (theory)"
