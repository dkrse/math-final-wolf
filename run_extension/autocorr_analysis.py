"""
autocorr_analysis.py — analysis of the rho(1, N) profile across multiple N.

Reads autocorr_N*.json files from the same directory and:
  1. Prints a table of rho(1..10) per N.
  2. Fits rho(1, N) as a function of log N (constant vs c/log N
     vs additive scaling).
  3. Plots rho(1) vs N (log axes) with the fits.
  4. Plots the rho(k) profile for each N (sub-plot grid).
  5. Saves a summary to autocorr_summary.json.

Usage:
  python run_extension/autocorr_analysis.py
"""
from __future__ import annotations
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

WORK = Path(__file__).resolve().parent / "autocorr"


def load_all() -> pd.DataFrame:
    rows = []
    for f in sorted(WORK.glob("autocorr_N*.json")):
        d = json.loads(f.read_text())
        rho = d["rho"]   # length max_lag+1 (rho[0] = 1.0)
        rec = {
            "N": d["N"],
            "n_gaps": d["n_gaps"],
            "mean_g": d["mean_g"],
            "var_g": d["var_g"],
            "wall_seconds": d["wall_seconds"],
        }
        for k in range(1, len(rho)):
            rec[f"rho_{k}"] = rho[k]
        rows.append(rec)
    df = pd.DataFrame(rows).sort_values("N").reset_index(drop=True)
    return df


def fit_rho1(df: pd.DataFrame) -> dict:
    """Fit three models for rho(1) as a function of N."""
    N = df["N"].to_numpy(dtype=float)
    rho1 = df["rho_1"].to_numpy(dtype=float)
    lnN = np.log(N)

    # Model A: constant rho(1) = a
    a_const = float(np.mean(rho1))
    rss_const = float(np.sum((rho1 - a_const) ** 2))

    # Model B: rho(1) = c / ln N
    def b_model(x, c):
        return c / x
    popt_b, _ = curve_fit(b_model, lnN, rho1, p0=[-1.0])
    rss_b = float(np.sum((rho1 - b_model(lnN, *popt_b)) ** 2))

    # Model C: rho(1) = a + b / ln N (additive scaling)
    def c_model(x, a, b):
        return a + b / x
    popt_c, _ = curve_fit(c_model, lnN, rho1, p0=[0.0, -1.0])
    rss_c = float(np.sum((rho1 - c_model(lnN, *popt_c)) ** 2))

    return {
        "model_const":    {"a": a_const, "rss": rss_const},
        "model_c_over_lnN": {"c": float(popt_b[0]), "rss": rss_b},
        "model_a_plus_b_over_lnN": {
            "a": float(popt_c[0]),
            "b": float(popt_c[1]),
            "rss": rss_c
        },
    }


def main() -> None:
    if not WORK.exists():
        print(f"ERROR: {WORK} not found")
        return
    df = load_all()
    if df.empty:
        print(f"No autocorr_N*.json found in {WORK}")
        return

    print("=" * 70)
    print("rho(k) per N")
    print("=" * 70)
    cols = ["N", "n_gaps", "mean_g", "var_g"] + [
        f"rho_{k}" for k in range(1, 11)
    ]
    show = df[cols].copy()
    show["N"] = show["N"].apply(lambda x: f"{x:.0e}")
    print(show.to_string(index=False))

    print()
    fits = fit_rho1(df)
    print("=" * 70)
    print("rho(1) vs N — model fits")
    print("=" * 70)
    print(f"  const:                rho(1) = {fits['model_const']['a']:+.5f}    "
          f"RSS = {fits['model_const']['rss']:.3e}")
    print(f"  c/ln N:               c = {fits['model_c_over_lnN']['c']:+.4f}        "
          f"RSS = {fits['model_c_over_lnN']['rss']:.3e}")
    print(f"  a + b/ln N:           a = {fits['model_a_plus_b_over_lnN']['a']:+.5f}, "
          f"b = {fits['model_a_plus_b_over_lnN']['b']:+.4f}, "
          f"RSS = {fits['model_a_plus_b_over_lnN']['rss']:.3e}")

    # --- Plot rho(1) vs N ---
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))

    Nvals = df["N"].to_numpy(dtype=float)
    rho1 = df["rho_1"].to_numpy(dtype=float)
    lnN = np.log(Nvals)

    ax[0].scatter(Nvals, rho1, s=80, color="C3", zorder=3, label="data")
    Nplot = np.logspace(np.log10(Nvals.min() * 0.5),
                        np.log10(Nvals.max() * 2), 200)
    lnNplot = np.log(Nplot)
    a, b = fits["model_a_plus_b_over_lnN"]["a"], \
        fits["model_a_plus_b_over_lnN"]["b"]
    ax[0].plot(Nplot, a + b / lnNplot, "C0--",
               label=f"a + b/ln N: a={a:+.4f}, b={b:+.3f}")
    c = fits["model_c_over_lnN"]["c"]
    ax[0].plot(Nplot, c / lnNplot, "C1:", label=f"c/ln N: c={c:+.3f}")
    ax[0].axhline(fits["model_const"]["a"], color="C2", linestyle="-.",
                  alpha=0.6,
                  label=f"const: {fits['model_const']['a']:+.4f}")
    ax[0].set_xscale("log")
    ax[0].set_xlabel("N")
    ax[0].set_ylabel(r"$\rho(1)$")
    ax[0].set_title(r"Lag-1 autocorrelation vs $N$")
    ax[0].axhline(0, color="k", linewidth=0.5)
    ax[0].grid(alpha=0.3)
    ax[0].legend(loc="best")

    # --- Plot rho(k) profile per N ---
    for _, row in df.iterrows():
        ks = list(range(1, 11))
        rhos = [row[f"rho_{k}"] for k in ks]
        ax[1].plot(ks, rhos, "o-", label=f"N=10^{int(np.log10(row['N']))}",
                   alpha=0.8)
    ax[1].axhline(0, color="k", linewidth=0.5)
    ax[1].set_xlabel("lag k")
    ax[1].set_ylabel(r"$\rho(k)$")
    ax[1].set_title(r"Autocorrelation profile $\rho(k)$ per $N$")
    ax[1].grid(alpha=0.3)
    ax[1].legend(loc="best", fontsize=9)

    fig.tight_layout()
    out_png = WORK / "autocorr_profile.png"
    fig.savefig(out_png, dpi=120, bbox_inches="tight")
    print(f"\nSaved {out_png}")

    # --- Save summary ---
    summary = {
        "data": [
            {**row.to_dict(),
             "N_log10": float(np.log10(row["N"])),
             }
            for _, row in df.iterrows()
        ],
        "fits": fits,
    }
    out_json = WORK / "autocorr_summary.json"
    out_json.write_text(json.dumps(summary, indent=2, default=float))
    print(f"Saved {out_json}")


if __name__ == "__main__":
    main()
