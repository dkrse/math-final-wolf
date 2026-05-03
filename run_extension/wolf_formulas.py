"""Wolf / Sestak / Cohen baseline formuly pre recompute analýzu.

Wolf 2014 PRE 89:022922 eq. (7) je peer-reviewed referencia.
Sestakov variant má extra C_g v exponente — to je nález inštrukcií.
Cohen bare nemá C_g vôbec.

Všetky funkcie vracajú log W (lebo dáta sú v log priestore).
"""
from __future__ import annotations
import math
import numpy as np
from scipy import integrate

C2_TWIN = 0.6601618158468695739278121100145557784326233602847334133194484233354


def hl_correct(g: int) -> float:
    """Hardy-Littlewood C_g = 2 C_2 * prod_{p|g, p>2} (p-1)/(p-2). Pre nepárne g 0."""
    if g <= 0 or g % 2:
        return 0.0
    n = g
    while n % 2 == 0:
        n //= 2
    corr, p = 1.0, 3
    while p * p <= n:
        if n % p == 0:
            corr *= (p - 1) / (p - 2)
            while n % p == 0:
                n //= p
        p += 2
    if n > 1:
        corr *= (n - 1) / (n - 2)
    return 2 * C2_TWIN * corr


def li2(N: float) -> float:
    v, _ = integrate.quad(lambda t: 1.0 / np.log(t) ** 2, 2.0, N, limit=200)
    return float(v)


def log_W_Sestak(g: int, N: float, Cg: float, lnN: float, li2N: float, pi_N: float) -> float:
    """Sestakov variant: log[C_g * Li_2(N) * exp(-g*C_g/ln N)]."""
    return math.log(Cg * li2N) - g * Cg / lnN


def log_W_Wolf2014(g: int, N: float, Cg: float, lnN: float, li2N: float, pi_N: float) -> float:
    """Wolf 2014 PRE eq. (7): log[C_g * (N/ln^2 N) * exp(-g/ln N)]."""
    return math.log(Cg) + math.log(N) - 2 * math.log(lnN) - g / lnN


def log_W_Wolf2018(g: int, N: float, Cg: float, lnN: float, li2N: float, pi_N: float) -> float:
    """Wolf 2018 review eq. (26): log[C_g * pi^2(N)/N * exp(-g*pi(N)/N)]."""
    return math.log(Cg) + 2 * math.log(pi_N) - math.log(N) - g * pi_N / N


def log_W_Cohen_bare(g: int, N: float, Cg: float, lnN: float, li2N: float, pi_N: float) -> float:
    """Cohen-implicit: log[pi^2(N)/N * exp(-g/ln N)]. ŽIADNE C_g."""
    return 2 * math.log(pi_N) - math.log(N) - g / lnN


BASELINES = {
    "Sestak":   log_W_Sestak,
    "Wolf2014": log_W_Wolf2014,
    "Wolf2018": log_W_Wolf2018,
    "Cohen":    log_W_Cohen_bare,
}


# --- self-validation ---
if __name__ == "__main__":
    N = 1e8
    pi_N = 5761455
    Cg = hl_correct(2)
    lnN = math.log(N)
    li2N = li2(N)
    print(f"N={N:.0e}  pi(N)={pi_N}  C_2={Cg:.6f}  ln N={lnN:.4f}  Li_2(N)={li2N:.4e}")
    for name, fn in BASELINES.items():
        lW = fn(2, N, Cg, lnN, li2N, pi_N)
        W = math.exp(lW)
        print(f"  {name:9s}: W_2(1e8) = {W:.4e}   ratio to empir(440312) = {W/440312:.4f}")
