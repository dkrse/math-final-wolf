"""
check_ratio.py — sanity check after a new N run completes.

Compares gap counts for small g between the new N and the nearest smaller N
already in ml_data/. Per-g expected ratio = wolf_density(g, N_new) /
wolf_density(g, N_old). Wolf's formula is not exact, but its systematic
offset is expected to carry over to both N values, so we check whether
   (empirical ratio) / (Wolf ratio) ~ 1
within 5% tolerance for g in {2, 4, ..., 16}.

Detects: corrupted CSV, wrong cwd, indexing bugs in the generator,
overflow, MAX_GAP saturation. Does NOT detect errors in Wolf's model
itself.

Usage:
   python run_extension/check_ratio.py 30000000000000
   python run_extension/check_ratio.py --all   # all new N values
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "ml_data"
sys.path.insert(0, str(ROOT / "app-python"))
from analyze_gaps import wolf_density, _li2  # noqa: E402

NEW_N = [
    30_000_000_000_000,
    100_000_000_000_000,
    300_000_000_000_000,
    1_000_000_000_000_000,
]
SMALL_G = [2, 4, 6, 8, 10, 12, 14, 16]
# Tolerance 5%: Wolf's formula carries a residual offset of order 1-3% at
# these N (precisely what the paper models via R(g, N) = a*sqrt(omega) -
# b*log log N). The purpose of this check is to catch catastrophic errors
# (broken CSV, indexing bug, overflow), not to validate Wolf.
TOLERANCE = 0.05


def list_all_n(data_dir: Path) -> list[int]:
    out = []
    for f in data_dir.glob("gaps_N*.csv"):
        try:
            n = int(f.stem.replace("gaps_N", ""))
            out.append(n)
        except ValueError:
            pass
    return sorted(out)


def previous_n(target: int, all_n: list[int]) -> int | None:
    smaller = [n for n in all_n if n < target]
    return max(smaller) if smaller else None


def load_counts(n: int) -> pd.Series:
    f = DATA / f"gaps_N{n}.csv"
    if not f.exists():
        raise FileNotFoundError(f)
    df = pd.read_csv(f)
    return df.set_index("gap")["count"]


def check_one(n_new: int) -> bool:
    all_n = list_all_n(DATA)
    n_old = previous_n(n_new, all_n)
    if n_old is None:
        print(f"[{n_new:.0e}] no smaller N in ml_data/", file=sys.stderr)
        return False

    try:
        new = load_counts(n_new)
    except FileNotFoundError:
        print(f"[{n_new:.0e}] gaps_N{n_new}.csv not found yet", file=sys.stderr)
        return False
    old = load_counts(n_old)

    li2_ratio = _li2(n_new) / _li2(n_old)
    total_emp = new.sum() / old.sum()

    print(f"\n[{n_new:.0e}]  vs  [{n_old:.0e}]")
    print(f"  total gaps:  {new.sum():>14d}  /  {old.sum():>14d}  "
          f"= {total_emp:.6f}")
    print(f"  Li_2 ratio (~ pi ratio):                       = "
          f"{li2_ratio:.6f}")
    print(f"  {'g':>4}  {'emp ratio':>11}  {'Wolf ratio':>11}  "
          f"{'emp/Wolf':>11}  {'flag':>6}")

    all_ok = True
    for g in SMALL_G:
        if g not in new.index or g not in old.index:
            continue
        nv, ov = int(new.loc[g]), int(old.loc[g])
        emp_ratio = nv / ov
        wolf_new = wolf_density(g, n_new)
        wolf_old = wolf_density(g, n_old)
        if wolf_old <= 0:
            continue
        wolf_ratio = wolf_new / wolf_old
        normalised = emp_ratio / wolf_ratio
        rel = abs(normalised - 1.0)
        flag = "" if rel <= TOLERANCE else "ANOMALY"
        if flag:
            all_ok = False
        print(f"  {g:>4}  {emp_ratio:>11.6f}  {wolf_ratio:>11.6f}  "
              f"{normalised:>11.6f}  {flag:>6}")

    # max gap check
    max_gap_new = int(new.index.max())
    max_gap_old = int(old.index.max())
    print(f"  max gap:     new={max_gap_new}   old={max_gap_old}")
    if max_gap_new < max_gap_old:
        print(f"  WARN: max gap decreased — extremely unlikely for larger N",
              file=sys.stderr)
        all_ok = False

    # log scan (overflow warning)
    log = ROOT / "run_extension" / "logs" / f"{n_new // 10**12}e12.log"
    # crude name; real log uses the original suffix; check both possibilities
    candidate_logs = list((ROOT / "run_extension" / "logs").glob("*.log"))
    for lf in candidate_logs:
        text = lf.read_text(errors="ignore")
        if "WARNING" in text and str(n_new) in text:
            print(f"  WARN: {lf} contains WARNING for N={n_new}",
                  file=sys.stderr)
            overflows.append(str(lf))

    return all_ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("N", nargs="?", type=int,
                    help="new N (decimal); omit with --all")
    ap.add_argument("--all", action="store_true",
                    help="check all NEW_N that are present")
    args = ap.parse_args()

    if args.all:
        targets = NEW_N
    elif args.N is not None:
        targets = [args.N]
    else:
        ap.error("provide N or --all")

    overall = True
    for n in targets:
        f = DATA / f"gaps_N{n}.csv"
        if not f.exists():
            print(f"[{n:.0e}] not yet generated, skipping")
            continue
        ok = check_one(n)
        overall = overall and ok

    print()
    print("OK" if overall else "FAILED")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
