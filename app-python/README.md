# Prime Gap Analysis (Python)

Post-processing scripts for the CSV outputs produced by the C programs in
`../app-c/`. They generate figures and a markdown summary describing the
statistical structure of the prime gaps.

## Scripts

- **`analyze_gaps.py`** histogram-based analysis. Consumes `gaps.csv` and
  `records.csv`. Produces `fig1_histogram.png`, `fig2_merit.png`,
  `fig3_ratios.png`, `fig4_champions.png` and `summary.md`.
- **`analyze_sequence.py`** sequential analysis. Consumes the ordered gap
  stream `gap_stream.csv`. Produces `fig5_champions.png`, `fig6_gpy.png`,
  `fig7_autocorr.png` and appends its results to `summary.md`.

## Requirements

Python 3.10+ and the packages listed in `requirements.txt`:

```
numpy >= 1.24
pandas >= 2.0
matplotlib >= 3.7
scipy >= 1.11
```

Install with:

```sh
pip install -r requirements.txt
```

## Typical workflow

1. Build the C binaries (`make` in `../app-c/`).
2. Produce CSV inputs, e.g.:
   ```sh
   ../app-c/build/main-csv 1e10 1000
   ```
3. Run the histogram analysis:
   ```sh
   python3 analyze_gaps.py --gaps gaps.csv --records records.csv --out .
   ```
4. (Optional) Run the sequential analysis on the gap stream:
   ```sh
   python3 analyze_sequence.py --stream gap_stream.csv --out .
   ```

## What is computed

- **Histogram + top-20** most frequent gaps, with highlighting of multiples
  of 6 (residue bias).
- **Merit of record gaps** vs Cramer's model `M = ln p` and the Cramer-
  Granville band `[ln p, 2 ln p]`, with a linear fit and a
  Cramer-Shanks-Granville power-law fit `g ~ c (ln p)^alpha`.
- **Hardy-Littlewood / Wolf prediction** for consecutive gaps
  `g in {2, 4, 6, ...}` with Pearson chi-square test against Wolf's model.
- **Jumping-champion transitions** along a logarithmic grid of upper
  bounds (running histogram).
- **Goldston-Pintz-Yildirim context**: running minimum of `g_n / ln p_n`.
- **Gap autocorrelation** at lags 1..`max_lag`, compared against shuffled
  surrogate data as the independence null.

## Author

krse

## Credits

Input data is produced with the **primesieve** library by **Kim Walisch**.

- Project: https://github.com/kimwalisch/primesieve
- Author: https://github.com/kimwalisch
