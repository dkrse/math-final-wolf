# Analysis of gaps between primes

- **Script**: analyze_gaps.py v4.0
- **Generated**: 2026-04-24T11:59:33+00:00
- **gaps.csv hash**: `1baad7c007f4`
- **records.csv hash**: `69686ce162bb`

## Range
- Up to $p \approx$ **99,741,319**
- Total number of gaps: **5,761,453**
- Distinct gap sizes: 96
- Largest gap: 220
- Number of records: 24

## Top 10 most frequent gaps
| g | count | % | 6\|g |
|---|---:|---:|:---:|
| 6 | 768,752 | 13.34 | YES |
| 12 | 538,382 | 9.34 | YES |
| 2 | 440,312 | 7.64 |  |
| 4 | 440,257 | 7.64 |  |
| 10 | 430,016 | 7.46 |  |
| 18 | 384,738 | 6.68 | YES |
| 8 | 334,180 | 5.80 |  |
| 14 | 293,201 | 5.09 |  |
| 24 | 257,548 | 4.47 | YES |
| 30 | 222,847 | 3.87 | YES |

## Jumping champion
- In this range: $g = 6$ with 768,752 occurrences.
- Erdos-Straus: for sufficiently large $N$ the JCs are primorials (2, 6, 30, 210, 2310, ...). The $6 \to 30$ transition is expected near $p \sim 10^{35}$.

## Agreement with theory
H-L: $\#\{p \le N: p, p{+}g \text{ prime}\} \sim C_g \int_2^N dt/\ln^2 t$ (all pairs). Wolf (1998) adds the factor $\exp(-g C_g/\ln N)$ for consecutive gaps. For $g \in \{2,4\}$ consecutive = pair (no prime can lie between), so H-L applies directly. For larger $g$, Wolf is reasonable when $\ln N \gg g$, which at $\ln N \approx 18.4$ is not yet fully satisfied.

| g | emp | Wolf | H-L (pair) | emp/Wolf |
|---|---:|---:|---:|---:|
| 2 | 440,312 | 380,676 | 439,361 | 1.1567 |
| 4 | 440,257 | 329,830 | 439,361 | 1.3348 |
| 6 | 768,752 | 371,755 | 878,722 | 2.0679 |
| 8 | 334,180 | 247,604 | 439,361 | 1.3497 |
| 10 | 430,016 | 225,245 | 585,815 | 1.9091 |
| 12 | 538,382 | 157,276 | 878,722 | 3.4232 |

**Pearson chi-square test** (emp vs Wolf, normalised): chi2 = 413586.29, dof = 5, p = 0.000e+00

## Merit of records
- Linear fit: $M \approx 0.846\ln p -2.695$ (Cramer predicts slope 1.0 asymptotically)
- Cramer-Shanks-Granville $g \sim c(\ln p)^\alpha$: $\alpha \approx 2.429$, $c \approx 0.2075$ (theory: $\alpha = 2$)

## Last 5 records
| g | p_start | merit |
|---:|---:|---:|
| 148 | 2,010,733 | 10.197 |
| 154 | 4,652,353 | 10.031 |
| 180 | 17,051,707 | 10.810 |
| 210 | 20,831,323 | 12.461 |
| 220 | 47,326,693 | 12.449 |

## Quasi-equivalence of g=2 and g=4
- $\#\{g=2\}$ = 440,312 (twin primes)
- $\#\{g=4\}$ = 440,257 (cousin primes)
- Difference: 55 (0.0125%), Poisson $z = 0.06\sigma$
- H-L: $C_2 = C_4 = 2 C_2^{\mathrm{twin}}$, hence $\pi_2(N) \sim \pi_4(N)$.
