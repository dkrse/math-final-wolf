# Prime Gap Analysis (C)

Tools for analysing gaps between consecutive primes using the
**primesieve** library by **Kim Walisch**.

- Project: https://github.com/kimwalisch/primesieve
- Author: https://github.com/kimwalisch

## Programs

- **`main.c`** minimal iterator that prints every new record gap up to 10^12.
- **`main-csv.c`** full analysis: histogram, records and optional sampled
  stream of gaps. Writes `gaps.csv`, `records.csv` and (optionally)
  `gap_stream.csv`.
- **`main-csv-static.c`** identical to `main-csv.c`, but linked statically
  against `libprimesieve.a` so the binary runs without the shared library.

## Requirements

- `gcc`
- `primesieve` installed (shared build provides `libprimesieve.so`, static
  build provides `libprimesieve.a`, typically under `/usr/local/lib/`)
- `libm` (linked with `-lm`)

## Compilation

Dynamic linking (shared library):

```sh
gcc -O3 main.c     -o main     -lprimesieve -lm
gcc -O3 main-csv.c -o main-csv -lprimesieve -lm
```

Static linking (bundles `libprimesieve.a`; `-lstdc++` is required because
primesieve is C++ internally):

```sh
gcc -O3 main-csv-static.c -o main-csv-static /usr/local/lib/libprimesieve.a -lm -lstdc++
```

### Using the Makefile

A `Makefile` is provided that builds all three binaries into the `build/`
directory:

```sh
make          # builds build/main, build/main-csv, build/main-csv-static
make clean    # removes the build/ directory
```

## Usage

```sh
./main-csv <N> [stride]
```

- `N` upper bound (e.g. `1e10` or `10000000000`).
- `stride` optional sampling step for `gap_stream.csv`:
  - `0` (default) stream disabled
  - `1` every gap
  - `1000` every 1000th gap

### Examples

```sh
./main-csv 1e10           # histogram + records only
./main-csv 1e10 1000      # + stream of every 1000th gap
./main-csv 1e9 1          # + stream of all gaps
```

## Output files

- **`gaps.csv`** histogram `gap,count` of all prime gaps in `[2, N]`.
- **`records.csv`** record gaps: `gap,p_start,ln_p,merit`
  (merit = `gap / ln(p_start)`).
- **`gap_stream.csv`** sampled `(p_start, gap)` pairs (only if `stride > 0`).

## Author

krse
