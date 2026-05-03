# math-final-wolf

Final and superseding repository for the empirical study of consecutive
prime-gap distribution against Wolf's heuristic, by Kristián Sesták.

> ⚠️ **This repository supersedes** three earlier preprints
> ([v1](https://doi.org/10.5281/zenodo.19796305),
> [v2](https://doi.org/10.5281/zenodo.19958063),
> [v3](https://doi.org/10.5281/zenodo.19975065))
> in which a $\sqrt{\omega(g)}$ correction to Wolf's formula was claimed.
> The claim was an artifact of a mis-specified baseline. See the
> [final note](paper/paper.pdf) for the negative result and a reproduction
> of Wolf's $a(x), s(x)$ drift on the extended range $N \le 3 \cdot 10^{14}$.

---

## What this repository contains

| Path | Content |
|---|---|
| `paper/` | Final note (LaTeX source + PDF). Negative result + drift reproduction. |
| `app-c/` | C generator for consecutive-prime-gap histograms (built on `libprimesieve`). |
| `ml_data/` | 28 sieve histograms covering $N \in [10^5, 3 \cdot 10^{14}]$, plus SHA-256 manifests. |
| `notebooks/` | Jupyter notebooks (`01`–`12`) reproducing every figure and table in the final note. |
| `run_extension/` | Pipeline scripts: `wolf_formulas.py`, `cohen_verify.py`, `refit_baselines.py`, `oos_test.py`, `post_launch.sh`. |
| `outputs/results/` | Frozen JSON outputs of the main computations (`recompute_summary.json`, `recompute_refit_4baselines.json`, `recompute_oos.json`, `wolf_drift_a_s.json`, `cohen_verify_t30.json`, `cohen_verify_t36.json`). |
| `archive/v1_v3/` | Read-only archive of the superseded preprints, kept for historical reference. |

## Headline results

1. **Sieve verification (PASS).** Histograms exact-matched against
   Cohen 2024 [Tab. 1] for $t \in \{30, 36\}$ on $\mu'_{1, n}, \mu'_{2, n}, G_n$
   (relative error $< 5 \cdot 10^{-5}$).
2. **Wolf 2014 drift reproduced** to $N = 3 \cdot 10^{14}$
   (Wolf 2014 Fig. 6 was published only to $\sim 10^{14}$).
   Parameters $a(x): 1.27 \to 1.16$ and $s(x): 1.07 \to 1.05$ continue
   to drift monotonically; a $\log\log N$ regression of $\log a(N) + \log s(N)$
   has slope $-0.204$.
3. **Negative result.** A $\sqrt{\omega(g)}$ correction term, reported
   in the superseded versions, collapses by 78–95 % under refit against
   the correct Wolf 2014 baseline. Out-of-sample $R^2$ on hold-out
   $N > 10^{13}$ is $-18.3$. The earlier finding was an artifact of using
   $\widehat W_S(g, N) = C_g \cdot \mathrm{Li}_2(N) \cdot \exp(-g\,C_g/\ln N)$
   in place of Wolf 2014 Eq. (7) (no $C_g$ in the exponent).

## Reproducing the results

### Environment

```bash
git clone https://github.com/dkrse/math-final-wolf.git
cd math-final-wolf
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Dependencies are pinned. `libprimesieve` headers must be installed at
the system level (e.g. `apt install libprimesieve-dev`).

### Sieve

The C generator reproduces the 28 histograms bit-for-bit:

```bash
cd app-c && cmake -B build && cmake --build build
./build/main-csv-static  # writes ml_data/gaps_N{N}.csv
```

Wall-clock cost on a single modern core: $\sim 25$ h for the full grid,
dominated by the $N = 3 \cdot 10^{14}$ run ($\sim 13$ min on its own).

### Pipeline

```bash
# 1. cross-check sieve against Cohen 2024 Tab. 1
python run_extension/cohen_verify.py 30
python run_extension/cohen_verify.py 36

# 2. fit Wolf's a(x), s(x) drift; check log-log-N slope
jupyter nbconvert --to notebook --execute notebooks/13_wolf_drift.ipynb

# 3. refit M1*, M3 against four baselines on n=169
python run_extension/refit_baselines.py

# 4. out-of-sample test (train N <= 1e13, test N > 1e13)
python run_extension/oos_test.py

# 5. summary
python run_extension/summarise.py  # writes outputs/results/recompute_summary.json
```

All five commands together take $\sim 5$ minutes; the costly part is the
sieve, which is pre-computed in `ml_data/`.

### Compiling the paper

```bash
cd paper
pdflatex paper.tex && pdflatex paper.tex
```

## Data

Sieve histograms live in `ml_data/gaps_N{N}.csv`:

```
gap,count
1,1
2,224376048
4,224373160
6,...
```

The first column is the gap size $g$; the second is the count
$\tau_g(N)$ of consecutive prime pairs $(p_n, p_{n+1})$ with
$p_{n+1} \le N$ and $p_{n+1} - p_n = g$.
SHA-256 sums in `ml_data/SHA256SUMS` confirm bit-identity across rebuilds.

The convention here matches Cohen 2024: the gap $d_1 = p_2 - p_1 = 1$
between $2$ and $3$ is recorded but excluded from moment calculations.

## Citation

Please cite the final note:

```bibtex
@misc{sestak2026wolfnegative,
  author = {Sestak, Kristian},
  title  = {A negative result on a putative $\sqrt{\omega(g)}$ correction
            to Wolf's consecutive-prime-gap formula, with a reproduction
            of finite-size drift to $3\cdot 10^{14}$},
  year   = {2026},
  doi    = {10.5281/zenodo.20010072},
  url    = {https://github.com/dkrse/math-final-wolf}
}
```

The superseded earlier records (v1–v3) are listed separately on Zenodo.
Each carries an editorial supersession note pointing to this record.
They should not be cited as primary results.

## License

- Code: [MIT](LICENSE-CODE)
- Data: [CC-BY-4.0](LICENSE-DATA)
- Paper: [CC-BY-4.0](LICENSE-PAPER)

## Acknowledgements

The author thanks Prof. Christian Elsholtz, whose critical reading of
the v1 manuscript drew attention to Wolf's review article
[arXiv:1102.0481] and, indirectly, to the baseline mis-specification
that this final note documents.

The work uses Kim Walisch's [`primesieve`](https://github.com/kimwalisch/primesieve).
The cross-check against Cohen 2024 Tab. 1 was made possible by Marek Wolf's
publicly archived $\tau_d$ data
([pracownicy.uksw.edu.pl/mwolf/gaps.zip](http://pracownicy.uksw.edu.pl/mwolf/gaps.zip)),
which Joel E. Cohen analysed independently and reported in
*Experimental Mathematics* 34 (2024), no. 2.

## Contact

[kristian.sestak@gmail.com](mailto:kristian.sestak@gmail.com)
