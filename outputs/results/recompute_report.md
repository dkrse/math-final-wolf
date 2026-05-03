# Recompute report — Sestakov výsledok voči Wolf 2014 PRE eq. (7)

**Dátum**: 2026-05-03
**Verdikt**: **Scenár C — výsledok je z veľkej časti artefakt zlej baseline.**

---

## Zhrnutie

Sestakov paper (v3) hlási dva nálezy nad Wolfovou formulou:
1. $\sqrt{\omega(g)}$ člen s amplitúdou $a = 0.855$ (M1*) — domnelý nový g-rozlíšený nález.
2. $b \log\log N$ člen s $b = -0.202$ — domnelý finite-size člen.

Sestak fituje voči formule $W_{\rm Sestak} = C_g \cdot \mathrm{Li}_2(N) \cdot \exp(-g\,C_g/\ln N)$,
ktorá sa **líši** od peer-reviewed Wolf 2014 (PRE 89:022922) eq. (7):
$W_{\rm Wolf} = C_g \cdot N/\ln^2 N \cdot \exp(-g/\ln N)$ — bez $C_g$ v exponente.

Tento recompute testoval každý nález na rovnakom dataset $n=169$ s 4 alternatívnymi baselinami.

---

## 1. Verifikácia sieve voči Cohen 2024 Tab. 1 — PASS

| t | $n$ emp. | $n$ Cohen | $k_1$ emp. | $k_1$ Cohen | $G_n$ | rel. err. |
|---|---|---|---|---|---|---|
| 30 | 54 400 026 | 54 400 026 | 19.7379 | 19.7379 | 282 | $4.5\cdot 10^{-7}$ |
| 36 | 2.874 · 10⁹ | 2.874 · 10⁹ | 23.9074 | 23.9074 | 464 | $4.0\cdot 10^{-5}$ |

Sieve je správny, konvencia (vylučuje $d_1=1$) sedí s Cohenovou.

## 2. Reprodukcia Wolf 2014 Fig. 6 driftu — PASS

| $N$ | $a(N)$ emp. | $s(N)$ emp. |
|---|---|---|
| $1.7 \cdot 10^8$ | 1.269 | 1.072 |
| $1 \cdot 10^{10}$ | 1.222 | 1.061 |
| $1 \cdot 10^{12}$ | 1.192 | 1.060 |
| $3 \cdot 10^{14}$ | 1.156 | 1.046 |

Wolf Fig. 6: $a$ klesá z ~1.51 (1e8) na ~1.27 (1e14), $s$ z ~1.19 na ~1.14.
Tvar (monotónne klesá) reprodukovaný; absolútny offset −0.15 je pravd. dôsledok rozdielu v `u_max` filtri.

## 3. Wolfov drift vysvetľuje Sestakov $b \log\log N$ člen — PASS

```
log a(N) = +0.716 − 0.163 · log log N
log s(N) = +0.191 − 0.041 · log log N
```

| | slope vs log log N | / Sestak $b = -0.202$ |
|---|---|---|
| `a(N)` | −0.163 | 0.808 |
| `s(N)` | −0.041 | 0.202 |
| spolu | −0.204 | **1.01** |

**Sestakov $\log\log N$ člen je v rámci šumu identický s už publikovaným Wolf finite-size driftom.** Nie je novým nálezom.

## 4. $\sqrt{\omega(g)}$ člen kolapsuje voči Wolf2014 baseline

### M1* (2 parametre: a, b)

| Baseline | $a$ | $b$ | RSS_w | AIC |
|---|---|---|---|---|
| Sestak (originál v3) | **+0.836** | −0.195 | 1.447 | −318.9 |
| **Wolf2014** | **+0.184** | +0.012 | 1.430 | −320.9 |
| Wolf2018 eq.26 | +0.159 | −0.004 | 0.702 | −441.2 |
| Cohen (bez $C_g$) | +1.091 | −0.215 | 3.525 | −168.4 |

### M3 (5 parametrov: α, β, a, b, c — Wolf-form + lineárny reziduál)

| Baseline | α | β | $a$ | $b$ | $c$ | RSS_w | AIC |
|---|---|---|---|---|---|---|---|
| Sestak | 0.691 | 1.092 | **+0.512** | −0.170 | +0.112 | 0.657 | −446.3 |
| **Wolf2014** | 0.987 | 1.334 | **+0.026** | −0.244 | +0.898 | 0.156 | −689.1 |
| Wolf2018 | 0.919 | 1.318 | +0.027 | −0.149 | +0.502 | 0.153 | −692.3 |
| Cohen | 1.398 | 1.512 | +1.123 | −0.208 | −0.088 | 2.824 | −199.9 |

**Voči Wolf2014:**
- M1*: $a$ klesá z 0.836 na **0.184** (−78 %)
- M3: $a$ klesá z 0.512 na **0.026** (−95 %, prakticky nula)

Voči Wolf2018 to isté ($a \approx 0.16$ v M1*, $0.027$ v M3).
Voči Cohen-bare (bez $C_g$) sa $a$ zväčšuje — potvrdzuje, že $C_g$ patrí do baseline.

## 5. OOS R² (hold-out $N > 10^{13}$, frozen koef.) — model zlyháva

| Baseline | trénovaný $a$ | trénovaný $b$ | OOS $R^2_w$ |
|---|---|---|---|
| Sestak | +0.855 | −0.202 | **+0.654** |
| **Wolf2014** | +0.180 | +0.021 | **−18.27** |
| Wolf2018 | +0.159 | +0.001 | −5.73 |
| Cohen | +1.121 | −0.227 | +0.538 |

V3 paper hlási OOS R² = 0.986 voči Sestak. Moja replikácia dáva 0.654 (rozdiel: extended dataset má teraz 3e13, 1e14, 3e14, ktoré v3 nemal).
Voči **Wolf2014** je R² = −18.27 — model úplne nefunguje, predikcia je horšia ako prosté priemerovanie.

---

## Záver: tri otázky z inštrukcií

| | Otázka | Odpoveď |
|---|---|---|
| Q1 | Prežíva $\sqrt{\omega(g)}$ člen voči Wolf2014? | **NIE.** Amplitúda 0.836 → 0.184 (M1*), 0.512 → 0.026 (M3). |
| Q2 | Reprodukuje Sestakov $\log\log N$ člen Wolfov $a(x)$ drift? | **ÁNO.** Slope($a$) + slope($s$) vs log log N = $1.01 \times b_{\rm Sestak}$. |
| Q3 | OOS $R^2$ voči Wolf2014? | **−18.27.** Model zlyháva. |

## Odporúčaná akcia: Scenár C

Pôvodný paper v3 nemá nálezový obsah, ktorý by prežil voči peer-reviewed Wolf 2014 baseline.

**Možnosti:**
1. **Krátka komunikácia** v *Integers* alebo arxiv-only s názvom typu *"Reproduction and verification of Wolf 2014 drift parameters $a(x), s(x)$ on extended dataset to $N = 3 \cdot 10^{14}$, with negative result on putative $\sqrt{\omega(g)}$ correction"*. Negatívny výsledok je tiež výsledok.
2. **Stiahnuť paper z plánovaného submitu** a uvoľniť dataset + recompute kód ako reprodukčný balík.
3. Pred akýmkoľvek ďalším krokom: **nepublikovať** v3 v súčasnej podobe — domnelé nálezy sú artefakty.

## Artefakty

- `outputs/results/recompute_summary.json` — strojovo čitateľný súhrn
- `outputs/results/cohen_verify_t30.json`, `cohen_verify_t36.json`
- `outputs/results/wolf_drift_a_s.json`, `wolf_drift_loglogN.json`
- `outputs/results/recompute_refit_4baselines.json`
- `outputs/results/recompute_oos.json`
- `run_extension/wolf_formulas.py`, `cohen_verify.py`, `refit_baselines.py`, `oos_test.py`
