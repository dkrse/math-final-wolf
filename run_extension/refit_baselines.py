"""Refit M1* a M3 voči 4 baselinom (Sestak, Wolf2014, Wolf2018, Cohen)
na rovnakom dataset n=169. Filter (rho_sestak in [0.05, 1.10]) zachovaný
pre porovnateľnosť s pôvodnou v3 analýzou.
"""
from __future__ import annotations
import math, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import optimize
import primesieve

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wolf_formulas import hl_correct, li2, BASELINES

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "ml_data"
OUT_DIR = ROOT / "outputs" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def omega(n: int) -> int:
    if n <= 1: return 0
    c, d = 0, 2
    while d * d <= n:
        if n % d == 0:
            c += 1
            while n % d == 0: n //= d
        d += 1
    if n > 1: c += 1
    return c


def build_dataset() -> pd.DataFrame:
    files = sorted(DATA_DIR.glob("gaps_N*.csv"))
    rows = []
    for f in files:
        N = int(f.stem.replace("gaps_N", ""))
        df = pd.read_csv(f)
        lnN = math.log(N)
        lnlnN = math.log(lnN)
        li2N = li2(N)
        pi_N = int(df["count"].sum()) + 1
        for _, r in df.iterrows():
            g, emp = int(r["gap"]), int(r["count"])
            if g < 2 or g > 100 or g % 2 or emp < 100: continue
            Cg = hl_correct(g)
            rho_sestak = g * Cg / lnN
            if not (0.05 <= rho_sestak <= 1.10): continue
            row = {"N": N, "g": g, "emp": emp, "log_emp": math.log(emp),
                   "Cg": Cg, "lnN": lnN, "lnlnN": lnlnN, "li2N": li2N, "pi_N": pi_N,
                   "sqrt_omega_g": math.sqrt(omega(g)),
                   "weight": min(1.0, emp / 1000.0)}
            for name, fn in BASELINES.items():
                row[f"logW_{name}"] = fn(g, N, Cg, lnN, li2N, pi_N)
            rows.append(row)
    return pd.DataFrame(rows)


def fit_models(D: pd.DataFrame, baseline: str) -> dict:
    y = D["log_emp"].values
    logW = D[f"logW_{baseline}"].values
    target = y - logW
    sqw = D["sqrt_omega_g"].values
    lnlnN = D["lnlnN"].values
    w = D["weight"].values
    n = len(D)

    # M1*: target = a*sqrt(omega) + b*lnlnN  (no intercept)
    X = np.column_stack([sqw, lnlnN])
    ws = np.sqrt(w)
    coefs_1s, *_ = np.linalg.lstsq(X * ws[:, None], target * ws, rcond=None)
    resid_1s = target - X @ coefs_1s
    rss_1s = float(np.sum(w * resid_1s**2))
    k_1s = 3
    sigma2 = rss_1s / n
    ll_1s = -0.5 * n * (math.log(2 * math.pi * sigma2) + 1.0)
    aic_1s = 2 * k_1s - 2 * ll_1s

    # M3: yhat = logW (with rho replaced) + a*sqw + b*lnlnN + c, but use Wolf-form:
    # Repurpose: y = (logW_baseline_without_exp) - alpha*rho^beta + a*sqw + b*lnlnN + c
    # We need rho per baseline. Use rho_baseline = -(exp_part). Extract:
    # logW = log_pre - rho_eff. We'll reconstruct rho_eff from the baseline definition.
    # Simpler: refit with logW already containing rho linearly; but for M3 we generalize
    # by allowing alpha, beta on the rho term. So we need rho separately.
    if baseline == "Sestak":
        rho = D["g"].values * D["Cg"].values / D["lnN"].values
        log_pre = np.log(D["Cg"].values * D["li2N"].values)
    elif baseline == "Wolf2014":
        rho = D["g"].values / D["lnN"].values
        log_pre = np.log(D["Cg"].values) + np.log(D["N"].astype(float).values) - 2 * np.log(D["lnN"].values)
    elif baseline == "Wolf2018":
        rho = D["g"].values * D["pi_N"].values / D["N"].astype(float).values
        log_pre = np.log(D["Cg"].values) + 2 * np.log(D["pi_N"].values) - np.log(D["N"].astype(float).values)
    elif baseline == "Cohen":
        rho = D["g"].values / D["lnN"].values
        log_pre = 2 * np.log(D["pi_N"].values) - np.log(D["N"].astype(float).values)
    else:
        raise ValueError(baseline)

    def neg_rss(theta):
        alpha, beta, a, b, c = theta
        yhat = log_pre - alpha * (rho ** beta) + a * sqw + b * lnlnN + c
        return float(np.sum(w * (y - yhat) ** 2))

    best = None
    for x0 in [[1.0, 1.0, 0.5, -0.1, 0.0],
               [0.7, 1.2, 0.6, -0.2, 0.1],
               [0.5, 1.5, 0.3, -0.15, 0.05]]:
        r = optimize.minimize(neg_rss, x0=x0, method="Nelder-Mead",
                              options={"xatol": 1e-8, "fatol": 1e-10, "maxiter": 30000})
        if best is None or r.fun < best.fun:
            best = r
    alpha3, beta3, a3, b3, c3 = best.x
    rss_3 = float(best.fun)
    k_3 = 6
    sigma2_3 = rss_3 / n
    ll_3 = -0.5 * n * (math.log(2 * math.pi * sigma2_3) + 1.0)
    aic_3 = 2 * k_3 - 2 * ll_3

    return {
        "n": n,
        "M1_star": {"a": float(coefs_1s[0]), "b": float(coefs_1s[1]),
                    "rss_w": rss_1s, "loglik": ll_1s, "aic": aic_1s, "k": k_1s},
        "M3": {"alpha": float(alpha3), "beta": float(beta3),
               "a": float(a3), "b": float(b3), "c": float(c3),
               "rss_w": rss_3, "loglik": ll_3, "aic": aic_3, "k": k_3},
        "delta_aic_M3_vs_M1": aic_3 - aic_1s,
    }


def main():
    print("Building dataset...")
    D = build_dataset()
    print(f"n = {len(D)}")

    results = {"n": len(D)}
    print(f"\n{'baseline':<10} {'M1* a':>8} {'M1* b':>8} {'M1* RSS':>9} {'M1* AIC':>9} | "
          f"{'M3 α':>7} {'M3 β':>7} {'M3 a':>7} {'M3 b':>8} {'M3 c':>7} {'M3 RSS':>8} {'M3 AIC':>9}")
    print("-" * 130)
    for name in BASELINES:
        r = fit_models(D, name)
        results[name] = r
        m1, m3 = r["M1_star"], r["M3"]
        print(f"{name:<10} {m1['a']:+8.4f} {m1['b']:+8.4f} {m1['rss_w']:9.3f} {m1['aic']:+9.2f} | "
              f"{m3['alpha']:+7.3f} {m3['beta']:+7.3f} {m3['a']:+7.3f} {m3['b']:+8.4f} {m3['c']:+7.3f} "
              f"{m3['rss_w']:8.3f} {m3['aic']:+9.2f}")

    out = OUT_DIR / "recompute_refit_4baselines.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"\n→ {out}")


if __name__ == "__main__":
    main()
