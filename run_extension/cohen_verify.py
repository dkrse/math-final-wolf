"""Cohen 2024 Tab. 1 verifikácia — nezávislý sieve cez primesieve.

Vypočíta {n, k1, k2, G_n} pre x=2^t a porovná s Cohen referenciou.
Vylučuje d_1=1 (gap medzi 2 a 3) podľa Cohenovej konvencie.

Spustenie:
    python run_extension/cohen_verify.py 36
"""
from __future__ import annotations
import sys, time, json
from pathlib import Path
import primesieve

COHEN_REF = {
    15: {"n": 3510,        "k1": 9.3293,  "k2": 136.2017,    "G_n": 72},
    18: {"n": 22998,       "k1": 11.3982, "k2": 210.7095,    "G_n": 86},
    21: {"n": 155609,      "k1": 13.4770, "k2": 304.1124,    "G_n": 148},
    24: {"n": 1077869,     "k1": 15.5652, "k2": 412.7866,    "G_n": 154},
    27: {"n": 7603551,     "k1": 17.6520, "k2": 539.4491,    "G_n": 222},
    30: {"n": 54400026,    "k1": 19.7379, "k2": 683.2373,    "G_n": 282},
    33: {"n": 393615804,   "k1": 21.8231, "k2": 844.1273,    "G_n": 354},
    36: {"n": 2.8744e9,    "k1": 23.9074, "k2": 1.0222e3,    "G_n": 464},
    39: {"n": 2.1152e10,   "k1": 25.9908, "k2": 1.2173e3,    "G_n": 532},
    42: {"n": 1.5666e11,   "k1": 28.0736, "k2": 1.4296e3,    "G_n": 652},
    45: {"n": 1.1667e12,   "k1": 30.1560, "k2": 1.6590e3,    "G_n": 766},
    48: {"n": 8.7312e12,   "k1": 32.2379, "k2": 1.9056e3,    "G_n": 906},
}


def gap_histogram(x: int) -> dict[int, int]:
    it = primesieve.Iterator()
    prev = it.next_prime()
    gaps: dict[int, int] = {}
    while True:
        p = it.next_prime()
        if p > x:
            break
        g = p - prev
        gaps[g] = gaps.get(g, 0) + 1
        prev = p
    return gaps


def stats_excl_d1(gaps: dict[int, int]) -> dict:
    items = [(g, c) for g, c in gaps.items() if g != 1]
    n = sum(c for _, c in items)
    k1 = sum(g * c for g, c in items) / n
    k2 = sum(g * g * c for g, c in items) / n
    G_n = max(g for g, _ in items)
    return {"n": n, "k1": k1, "k2": k2, "G_n": G_n}


def verify(t: int) -> dict:
    if t not in COHEN_REF:
        raise ValueError(f"t={t} not in Cohen Tab. 1")
    x = 2 ** t
    t0 = time.time()
    gaps = gap_histogram(x)
    elapsed = time.time() - t0
    emp = stats_excl_d1(gaps)
    ref = COHEN_REF[t]
    rel = {
        "n": (emp["n"] - ref["n"]) / ref["n"],
        "k1": (emp["k1"] - ref["k1"]) / ref["k1"],
        "k2": (emp["k2"] - ref["k2"]) / ref["k2"],
    }
    return {"t": t, "x": x, "elapsed_s": elapsed,
            "empirical": emp, "cohen_ref": ref, "rel_err": rel}


if __name__ == "__main__":
    t = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    res = verify(t)
    out_dir = Path(__file__).resolve().parent.parent / "outputs" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"cohen_verify_t{t}.json"
    out_path.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    print(f"\n→ {out_path}")
