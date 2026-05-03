"""
analyze_sequence.py

Sequential analysis of gaps between primes.
Unlike analyze_gaps.py (which works with a histogram), this script needs the
STREAM of gaps in the order they occur:

    gap_stream.csv:   p_start,gap

Produced via `./main-csv <N> <stride>` (stride >= 1).

Produces three figures + an appendix to the summary:
  fig5_champions.png   - jumping-champion transitions
  fig6_gpy.png         - GPY / running minimum of g_n / ln p_n
  fig7_autocorr.png    - autocorrelation of gaps (empirical vs shuffled)

Usage:
  python3 analyze_sequence.py
  python3 analyze_sequence.py --stream gap_stream.csv --out .
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------------------------------------------------------
# Data
# -----------------------------------------------------------------------------

def load_stream(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[df["gap"] >= 2].reset_index(drop=True)
    if len(df) < 100:
        raise ValueError(
            f"Stream {path} is too short ({len(df)} rows). "
            "Rerun the C program with a smaller stride."
        )
    return df


# -----------------------------------------------------------------------------
# 1. Jumping champions
# -----------------------------------------------------------------------------

def plot_jumping_champions(df: pd.DataFrame, out: Path) -> list[tuple[float, int]]:
    """
    Tracks the most frequent gap in the running window [2, x] as a function of x.
    Returns the list of transitions (x, new_champion).

    The result should be a staircase function 2 -> 4 -> 6 -> ... whose
    transitions we verify empirically.
    """
    p = df["p_start"].to_numpy()
    g = df["gap"].to_numpy()

    # Running histogram realised via np.bincount-style increments over windows.
    max_g = int(g.max()) + 1
    counts = np.zeros(max_g, dtype=np.int64)

    # Logarithmic grid of points at which we record the current champion.
    p_min = max(float(p[0]), 10.0)
    p_max = float(p[-1])
    n_points = 400
    grid = np.geomspace(p_min, p_max, n_points)

    current_champion = 0
    transitions: list[tuple[float, int]] = []
    champion_history: list[tuple[float, int]] = []

    idx = 0
    for x in grid:
        while idx < len(p) and p[idx] <= x:
            counts[g[idx]] += 1
            idx += 1
        if counts.sum() == 0:
            continue
        champ = int(counts.argmax())
        if champ != current_champion:
            transitions.append((float(x), champ))
            current_champion = champ
        champion_history.append((float(x), champ))

    # Plot
    fig, ax = plt.subplots(figsize=(11, 5.5))
    xs = [h[0] for h in champion_history]
    ys = [h[1] for h in champion_history]
    ax.step(xs, ys, where="post", linewidth=2, color="#1f77b4")
    ax.set_xscale("log")
    ax.set_xlabel("$x$ (upper bound of the interval)")
    ax.set_ylabel("jumping champion (most frequent gap in $[2, x]$)")
    ax.set_title("Jumping-champion transitions\n"
                 "Erdos-Straus conjectures the primorial sequence 2, 6, 30, 210, ...")
    ax.grid(True, alpha=0.3, which="both")

    # Only vertical lines without textual labels (they overlap when
    # transitions oscillate). The transition list is shown in the text box.
    for x_t, _ in transitions:
        ax.axvline(x_t, color="red", linestyle=":", alpha=0.4, linewidth=0.8)

    if transitions:
        lines = ["Transitions (x -> champion):"]
        for x_t, champ in transitions:
            lines.append(f"  {x_t:.3e}  ->  g = {champ}")
        ax.text(0.02, 0.98, "\n".join(lines),
                transform=ax.transAxes, fontsize=8,
                verticalalignment="top", family="monospace",
                bbox=dict(boxstyle="round", facecolor="white",
                          edgecolor="gray", alpha=0.9))

    ax.set_yticks(sorted(set(ys)))
    ax.margins(y=0.15)
    plt.tight_layout()
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    return transitions


# -----------------------------------------------------------------------------
# 2. GPY / running minimum of g_n / ln p_n
# -----------------------------------------------------------------------------

def plot_gpy(df: pd.DataFrame, out: Path) -> tuple[float, float]:
    """
    Plots:
      - scatter of ratios g_n / ln p_n (sampled),
      - running minimum as a function of p_n.

    Returns (min_ratio, p_at_min).
    """
    p = df["p_start"].to_numpy(dtype=float)
    g = df["gap"].to_numpy(dtype=float)
    mask = p > 2
    p = p[mask]
    g = g[mask]

    ratio = g / np.log(p)
    running_min = np.minimum.accumulate(ratio)

    fig, ax = plt.subplots(figsize=(11, 5))

    # Scatter (at most 5000 points for readability)
    if len(p) > 5000:
        sel = np.random.default_rng(0).choice(len(p), 5000, replace=False)
        sel.sort()
    else:
        sel = np.arange(len(p))
    ax.scatter(p[sel], ratio[sel], s=4, alpha=0.25, c="#7f7f7f",
               label="$g_n / \\ln p_n$ (sample)")

    ax.plot(p, running_min, linewidth=2, color="#d62728",
            label="running minimum")
    ax.axhline(1.0, color="black", linestyle="--", alpha=0.5,
               label="average (PNT: $g_n \\sim \\ln p_n$)")

    ax.set_xscale("log")
    ax.set_xlabel("$p_n$")
    ax.set_ylabel("$g_n / \\ln p_n$")
    ax.set_title("Tightest gaps (Goldston-Pintz-Yildirim context)\n"
                 "GPY theorem (2009): $\\liminf g_n / \\ln p_n = 0$")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3, which="both")

    plt.tight_layout()
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()

    imin = int(running_min.argmin())
    return float(running_min[imin]), float(p[imin])


# -----------------------------------------------------------------------------
# 3. Autocorrelation of gaps
# -----------------------------------------------------------------------------

def plot_autocorr(df: pd.DataFrame, out: Path, max_lag: int = 20
                  ) -> tuple[np.ndarray, np.ndarray]:
    """
    Compares the autocorrelation rho(k) of the gap sequence against rho(k) of a
    randomly shuffled version of the same gaps. If gaps are independent, the
    empirical curve should lie within the shuffled noise. If real correlation
    is present, the empirical curve sits outside that noise band.
    """
    g = df["gap"].to_numpy(dtype=float)
    g = g - g.mean()
    var = g.var()

    def acorr(x: np.ndarray, max_lag: int) -> np.ndarray:
        out = np.zeros(max_lag + 1)
        for k in range(max_lag + 1):
            if k == 0:
                out[k] = 1.0
            else:
                out[k] = np.mean(x[:-k] * x[k:]) / var
        return out

    rho_emp = acorr(g, max_lag)

    rng = np.random.default_rng(42)
    n_shuffles = 20
    rho_shuffled = np.zeros((n_shuffles, max_lag + 1))
    for i in range(n_shuffles):
        shuffled = g.copy()
        rng.shuffle(shuffled)
        rho_shuffled[i] = acorr(shuffled, max_lag)

    shuf_mean = rho_shuffled.mean(axis=0)
    shuf_std = rho_shuffled.std(axis=0)

    fig, ax = plt.subplots(figsize=(11, 5))
    lags = np.arange(max_lag + 1)

    ax.fill_between(lags, shuf_mean - 2 * shuf_std, shuf_mean + 2 * shuf_std,
                    color="#7f7f7f", alpha=0.3,
                    label="shuffled $\\pm 2\\sigma$ (null)")
    ax.plot(lags, shuf_mean, color="#7f7f7f", linestyle="--",
            label="shuffled mean")
    ax.plot(lags[1:], rho_emp[1:], marker="o", color="#d62728",
            label="empirical $\\rho(k)$")
    ax.axhline(0, color="black", alpha=0.4)

    ax.set_xlabel("lag $k$")
    ax.set_ylabel("autocorrelation $\\rho(k)$")
    ax.set_title("Autocorrelation of prime gaps\n"
                 "Deviation from the shuffled null = evidence of structural dependence")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()

    return rho_emp, shuf_std


# -----------------------------------------------------------------------------
# Summary append
# -----------------------------------------------------------------------------

def append_summary(
    out: Path,
    n_stream: int,
    transitions: list[tuple[float, int]],
    gpy: tuple[float, float],
    rho_emp: np.ndarray,
    shuf_std: np.ndarray,
) -> None:
    lines = ["\n\n---\n",
             "# Sequential analysis (analyze_sequence.py)\n",
             f"- Number of gaps in the stream: **{n_stream:,}**\n",
             "## Jumping-champion transitions (fig5)\n"]
    if transitions:
        lines.append("| x | new champion |")
        lines.append("|---|---:|")
        for x_t, champ in transitions:
            lines.append(f"| {x_t:.3e} | {champ} |")
    else:
        lines.append("_No transitions captured - range may be too small or stride too large._")
    lines.append("")

    min_ratio, p_at_min = gpy
    lines.append("## GPY / running minimum (fig6)")
    lines.append(f"- Smallest ratio $g_n / \\ln p_n = {min_ratio:.4f}$ "
                 f"at $p \\approx {p_at_min:.3e}$")
    lines.append("- Goldston-Pintz-Yildirim theorem (2009): lim inf = 0.\n")

    lines.append("## Autocorrelation (fig7)")
    lines.append("| lag | emp rho | shuffled sigma | z |")
    lines.append("|---:|---:|---:|---:|")
    for k in range(1, min(11, len(rho_emp))):
        z = rho_emp[k] / shuf_std[k] if shuf_std[k] > 0 else 0.0
        lines.append(f"| {k} | {rho_emp[k]:+.4f} | {shuf_std[k]:.4f} | {z:+.2f} |")
    lines.append("")
    lines.append("Large $|z|$ (e.g. $> 3$) indicates structural deviations from "
                 "Cramer-style independence.")

    with out.open("a") as f:
        f.write("\n".join(lines))


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sequential analysis of prime gaps.")
    p.add_argument("--stream", type=Path, default=Path("gap_stream.csv"))
    p.add_argument("--out", type=Path, default=Path("."))
    p.add_argument("--summary", type=Path, default=Path("summary.md"),
                   help="Markdown file to which the results are appended.")
    p.add_argument("--max-lag", type=int, default=20)
    p.add_argument("--no-append", action="store_true",
                   help="Do not append to summary.md, only generate figures.")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    if not args.stream.exists():
        print(f"Error: {args.stream} does not exist.\n"
              f"Run the C program with a stride, e.g.:\n"
              f"  ./main-csv 1e9 100",
              file=sys.stderr)
        return 1

    df = load_stream(args.stream)
    print(f"Loaded: {len(df):,} gaps from stream "
          f"(p from {df['p_start'].min()} to {df['p_start'].max():.3e})")

    transitions = plot_jumping_champions(df, args.out / "fig5_champions.png")
    print(f"  fig5_champions.png ({len(transitions)} transitions)")

    gpy = plot_gpy(df, args.out / "fig6_gpy.png")
    print(f"  fig6_gpy.png (min ratio = {gpy[0]:.4f} at p = {gpy[1]:.3e})")

    rho_emp, shuf_std = plot_autocorr(df, args.out / "fig7_autocorr.png",
                                       max_lag=args.max_lag)
    print(f"  fig7_autocorr.png (rho(1) = {rho_emp[1]:+.4f})")

    if not args.no_append and args.summary.exists():
        append_summary(args.summary, len(df), transitions, gpy,
                       rho_emp, shuf_std)
        print(f"  appended to {args.summary}")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
