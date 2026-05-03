"""
d1_loo_cv.py — leave-one-out cross-validation for the rho(1) = a + b/ln N fit.

For each of the 5 N: fit on the remaining 4, predict the 5th. Reports:
  - in-sample (a, b) on 4
  - prediction for the held-out N
  - true value
  - relative error

Robustness check for the paper-worthy finding (b = -0.652).
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

WORK = Path(__file__).resolve().parent / "autocorr"


def main() -> None:
    files = sorted(WORK.glob("autocorr_N1e*.json"))
    data = []
    for f in files:
        d = json.loads(f.read_text())
        data.append({"N": d["N"], "lnN": np.log(d["N"]), "rho1": d["rho"][1]})
    n = len(data)
    print(f"Number of N values: {n}")

    # Full fit
    lnN_all = np.array([d["lnN"] for d in data])
    rho_all = np.array([d["rho1"] for d in data])
    A = np.column_stack([np.ones(n), 1.0 / lnN_all])
    full_coef, *_ = np.linalg.lstsq(A, rho_all, rcond=None)
    a_full, b_full = full_coef
    print(f"\nFull fit (n={n}):")
    print(f"  a = {a_full:+.6f},  b = {b_full:+.6f}")
    print(f"  RSS = {float(np.sum((rho_all - A @ full_coef)**2)):.3e}")

    print(f"\n{'held-out N':>12}  {'a (4)':>10}  {'b (4)':>10}  "
          f"{'pred rho(1)':>11}  {'true rho(1)':>11}  {'rel.err':>8}")
    abs_errs = []
    rel_errs = []
    bs = []
    for i in range(n):
        train = [d for j, d in enumerate(data) if j != i]
        test = data[i]
        lnN_tr = np.array([d["lnN"] for d in train])
        rho_tr = np.array([d["rho1"] for d in train])
        A_tr = np.column_stack([np.ones(len(train)), 1.0 / lnN_tr])
        coef, *_ = np.linalg.lstsq(A_tr, rho_tr, rcond=None)
        a, b = coef
        pred = a + b / test["lnN"]
        rel = abs(pred - test["rho1"]) / abs(test["rho1"])
        abs_errs.append(abs(pred - test["rho1"]))
        rel_errs.append(rel)
        bs.append(b)
        print(f"  {test['N']:>10.0e}  {a:>+10.5f}  {b:>+10.5f}  "
              f"{pred:>+11.5f}  {test['rho1']:>+11.5f}  {rel * 100:>7.3f}%")

    print()
    print(f"LOO summary:")
    print(f"  b across 5 LOO fits: min = {min(bs):+.5f}, max = {max(bs):+.5f}")
    print(f"  b spread (max-min): {max(bs) - min(bs):.5f}")
    print(f"  mean abs error: {np.mean(abs_errs):.5f}")
    print(f"  max abs error:  {max(abs_errs):.5f}")
    print(f"  mean rel error: {np.mean(rel_errs) * 100:.2f}%")
    print(f"  max rel error:  {max(rel_errs) * 100:.2f}%")

    # Pure scaling fit (no intercept), for comparison
    print()
    print("=" * 70)
    print("Comparison: pure scaling rho(1) = c/ln N (no intercept)")
    print("=" * 70)
    A_scale = (1.0 / lnN_all).reshape(-1, 1)
    c_full, *_ = np.linalg.lstsq(A_scale, rho_all, rcond=None)
    c_scaled = float(c_full[0])
    rss_scaled = float(np.sum((rho_all - c_scaled / lnN_all) ** 2))
    print(f"  c = {c_scaled:+.5f}  (full fit, RSS = {rss_scaled:.3e})")
    print()
    print(f"{'held-out N':>12}  {'c (4)':>10}  {'pred':>11}  {'true':>11}  "
          f"{'rel.err':>8}")
    cs_loo = []
    rels_loo = []
    for i in range(n):
        train = [d for j, d in enumerate(data) if j != i]
        test = data[i]
        lnN_tr = np.array([d["lnN"] for d in train])
        rho_tr = np.array([d["rho1"] for d in train])
        A_tr = (1.0 / lnN_tr).reshape(-1, 1)
        coef, *_ = np.linalg.lstsq(A_tr, rho_tr, rcond=None)
        c = float(coef[0])
        pred = c / test["lnN"]
        rel = abs(pred - test["rho1"]) / abs(test["rho1"])
        cs_loo.append(c)
        rels_loo.append(rel)
        print(f"  {test['N']:>10.0e}  {c:>+10.5f}  "
              f"{pred:>+11.5f}  {test['rho1']:>+11.5f}  {rel * 100:>7.3f}%")
    print(f"\n  c spread across LOO: {max(cs_loo) - min(cs_loo):.5f}")
    print(f"  mean rel error: {np.mean(rels_loo) * 100:.2f}%")


if __name__ == "__main__":
    main()
