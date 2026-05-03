"""
autocorr_decay_analysis.py — power-law fit rho(k) ~ A * k^(-beta) per N.

Motivation: D.1 showed that rho(2) >> rho(1)^2 (single-step Markov is
falsified) and the log-log profile of rho(k) looks linear. Here we fit a
power law and check:
  (a) stability of the exponent beta across 5 N values,
  (b) whether A * rho(1) is a constant function of N (for normalisation),
  (c) comparison with alternative decay forms (geometric, stretched-exp).

Outputs:
  decay_summary.json  — per-N coefficients and fit quality
  decay_profile.png   — log-log rho(k) per N with fits
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

WORK = Path(__file__).resolve().parent / "autocorr"


def load_all() -> list[dict]:
    out = []
    for f in sorted(WORK.glob("autocorr_N*.json")):
        d = json.loads(f.read_text())
        out.append(d)
    out.sort(key=lambda d: d["N"])
    return out


def fit_powerlaw(rho: list[float], k_min: int = 1, k_max: int = 10) -> dict:
    """Fit |rho(k)| = A * k^(-beta) on k in [k_min, k_max]."""
    ks = np.arange(k_min, k_max + 1)
    rs = np.array([abs(rho[k]) for k in ks])
    # log-linearization
    logk = np.log(ks)
    logr = np.log(rs)
    # least-squares fit
    A_mat = np.column_stack([logk, np.ones_like(logk)])
    coef, residuals, _, _ = np.linalg.lstsq(A_mat, logr, rcond=None)
    slope, intercept = coef
    A = float(np.exp(intercept))
    beta = float(-slope)
    # RSS
    fit = A * ks ** (-beta)
    rss = float(np.sum((rs - fit) ** 2))
    return {"A": A, "beta": beta, "rss": rss, "k_min": k_min, "k_max": k_max}


def fit_geometric(rho: list[float], k_min: int = 1, k_max: int = 10) -> dict:
    """Fit |rho(k)| = A * r^k (pure geometric, like Markov)."""
    ks = np.arange(k_min, k_max + 1)
    rs = np.array([abs(rho[k]) for k in ks])
    logr = np.log(rs)
    A_mat = np.column_stack([ks, np.ones_like(ks, dtype=float)])
    coef, *_ = np.linalg.lstsq(A_mat, logr, rcond=None)
    log_r, intercept = coef
    A = float(np.exp(intercept))
    r = float(np.exp(log_r))
    fit = A * r ** ks
    rss = float(np.sum((rs - fit) ** 2))
    return {"A": A, "r": r, "rss": rss, "k_min": k_min, "k_max": k_max}


def fit_stretched_exp(rho: list[float], k_min: int = 1,
                      k_max: int = 10) -> dict:
    """Fit |rho(k)| = A * exp(-alpha * k^theta) (stretched-exponential)."""
    ks_int = np.arange(k_min, k_max + 1)
    ks = ks_int.astype(float)
    rs = np.array([abs(rho[int(k)]) for k in ks_int])

    def model(k, A, alpha, theta):
        return A * np.exp(-alpha * k ** theta)

    try:
        popt, _ = curve_fit(model, ks, rs, p0=[0.04, 1.0, 0.5],
                            maxfev=5000)
        fit = model(ks, *popt)
        rss = float(np.sum((rs - fit) ** 2))
        return {"A": float(popt[0]), "alpha": float(popt[1]),
                "theta": float(popt[2]), "rss": rss}
    except Exception as e:
        return {"error": str(e), "rss": float("inf")}


def main() -> None:
    data = load_all()
    print("=" * 78)
    print("Power-law fit |rho(k)| = A * k^(-beta),  k in [1, 10]")
    print("=" * 78)
    print(f"{'N':>10} {'A':>10} {'beta':>10} {'A*|rho(1)|':>12} "
          f"{'RSS':>11} {'sign':>8}")
    summary = {"per_N": [], "trend": {}}
    betas = []
    Ns = []
    for d in data:
        rho = d["rho"]
        N = d["N"]
        pl = fit_powerlaw(rho)
        gm = fit_geometric(rho)
        se = fit_stretched_exp(rho)
        # sign pattern: how many lags have rho(k) negative?
        signs = [1 if rho[k] < 0 else 0 for k in range(1, 11)]
        # signs[i] = 1 if rho(i+1) < 0
        n_neg = sum(signs)
        rec = {
            "N": N,
            "lnN": float(np.log(N)),
            "rho_1": rho[1],
            "powerlaw": pl,
            "geometric": gm,
            "stretched_exp": se,
            "n_neg_signs_lag1to10": n_neg,
        }
        summary["per_N"].append(rec)
        betas.append(pl["beta"])
        Ns.append(N)
        print(f"{N:>10.0e} {pl['A']:>10.5f} {pl['beta']:>10.4f} "
              f"{pl['A'] * abs(rho[1]):>12.5f} {pl['rss']:>11.3e} "
              f"{n_neg:>4d}/10")
    print()

    # Beta vs N — is it stable?
    print("Stability of beta across N:")
    betas = np.array(betas)
    Ns = np.array(Ns, dtype=float)
    print(f"  beta: min = {betas.min():.4f}, max = {betas.max():.4f}, "
          f"mean = {betas.mean():.4f}, std = {betas.std():.4f}")
    print(f"  spread (max - min) / mean: "
          f"{(betas.max() - betas.min()) / betas.mean() * 100:.2f}%")
    summary["trend"]["beta_min"] = float(betas.min())
    summary["trend"]["beta_max"] = float(betas.max())
    summary["trend"]["beta_mean"] = float(betas.mean())
    summary["trend"]["beta_std"] = float(betas.std())

    print()
    print("Comparison RSS (lower = better fit):")
    print(f"  {'N':>10} {'powerlaw':>12} {'geometric':>12} "
          f"{'stretched-exp':>14}")
    for d, rec in zip(data, summary["per_N"]):
        print(f"  {d['N']:>10.0e} {rec['powerlaw']['rss']:>12.3e} "
              f"{rec['geometric']['rss']:>12.3e} "
              f"{rec['stretched_exp']['rss']:>14.3e}")

    # Save
    out_json = WORK / "decay_summary.json"
    out_json.write_text(json.dumps(summary, indent=2, default=float))
    print(f"\nSaved {out_json}")

    # --- Plot ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: log-log rho(k) per N + power-law fit
    ax = axes[0]
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(data)))
    for d, c in zip(data, colors):
        rho = d["rho"]
        ks = np.arange(1, 11)
        rs = np.array([abs(rho[k]) for k in ks])
        ax.plot(ks, rs, "o-", color=c, alpha=0.85,
                label=f"N=10^{int(np.log10(d['N']))}")
        # fit line
        pl = fit_powerlaw(rho)
        kfit = np.linspace(1, 10, 100)
        ax.plot(kfit, pl["A"] * kfit ** (-pl["beta"]), "--",
                color=c, alpha=0.5)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("lag k")
    ax.set_ylabel(r"$|\rho(k)|$")
    ax.set_title(r"$|\rho(k)|$ vs $k$ (log-log) with power-law fits")
    ax.grid(alpha=0.3, which="both")
    ax.legend(loc="best", fontsize=9)

    # Right: beta vs N
    ax = axes[1]
    ax.plot(Ns, betas, "o-", color="C3", markersize=10)
    ax.set_xscale("log")
    ax.set_xlabel("N")
    ax.set_ylabel(r"power-law exponent $\beta$")
    ax.set_title(r"Stability of $\beta$ in $|\rho(k)| \sim k^{-\beta}$")
    ax.grid(alpha=0.3)
    ax.axhline(betas.mean(), color="C0", linestyle="--", alpha=0.5,
               label=f"mean = {betas.mean():.4f}")
    ax.legend()

    fig.tight_layout()
    out_png = WORK / "decay_profile.png"
    fig.savefig(out_png, dpi=120, bbox_inches="tight")
    print(f"Saved {out_png}")


if __name__ == "__main__":
    main()
