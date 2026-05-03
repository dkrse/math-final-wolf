# baseline_n140 — pre-extension snapshot

Snapshot `outputs/results/rev01_*.json` pred spustením vetvy B (extension
do *N* = 3·10¹⁴). Slúži na čistý before/after diff.

## Generovanie

```bash
# 30. apríl 2026, na work-pc
source .venv/bin/activate
jupyter nbconvert --to notebook --execute --inplace 09_rev01_alt_forms.ipynb
jupyter nbconvert --to notebook --execute --inplace 10_rev01_robustness.ipynb
jupyter nbconvert --to notebook --execute --inplace 11_rev01_m1_vs_m3.ipynb
cp outputs/results/rev01_*.json outputs/results/baseline_n140/
```

## Reprodukovateľnosť — overené

```
diff _paper_v1/rev01_m1_vs_m3.json     baseline_n140/rev01_m1_vs_m3.json   → bit-identical
diff _paper_v1/rev01_results.json      baseline_n140/rev01_results.json    → bit-identical
diff _paper_v1/rev01_robustness.json   baseline_n140/rev01_robustness.json → bit-identical
```

Pipeline je 100 % reprodukovateľný cez stroje (paper bol napočítaný na
`/opt/apps/jupyter/work/`, baseline na `work-pc`).

## Kľúčové čísla

| | hodnota | paper §3.5 |
|---|---|---|
| dataset_size *n* | 140 | 140 |
| N values | 25 | 25 |
| filter | ρ ∈ [0,05; 1,10], g ∈ [2,100], N_g ≥ 100 | rovnaké |
| **M₁\*** *a* (√ω) | +0,8552 | +0,855 |
| **M₁\*** *b* (log log N) | −0,2017 | −0,202 |
| **M₁\*** AIC | −273,74 | −275,74 (paper) — 2-AIC offset |
| **M₃** α | +0,6889 | +0,689 |
| **M₃** β | +1,1674 | +1,167 |
| **M₃** AIC | −384,52 | −386,52 (paper) |
| **ΔAIC(M₃ − M₁\*)** | **−110,78** | **−110,8** |

(2-AIC-unit konštantný offset proti paperu pre absolútne AIC hodnoty
je pravdepodobne rozdiel v normalizácii log-likelihood. Relatívne ΔAIC
sú zhodné na 2 desatinné miesta — to je čo sa používa v paperi.)

## Po B-runu (ako porovnať)

Po `post_launch.sh` budú v `outputs/results/rev01_*.json` nové čísla na
*n* ≈ 175 (29 N hodnôt). Diff:

```bash
diff -q outputs/results/baseline_n140/ outputs/results/
# alebo per file:
python3 -c "
import json
b = json.loads(open('outputs/results/baseline_n140/rev01_m1_vs_m3.json').read())
n = json.loads(open('outputs/results/rev01_m1_vs_m3.json').read())
print(f'n: {b[\"n\"]} → {n[\"n\"]}')
print(f'M1* a: {b[\"M1_star\"][\"coefs\"][0]:.4f} → {n[\"M1_star\"][\"coefs\"][0]:.4f}')
print(f'M1* b: {b[\"M1_star\"][\"coefs\"][1]:.4f} → {n[\"M1_star\"][\"coefs\"][1]:.4f}')
print(f'M3 β:  {b[\"M3\"][\"coefs\"][1]:.4f} → {n[\"M3\"][\"coefs\"][1]:.4f}')
print(f'ΔAIC:  {b[\"M3\"][\"aic\"]-b[\"M1_star\"][\"aic\"]:.2f} → {n[\"M3\"][\"aic\"]-n[\"M1_star\"][\"aic\"]:.2f}')
"
```

Co sledovať:
- **(a, b) drift** — paper bootstrap CI: a ∈ [0,791; 0,933], b ∈ [−0,230; −0,179].
  Po B by nové fittované hodnoty mali ostať v tom intervale.
- **M₃ β** — pri 25 N je β = 1,167. Predikcia: pri 28 N by malo byť bližšie
  k 1 ak je β pre-asymptotický artefakt; alebo stabilne ~1,2 ak je to
  reálna štruktúra.
- **n** — primary filter ide z 140 na ~175 (predikcia z `filter_prediction.py`).
- **ΔAIC(M₃ − M₁\*)** — bude rásť (M₃ má viac parametrov, profituje z viac dát).
