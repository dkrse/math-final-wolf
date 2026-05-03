/*
 * main-autocorr.c
 *
 * Streaming computation of lag-k autocorrelation ρ(k) of consecutive prime
 * gap sequence on [2, N], using primesieve_iterator. O(K) memory total
 * where K = MAX_LAG, single sieve pass.
 *
 * Output: JSON to stdout (or to file if -o SUFFIX given):
 *   {
 *     "N": ..., "n_primes": ..., "n_gaps": ...,
 *     "mean_g": ..., "var_g": ...,
 *     "rho": [1.0, ρ(1), ρ(2), ..., ρ(MAX_LAG)],
 *     "wall_seconds": ...
 *   }
 *
 * Math (biased estimator, equivalent to numpy default at large N):
 *   ρ(k) = (E[g_i * g_{i+k}] - E[g]^2) / (E[g^2] - E[g]^2)
 *        = (S_{xk} / n_k - μ²) / (S_xx / n - μ²),  μ = S_x / n
 * where S_x = Σ g_i, S_xx = Σ g_i², S_{xk} = Σ_{i ≤ n-k} g_i g_{i+k},
 * n = total #gaps, n_k = n - k.
 *
 * Compile:  see Makefile target build/main-autocorr
 * Use:      ./main-autocorr [-o SUFFIX] <N>
 */

#include <primesieve.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

#define MAX_LAG 10

static int build_path(char *buf, size_t buflen, const char *base,
                      const char *suffix) {
    if (suffix && suffix[0] != '\0') {
        return snprintf(buf, buflen, "%s_%s.json", base, suffix);
    }
    return snprintf(buf, buflen, "%s.json", base);
}

int main(int argc, char *argv[]) {
    const char *suffix = "";
    const char *positional = NULL;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-o") == 0) {
            if (i + 1 >= argc) {
                fprintf(stderr, "Error: -o requires an argument\n");
                return 1;
            }
            suffix = argv[++i];
        } else if (positional == NULL) {
            positional = argv[i];
        } else {
            fprintf(stderr, "Error: unexpected argument '%s'\n", argv[i]);
            return 1;
        }
    }
    if (!positional) {
        fprintf(stderr, "Usage: %s [-o SUFFIX] <N>\n", argv[0]);
        return 1;
    }

    uint64_t N = (uint64_t) strtod(positional, NULL);
    if (N < 3) { fprintf(stderr, "N must be at least 3\n"); return 1; }

    /* Running sums (long double for numerical stability at large N) */
    long double S_x = 0.0L;       /* Σ g */
    long double S_xx = 0.0L;      /* Σ g² */
    long double S_xk[MAX_LAG + 1] = {0.0L};   /* Σ g_i * g_{i+k} for k = 1..MAX_LAG */
    uint64_t n_gaps = 0;

    /* Circular buffer of the last MAX_LAG gaps */
    uint64_t buf[MAX_LAG] = {0};
    int buf_cnt = 0;
    int buf_head = 0;       /* next slot to write */

    fprintf(stderr, "Streaming autocorrelation up to N = %lu, MAX_LAG = %d\n",
            (unsigned long) N, MAX_LAG);
    fprintf(stderr, "===============================================\n");
    clock_t t_start = clock();

    primesieve_iterator it;
    primesieve_init(&it);

    uint64_t prev = primesieve_next_prime(&it);
    uint64_t total_primes = 1;
    uint64_t curr = primesieve_next_prime(&it);

    while (curr <= N) {
        uint64_t g = curr - prev;
        n_gaps++;
        total_primes++;
        long double gd = (long double) g;
        S_x  += gd;
        S_xx += gd * gd;

        /* For each lag k that has a valid past gap, accumulate cross-product. */
        int avail = buf_cnt < MAX_LAG ? buf_cnt : MAX_LAG;
        for (int k = 1; k <= avail; k++) {
            int idx = buf_head - k;
            if (idx < 0) idx += MAX_LAG;
            S_xk[k] += gd * (long double) buf[idx];
        }

        /* Push current gap to circular buffer for future cross-products. */
        buf[buf_head] = g;
        buf_head = (buf_head + 1) % MAX_LAG;
        if (buf_cnt < MAX_LAG) buf_cnt++;

        prev = curr;
        curr = primesieve_next_prime(&it);
    }

    primesieve_free_iterator(&it);

    double t_elapsed = (double)(clock() - t_start) / CLOCKS_PER_SEC;

    /* Final statistics */
    long double mean_g = S_x / (long double) n_gaps;
    long double E_xx   = S_xx / (long double) n_gaps;
    long double var_g  = E_xx - mean_g * mean_g;

    long double rho[MAX_LAG + 1];
    rho[0] = 1.0L;
    for (int k = 1; k <= MAX_LAG; k++) {
        if (n_gaps <= (uint64_t) k) { rho[k] = 0.0L; continue; }
        long double E_xk = S_xk[k] / (long double) (n_gaps - k);
        rho[k] = (E_xk - mean_g * mean_g) / var_g;
    }

    /* JSON output */
    char path[512];
    build_path(path, sizeof(path), "autocorr", suffix);
    FILE *out = fopen(path, "w");
    if (!out) { fprintf(stderr, "Cannot open %s\n", path); return 1; }
    fprintf(out, "{\n");
    fprintf(out, "  \"N\":            %lu,\n", (unsigned long) N);
    fprintf(out, "  \"n_primes\":     %lu,\n", (unsigned long) total_primes);
    fprintf(out, "  \"n_gaps\":       %lu,\n", (unsigned long) n_gaps);
    fprintf(out, "  \"mean_g\":       %.12Lg,\n", mean_g);
    fprintf(out, "  \"var_g\":        %.12Lg,\n", var_g);
    fprintf(out, "  \"max_lag\":      %d,\n", MAX_LAG);
    fprintf(out, "  \"rho\": [");
    for (int k = 0; k <= MAX_LAG; k++) {
        fprintf(out, "%s%.10Lg",
                k == 0 ? "" : ", ", rho[k]);
    }
    fprintf(out, "],\n");
    fprintf(out, "  \"wall_seconds\": %.3f\n", t_elapsed);
    fprintf(out, "}\n");
    fclose(out);

    fprintf(stderr, "Wrote %s\n", path);
    fprintf(stderr, "  N      = %lu\n", (unsigned long) N);
    fprintf(stderr, "  n_gaps = %lu\n", (unsigned long) n_gaps);
    fprintf(stderr, "  mean_g = %.6Lg, var_g = %.6Lg\n", mean_g, var_g);
    for (int k = 1; k <= MAX_LAG; k++) {
        fprintf(stderr, "  rho(%2d) = %+.5Lg\n", k, rho[k]);
    }
    fprintf(stderr, "  wall   = %.2f s\n", t_elapsed);

    return 0;
}
