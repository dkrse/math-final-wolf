"""OOS hold-out test: trénuj M1* na N <= 1e13, predikuj N > 1e13, weighted R^2.
Pre každý zo 4 baselinov."""
from __future__ import annotations
import math, json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from refit_baselines import build_dataset
from wolf_formulas import BASELINES

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "outputs" / "results"


def fit_predict_oos(D, baseline, N_split=1e13):
    train = D[D["N"] <= N_split].reset_index(drop=True)
    test = D[D["N"] > N_split].reset_index(drop=True)
    sqw_tr = train["sqrt_omega_g"].values
    lnlnN_tr = train["lnlnN"].values
    w_tr = train["weight"].values
    target_tr = train["log_emp"].values - train[f"logW_{baseline}"].values
    X_tr = np.column_stack([sqw_tr, lnlnN_tr])
    ws = np.sqrt(w_tr)
    coefs, *_ = np.linalg.lstsq(X_tr * ws[:, None], target_tr * ws, rcond=None)
    a, b = coefs
    # predict on test
    target_te = test["log_emp"].values - test[f"logW_{baseline}"].values
    pred = a * test["sqrt_omega_g"].values + b * test["lnlnN"].values
    w_te = test["weight"].values
    # weighted R^2: 1 - sum(w*(t-p)^2) / sum(w*(t-mean_w)^2)
    mean_t = float(np.sum(w_te * target_te) / np.sum(w_te))
    ss_res = float(np.sum(w_te * (target_te - pred) ** 2))
    ss_tot = float(np.sum(w_te * (target_te - mean_t) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {"a": float(a), "b": float(b),
            "n_train": len(train), "n_test": len(test),
            "ss_res": ss_res, "ss_tot": ss_tot, "R2_w": r2}


def main():
    D = build_dataset()
    print(f"n total = {len(D)};  N_split = 1e13")
    out = {"n_total": len(D), "N_split": 1e13}
    print(f"\n{'baseline':<10} {'a':>8} {'b':>8} {'n_tr':>5} {'n_te':>5} {'R²_w':>8}")
    print("-" * 60)
    for name in BASELINES:
        r = fit_predict_oos(D, name)
        out[name] = r
        print(f"{name:<10} {r['a']:+8.4f} {r['b']:+8.4f} {r['n_train']:5d} {r['n_test']:5d} {r['R2_w']:+8.4f}")

    p = OUT_DIR / "recompute_oos.json"
    p.write_text(json.dumps(out, indent=2))
    print(f"\n→ {p}")


if __name__ == "__main__":
    main()
