"""
Pre-computation: which (N, g) pairs will pass the primary / relaxed filter
on the extended dataset, given the Hardy-Littlewood + Wolf model?

Outputs:
  - filter_prediction.csv   long-form (N, g, ω, C_g, ρ, N_g_pred, passes_*)
  - filter_summary.txt      human-readable summary by ω(g) and filter regime
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app-python"))
from analyze_gaps import hl_constant, _li2, wolf_density  # noqa: E402


def omega(g: int) -> int:
    """Number of distinct prime divisors of g."""
    if g <= 1:
        return 0
    n, count = g, 0
    p = 2
    while p * p <= n:
        if n % p == 0:
            count += 1
            while n % p == 0:
                n //= p
        p += 1
    if n > 1:
        count += 1
    return count


# Existing N values (from ml_data/) plus the 4 planned extensions.
N_EXISTING = [
    100_000, 196_841, 387_467, 762_698, 1_501_310, 2_955_209, 5_817_091,
    11_450_475, 22_539_339, 44_366_873, 87_332_616, 171_907_220,
    338_385_515, 666_084_629, 1_311_133_937, 2_580_861_540,
    5_080_218_046, 10_000_000_000, 30_000_000_000, 70_000_000_000,
    100_000_000_000, 300_000_000_000, 1_000_000_000_000,
    3_000_000_000_000, 10_000_000_000_000,
]
N_NEW = [30_000_000_000_000, 100_000_000_000_000,
         300_000_000_000_000, 1_000_000_000_000_000]
N_ALL = N_EXISTING + N_NEW

G_VALUES = list(range(2, 252, 2))   # cover ω=4 candidate g=210

PRIMARY_RHO = (0.05, 1.10)
RELAXED_RHO = (0.05, 4.00)
N_G_THRESHOLD = 100


def main() -> None:
    rows = []
    for g in G_VALUES:
        Cg = hl_constant(g)
        if Cg == 0.0:
            continue
        og = omega(g)
        for N in N_ALL:
            lnN = np.log(N)
            rho = g * Cg / lnN
            N_g_pred = wolf_density(g, N)
            in_primary = (PRIMARY_RHO[0] <= rho <= PRIMARY_RHO[1]
                          and N_g_pred >= N_G_THRESHOLD)
            in_relaxed = (RELAXED_RHO[0] <= rho <= RELAXED_RHO[1]
                          and N_g_pred >= N_G_THRESHOLD)
            rows.append({
                "N": N, "g": g, "omega": og, "C_g": Cg,
                "rho": rho, "N_g_pred": N_g_pred,
                "is_new_N": N in N_NEW,
                "passes_primary": in_primary,
                "passes_relaxed": in_relaxed,
            })

    df = pd.DataFrame(rows)
    out_csv = Path(__file__).parent / "filter_prediction.csv"
    df.to_csv(out_csv, index=False)
    print(f"Wrote {out_csv}  ({len(df)} rows)")

    # ----- Summary ------------------------------------------------------------
    def block(title, mask, columns_n=("is_new_N", False)):
        sub = df[mask].copy()
        if sub.empty:
            return f"{title}: NONE\n"
        out = [f"{title}: n={len(sub)}"]
        out.append(f"  ω distribution: "
                   f"{sub.groupby('omega').size().to_dict()}")
        out.append(f"  unique g values: "
                   f"{sorted(sub['g'].unique())}")
        out.append(f"  unique N values: {len(sub['N'].unique())}")
        return "\n".join(out) + "\n"

    parts = []
    parts.append("=" * 70)
    parts.append("FILTER PREDICTION SUMMARY")
    parts.append("=" * 70)
    parts.append(f"\nN_existing: {len(N_EXISTING)}, "
                 f"N_new: {len(N_NEW)}, N_total: {len(N_ALL)}")
    parts.append(f"g grid: even {G_VALUES[0]}..{G_VALUES[-1]}\n")

    parts.append("--- PRIMARY FILTER  ρ ∈ [0.05, 1.10],  N_g ≥ 100 ---\n")
    parts.append(block("Total surviving (all N)",
                       df["passes_primary"]))
    parts.append(block("Existing-N only",
                       df["passes_primary"] & ~df["is_new_N"]))
    parts.append(block("New-N only (gain from extension)",
                       df["passes_primary"] & df["is_new_N"]))

    parts.append("\n--- RELAXED FILTER  ρ ∈ [0.05, 4.00],  N_g ≥ 100 ---\n")
    parts.append(block("Total surviving (all N)",
                       df["passes_relaxed"]))
    parts.append(block("Existing-N only",
                       df["passes_relaxed"] & ~df["is_new_N"]))
    parts.append(block("New-N only (gain from extension)",
                       df["passes_relaxed"] & df["is_new_N"]))

    # --- Per-N table for new extensions -------------------------------------
    parts.append("\n--- NEW N VALUES — per-N gain ---\n")
    parts.append(f"{'N':>16}  {'pri+':>5}  {'rel+':>5}  "
                 f"{'rel ω=3':>8}  {'rel ω=4':>8}")
    for N in N_NEW:
        sub = df[df["N"] == N]
        pri = int(sub["passes_primary"].sum())
        rel = int(sub["passes_relaxed"].sum())
        rel3 = int(((sub["omega"] == 3) & sub["passes_relaxed"]).sum())
        rel4 = int(((sub["omega"] == 4) & sub["passes_relaxed"]).sum())
        parts.append(f"{N:>16d}  {pri:>5d}  {rel:>5d}  "
                     f"{rel3:>8d}  {rel4:>8d}")

    # --- Smallest g per ω that ever enters each filter ----------------------
    parts.append("\n--- SMALLEST g THAT ENTERS BY ω ---\n")
    for omega_val in [1, 2, 3, 4]:
        for label, mask_col in [("primary", "passes_primary"),
                                ("relaxed", "passes_relaxed")]:
            sub = df[(df["omega"] == omega_val) & df[mask_col]]
            if sub.empty:
                parts.append(f"  ω={omega_val} {label}: NEVER")
            else:
                g_min = sub["g"].min()
                N_min = sub[sub["g"] == g_min]["N"].min()
                parts.append(f"  ω={omega_val} {label}: smallest g = {g_min} "
                             f"(first enters at N = {N_min:.0e})")

    out_txt = Path(__file__).parent / "filter_summary.txt"
    out_txt.write_text("\n".join(parts) + "\n")
    print(f"Wrote {out_txt}")
    print()
    print("\n".join(parts))


if __name__ == "__main__":
    main()
