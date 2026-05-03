"""
analyze_gaps.py

Analyses the outputs of gap_histogram.c:
  - gaps.csv    (histogram of gaps between consecutive primes)
  - records.csv (record gaps with merit ratio)

Produces figures + a markdown summary.

Usage:
  python3 analyze_gaps.py
  python3 analyze_gaps.py --gaps gaps.csv --records records.csv --out .
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

SCRIPT_VERSION = "4.0"

# Hardy-Littlewood twin prime constant (OEIS A005597)
C_2 = 0.6601618158468695739278121100145557784326233602847334133194484233354


# -----------------------------------------------------------------------------
# Theory
# -----------------------------------------------------------------------------

def hl_constant(g: int) -> float:
    """
    Hardy-Littlewood singular-series constant C_g for prime pairs (p, p+g).
    Returns 0 for odd g or g <= 0.

    C_g = 2 * C_2 * prod_{q | g, q odd prime} (q - 1) / (q - 2)
    """
    if g <= 0 or g % 2 != 0:
        return 0.0
    n = g
    # Strip the factor of 2 - it is not part of the odd-prime product.
    while n % 2 == 0:
        n //= 2
    correction = 1.0
    p = 3
    while p * p <= n:
        if n % p == 0:
            correction *= (p - 1) / (p - 2)
            while n % p == 0:
                n //= p
        p += 2
    if n > 1:
        correction *= (n - 1) / (n - 2)
    return 2 * C_2 * correction


def _li2(N: float) -> float:
    """Integral integral_2^N dt / ln^2 t (via scipy.integrate)."""
    from scipy import integrate
    val, _ = integrate.quad(lambda t: 1.0 / np.log(t) ** 2, 2.0, N)
    return float(val)


def hl_pair_count(g: int, N: float) -> float:
    """
    Hardy-Littlewood prediction of the number of prime pairs (p, p+g) with p <= N:
        #{p <= N : p, p+g prime} ~ C_g * integral_2^N dt / ln^2 t
    """
    Cg = hl_constant(g)
    if Cg == 0.0 or N <= 2:
        return 0.0
    return Cg * _li2(N)


def wolf_density(g: int, N: float) -> float:
    """
    Wolf (1998) estimate of the number of *consecutive* gaps of size g up to p ~ N:
        N_g(N) ~ C_g * (integral_2^N dt / ln^2 t) * exp(-g * C_g / ln N)

    The exponential factor corrects for the probability that no prime lies between
    p and p+g - which is exactly what the plain H-L count does not model.
    """
    Cg = hl_constant(g)
    if Cg == 0.0 or N <= 2:
        return 0.0
    lnN = np.log(N)
    return Cg * _li2(N) * np.exp(-g * Cg / lnN)


# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------

@dataclass
class Data:
    gaps: pd.DataFrame
    records: pd.DataFrame
    gap_counts: dict[int, int]
    total_gaps: int
    max_gap: int
    N_approx: float
    gaps_hash: str
    records_hash: str


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def estimate_N_from_prime_count(n: int) -> float:
    """
    Estimate of the n-th prime (= upper bound of the scan when total_gaps ~ n):
        p_n ~ n (ln n + ln ln n - 1)           (Dusart)
    """
    if n < 6:
        return float([2, 3, 5, 7, 11, 13][max(n - 1, 0)])
    ln_n = np.log(n)
    return float(n * (ln_n + np.log(ln_n) - 1.0))


def load_data(gaps_path: Path, records_path: Path) -> Data:
    gaps = pd.read_csv(gaps_path)
    records = pd.read_csv(records_path)

    # Filter out artefact row gap=1 (2->3 transition, not a gap between odd primes)
    records = records[records["gap"] >= 2].reset_index(drop=True)
    gaps = gaps[gaps["gap"] >= 2].reset_index(drop=True)

    gap_counts = dict(zip(gaps["gap"].astype(int), gaps["count"].astype(int)))
    total_gaps = int(gaps["count"].sum())

    return Data(
        gaps=gaps,
        records=records,
        gap_counts=gap_counts,
        total_gaps=total_gaps,
        max_gap=int(gaps["gap"].max()),
        N_approx=estimate_N_from_prime_count(total_gaps),
        gaps_hash=_file_hash(gaps_path),
        records_hash=_file_hash(records_path),
    )


def color_for_gap(g: int) -> str:
    if g % 6 == 0:
        return "#d62728"
    if g % 2 == 0:
        return "#1f77b4"
    return "#7f7f7f"


# -----------------------------------------------------------------------------
# Figures
# -----------------------------------------------------------------------------

def plot_histogram(d: Data, out: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    small = d.gaps[d.gaps["gap"] <= 60]
    colors = [color_for_gap(g) for g in small["gap"]]
    ax1.bar(small["gap"], small["count"], color=colors, width=1.5,
            edgecolor="black", linewidth=0.3)
    ax1.set_xlabel("gap $g$")
    ax1.set_ylabel("number of occurrences")
    ax1.set_title("Histogram of gaps $g \\leq 60$\n"
                  "(red: $6 \\mid g$, blue: even non-6)")
    ax1.grid(True, alpha=0.3, axis="y")

    ax2.scatter(d.gaps["gap"], d.gaps["count"], s=10, alpha=0.6, c="#1f77b4")
    for prim in [2, 6, 30, 210]:
        cnt = d.gap_counts.get(prim, 0)
        if cnt > 0:
            ax2.scatter(prim, cnt, s=120, c="red", marker="*", zorder=5,
                        edgecolors="black",
                        label="primorial" if prim == 2 else None)
    ax2.set_xlabel("gap $g$")
    ax2.set_ylabel("number of occurrences")
    ax2.set_title(f"Gap distribution (up to $p \\approx {d.N_approx:.2e}$)")
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.legend()
    ax2.grid(True, alpha=0.3, which="both")

    plt.tight_layout()
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()


def fit_records(records: pd.DataFrame, ln_min: float = 5.0):
    """Linear fit M ~ slope * ln p + intercept on later records."""
    mask = records["ln_p"] > ln_min
    if mask.sum() < 2:
        return None
    slope, intercept = np.polyfit(records.loc[mask, "ln_p"],
                                   records.loc[mask, "merit"], 1)
    return float(slope), float(intercept)


def fit_records_cramer_shanks(records: pd.DataFrame, ln_min: float = 5.0):
    """
    Cramer-Shanks-Granville: g_max(p) ~ c * (ln p)^2.
    Fit log(g) = c_log + alpha * log(ln p); slope alpha is free (expected ~ 2).
    """
    mask = records["ln_p"] > ln_min
    if mask.sum() < 2:
        return None
    x = np.log(records.loc[mask, "ln_p"].values)
    y = np.log(records.loc[mask, "gap"].values)
    slope, intercept = np.polyfit(x, y, 1)
    c = np.exp(intercept)
    return float(slope), float(c)


def plot_merit(d: Data, out: Path) -> tuple[float, float] | None:
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.scatter(d.records["ln_p"], d.records["merit"],
               s=60, c="#2ca02c", edgecolors="black", zorder=3,
               label="empirical records")

    ln_p_range = np.linspace(1, d.records["ln_p"].max() * 1.1, 200)
    ax.plot(ln_p_range, ln_p_range, "--", color="#ff7f0e", linewidth=2,
            label="Cramer: $M = \\ln p$")
    ax.fill_between(ln_p_range, ln_p_range, 2 * ln_p_range,
                    color="#ff7f0e", alpha=0.12,
                    label="Cramer-Granville band $[\\ln p,\\, 2\\ln p]$")

    fit = fit_records(d.records)
    if fit:
        slope, intercept = fit
        ax.plot(ln_p_range, slope * ln_p_range + intercept,
                ":", color="black", alpha=0.8, linewidth=2,
                label=f"fit: $M \\approx {slope:.3f}\\ln p {intercept:+.2f}$")

    ax.set_xlabel("$\\ln p$")
    ax.set_ylabel("merit $M = g / \\ln p$")
    ax.set_title("Merit of record gaps vs Cramer model")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    return fit


def plot_ratios(d: Data, out: Path, max_g: int = 12):
    """
    Compares empirical counts against Wolf's prediction (not plain H-L).
    Wolf's formula models consecutive gaps (which is what we measure).
    """
    N = d.N_approx
    compare_gaps = [g for g in range(2, max_g + 1, 2) if d.gap_counts.get(g, 0) > 0]

    emp = np.array([d.gap_counts[g] for g in compare_gaps], dtype=float)
    theo_wolf = np.array([wolf_density(g, N) for g in compare_gaps], dtype=float)
    theo_hl_pair = np.array([hl_pair_count(g, N) for g in compare_gaps], dtype=float)

    # Error bars: Poisson sigma = sqrt(count)
    err = np.sqrt(emp)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    x = np.arange(len(compare_gaps))
    width = 0.28
    ax1.bar(x - width, emp, width, yerr=err, capsize=3,
            label="empirical (consecutive)", color="#1f77b4")
    ax1.bar(x, theo_wolf, width,
            label="Wolf (consecutive)", color="#2ca02c", alpha=0.85)
    ax1.bar(x + width, theo_hl_pair, width,
            label="H-L (all pairs $p,p{+}g$)", color="#ff7f0e", alpha=0.85)
    ax1.set_xticks(x)
    ax1.set_xticklabels([str(g) for g in compare_gaps])
    ax1.set_xlabel("gap $g$")
    ax1.set_ylabel("count")
    ax1.set_title(f"Absolute counts at $p \\lesssim {N:.2e}$")
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3, axis="y")

    ratio_wolf = emp / theo_wolf
    colors = ["#2ca02c" if 0.9 <= r <= 1.1 else "#ff7f0e" for r in ratio_wolf]
    ax2.bar(x, ratio_wolf, color=colors, edgecolor="black", linewidth=0.5)
    ax2.axhline(1.0, color="black", linestyle="--", alpha=0.6)
    ax2.set_xticks(x)
    ax2.set_xticklabels([str(g) for g in compare_gaps])
    ax2.set_xlabel("gap $g$")
    ax2.set_ylabel("empirical / Wolf")
    ax2.set_title("Agreement with Wolf's model (consecutive gaps)")
    ax2.grid(True, alpha=0.3, axis="y")
    for i, r in enumerate(ratio_wolf):
        ax2.text(i, r + 0.01, f"{r:.3f}", ha="center", fontsize=8)

    plt.tight_layout()
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()

    return compare_gaps, emp, theo_wolf, theo_hl_pair


def chi2_test(emp: np.ndarray, theo: np.ndarray):
    """Pearson chi-square goodness-of-fit test after normalising theory to the empirical sum."""
    theo_norm = theo * emp.sum() / theo.sum()
    chi2 = float(np.sum((emp - theo_norm) ** 2 / theo_norm))
    dof = len(emp) - 1
    p = float(1.0 - stats.chi2.cdf(chi2, dof))
    return chi2, dof, p


def plot_champions(d: Data, out: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    top20 = d.gaps.nlargest(20, "count").sort_values("gap")
    colors_top = [color_for_gap(g) for g in top20["gap"]]
    ax1.bar([str(g) for g in top20["gap"]], top20["count"],
            color=colors_top, edgecolor="black", linewidth=0.3)
    ax1.set_xlabel("gap $g$")
    ax1.set_ylabel("number of occurrences")
    ax1.set_title("Top 20 most frequent gaps\n(red: $6 \\mid g$)")
    ax1.tick_params(axis="x", rotation=45)
    ax1.grid(True, alpha=0.3, axis="y")

    small = d.gaps[d.gaps["gap"] <= 60]
    mult_6 = small[small["gap"] % 6 == 0]
    not_6 = small[(small["gap"] % 6 != 0) & (small["gap"] % 2 == 0)]

    ax2.scatter(mult_6["gap"], mult_6["count"], s=80, c="#d62728",
                label="$6 \\mid g$", zorder=3, edgecolor="black")
    ax2.scatter(not_6["gap"], not_6["count"], s=80, c="#1f77b4",
                label="$g$ even, $6 \\nmid g$", zorder=3, edgecolor="black")
    ax2.set_xlabel("gap $g$")
    ax2.set_ylabel("number of occurrences")
    ax2.set_title("Preference for gaps divisible by 6")
    ax2.set_yscale("log")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()


# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

def write_summary(
    d: Data,
    out: Path,
    ratios: tuple,
    chi2_res: tuple,
    fit_lin: tuple | None,
    fit_csg: tuple | None,
) -> None:
    compare_gaps, emp, theo_wolf, theo_hl_pair = ratios
    chi2, dof, pval = chi2_res
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    lines = []
    lines.append("# Analysis of gaps between primes\n")
    lines.append(f"- **Script**: analyze_gaps.py v{SCRIPT_VERSION}")
    lines.append(f"- **Generated**: {now}")
    lines.append(f"- **gaps.csv hash**: `{d.gaps_hash}`")
    lines.append(f"- **records.csv hash**: `{d.records_hash}`\n")

    lines.append("## Range")
    lines.append(f"- Up to $p \\approx$ **{int(d.N_approx):,}**")
    lines.append(f"- Total number of gaps: **{d.total_gaps:,}**")
    lines.append(f"- Distinct gap sizes: {len(d.gaps)}")
    lines.append(f"- Largest gap: {d.max_gap}")
    lines.append(f"- Number of records: {len(d.records)}\n")

    lines.append("## Top 10 most frequent gaps")
    lines.append("| g | count | % | 6\\|g |")
    lines.append("|---|---:|---:|:---:|")
    for _, row in d.gaps.nlargest(10, "count").iterrows():
        g = int(row["gap"])
        cnt = int(row["count"])
        pct = 100 * cnt / d.total_gaps
        mod6 = "YES" if g % 6 == 0 else ""
        lines.append(f"| {g} | {cnt:,} | {pct:.2f} | {mod6} |")
    lines.append("")

    champion = d.gaps.loc[d.gaps["count"].idxmax()]
    lines.append("## Jumping champion")
    lines.append(f"- In this range: $g = {int(champion['gap'])}$ "
                 f"with {int(champion['count']):,} occurrences.")
    lines.append("- Erdos-Straus: for sufficiently large $N$ the JCs are primorials "
                 "(2, 6, 30, 210, 2310, ...). The $6 \\to 30$ transition is expected "
                 "near $p \\sim 10^{35}$.\n")

    lines.append("## Agreement with theory")
    lines.append("H-L: $\\#\\{p \\le N: p, p{+}g \\text{ prime}\\} "
                 "\\sim C_g \\int_2^N dt/\\ln^2 t$ (all pairs). "
                 "Wolf (1998) adds the factor $\\exp(-g C_g/\\ln N)$ for "
                 "consecutive gaps. For $g \\in \\{2,4\\}$ consecutive = pair "
                 "(no prime can lie between), so H-L applies directly. "
                 "For larger $g$, Wolf is reasonable when $\\ln N \\gg g$, which "
                 f"at $\\ln N \\approx {np.log(d.N_approx):.1f}$ is not yet fully "
                 "satisfied.\n")
    lines.append("| g | emp | Wolf | H-L (pair) | emp/Wolf |")
    lines.append("|---|---:|---:|---:|---:|")
    for g, e, w, h in zip(compare_gaps, emp, theo_wolf, theo_hl_pair):
        lines.append(f"| {g} | {int(e):,} | {w:,.0f} | {h:,.0f} | {e/w:.4f} |")
    lines.append("")
    lines.append(f"**Pearson chi-square test** (emp vs Wolf, normalised): "
                 f"chi2 = {chi2:.2f}, dof = {dof}, p = {pval:.3e}\n")

    lines.append("## Merit of records")
    if fit_lin:
        s, i = fit_lin
        lines.append(f"- Linear fit: $M \\approx {s:.3f}\\ln p {i:+.3f}$ "
                     f"(Cramer predicts slope 1.0 asymptotically)")
    if fit_csg:
        slope, c = fit_csg
        lines.append(f"- Cramer-Shanks-Granville $g \\sim c(\\ln p)^\\alpha$: "
                     f"$\\alpha \\approx {slope:.3f}$, $c \\approx {c:.4f}$ "
                     f"(theory: $\\alpha = 2$)")
    lines.append("")

    lines.append("## Last 5 records")
    lines.append("| g | p_start | merit |")
    lines.append("|---:|---:|---:|")
    for _, row in d.records.tail(5).iterrows():
        lines.append(f"| {int(row['gap'])} | {int(row['p_start']):,} | "
                     f"{row['merit']:.3f} |")
    lines.append("")

    lines.append("## Quasi-equivalence of g=2 and g=4")
    c2 = d.gap_counts.get(2, 0)
    c4 = d.gap_counts.get(4, 0)
    if c2 and c4:
        diff = abs(c2 - c4)
        # Poisson sigma interval
        sigma = np.sqrt(c2 + c4)
        z = diff / sigma
        lines.append(f"- $\\#\\{{g=2\\}}$ = {c2:,} (twin primes)")
        lines.append(f"- $\\#\\{{g=4\\}}$ = {c4:,} (cousin primes)")
        lines.append(f"- Difference: {diff:,} ({100*diff/c2:.4f}%), "
                     f"Poisson $z = {z:.2f}\\sigma$")
        lines.append("- H-L: $C_2 = C_4 = 2 C_2^{\\mathrm{twin}}$, "
                     "hence $\\pi_2(N) \\sim \\pi_4(N)$.\n")

    out.write_text("\n".join(lines))


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Analyze prime gap histograms.")
    p.add_argument("--gaps", type=Path, default=Path("gaps.csv"))
    p.add_argument("--records", type=Path, default=Path("records.csv"))
    p.add_argument("--out", type=Path, default=Path("."))
    p.add_argument("--max-ratio-g", type=int, default=12,
                   help="Max g for FIG3 comparison against Wolf.")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    d = load_data(args.gaps, args.records)
    print(f"Loaded: {len(d.gaps)} sizes, {d.total_gaps:,} gaps, "
          f"{len(d.records)} records, up to p ~ {d.N_approx:.3e}")

    plot_histogram(d, args.out / "fig1_histogram.png")
    print("  fig1_histogram.png")

    fit_lin = plot_merit(d, args.out / "fig2_merit.png")
    print("  fig2_merit.png")

    ratios = plot_ratios(d, args.out / "fig3_ratios.png",
                         max_g=args.max_ratio_g)
    print("  fig3_ratios.png")

    plot_champions(d, args.out / "fig4_champions.png")
    print("  fig4_champions.png")

    _, emp, theo_wolf, _ = ratios
    chi2_res = chi2_test(emp, theo_wolf)
    fit_csg = fit_records_cramer_shanks(d.records)

    write_summary(d, args.out / "summary.md",
                  ratios, chi2_res, fit_lin, fit_csg)
    print("  summary.md")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
