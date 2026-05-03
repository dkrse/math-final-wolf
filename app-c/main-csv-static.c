/*
 * gap_histogram.c
 *
 * Generates the complete distribution of gaps between primes in the range
 * [2, N] using the primesieve library. Output:
 *   - stdout: record gaps with their position and merit ratio
 *   - gaps.csv: histogram of all gaps
 *   - records.csv: list of record gaps in machine-readable format
 *
 * Compilation:
 *   gcc -O2 -o gap_histogram gap_histogram.c -lprimesieve -lm
 *
 * Usage:
 *   ./gap_histogram [-o SUFFIX] <N> [stride]
 *     N         - upper bound (e.g. 1e10 or 10000000000)
 *     stride    - optional sampling step for gap_stream.csv
 *                 (1 = every gap, 1000 = every 1000th, 0 = stream disabled)
 *                 default: 0 (stream is not written)
 *     -o SUFFIX - optional output filename suffix; when set, outputs are
 *                 gaps_<SUFFIX>.csv, records_<SUFFIX>.csv,
 *                 gap_stream_<SUFFIX>.csv. Default: no suffix (gaps.csv).
 *
 * Examples:
 *   ./gap_histogram 1e10                       # gaps.csv, records.csv
 *   ./gap_histogram 1e10 1000                  # + stream of every 1000th gap
 *   ./gap_histogram -o N1e13 1e13              # gaps_N1e13.csv, records_N1e13.csv
 *   ./gap_histogram -o N1e13 1e13 100000000    # + sampled stream
 */

#include <primesieve.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* Maximum histogram size. A gap > 4096 is impossible up to 10^15 (the largest
 * known up to 2^64 is ~1552). 4096 is kept as a safety margin. */
#define MAX_GAP 4096

static int build_path(char *buf, size_t buflen, const char *base,
                      const char *suffix) {
    /* Compose <base>.csv or <base>_<suffix>.csv into buf. */
    if (suffix && suffix[0] != '\0') {
        return snprintf(buf, buflen, "%s_%s.csv", base, suffix);
    }
    return snprintf(buf, buflen, "%s.csv", base);
}

int main(int argc, char *argv[]) {
    const char *suffix = "";
    const char *positional[2] = {NULL, NULL};
    int n_pos = 0;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-o") == 0) {
            if (i + 1 >= argc) {
                fprintf(stderr, "Error: -o requires an argument\n");
                return 1;
            }
            suffix = argv[++i];
        } else if (n_pos < 2) {
            positional[n_pos++] = argv[i];
        } else {
            fprintf(stderr, "Error: unexpected argument '%s'\n", argv[i]);
            return 1;
        }
    }

    if (n_pos < 1) {
        fprintf(stderr, "Usage: %s [-o SUFFIX] <N> [stride]\n", argv[0]);
        fprintf(stderr, "  N         - upper bound (e.g. 1e10)\n");
        fprintf(stderr, "  stride    - gap stream sampling step (0 = disabled)\n");
        fprintf(stderr, "  -o SUFFIX - output filename suffix (gaps_SUFFIX.csv, ...)\n");
        return 1;
    }

    /* Parse N - scientific notation such as 1e10 is also supported */
    uint64_t N = (uint64_t) strtod(positional[0], NULL);
    if (N < 3) {
        fprintf(stderr, "N must be at least 3\n");
        return 1;
    }

    /* Stride for stream sampling (0 = stream disabled) */
    uint64_t stride = 0;
    if (n_pos == 2) {
        stride = (uint64_t) strtoull(positional[1], NULL, 10);
    }

    /* Compose output filenames */
    char path_hist[512], path_rec[512], path_stream[512];
    build_path(path_hist,   sizeof(path_hist),   "gaps",       suffix);
    build_path(path_rec,    sizeof(path_rec),    "records",    suffix);
    build_path(path_stream, sizeof(path_stream), "gap_stream", suffix);

    /* Histogram allocation - uint64_t for large ranges */
    uint64_t *histogram = calloc(MAX_GAP, sizeof(uint64_t));
    if (!histogram) {
        fprintf(stderr, "Memory allocation error\n");
        return 1;
    }

    /* Record array - kept in memory and written at the end */
    typedef struct {
        uint64_t gap;
        uint64_t p_start;   /* prime after which the record occurs */
        double merit;        /* g / ln(p_start) */
    } Record;

    size_t records_capacity = 256;
    size_t records_count = 0;
    Record *records = malloc(records_capacity * sizeof(Record));

    /* Run statistics */
    uint64_t total_primes = 0;
    uint64_t total_gaps = 0;
    uint64_t overflow_count = 0;   /* number of gaps that exceeded MAX_GAP */

    /* Optional stream of gaps (p_start, gap) for sequential analysis */
    FILE *f_stream = NULL;
    if (stride > 0) {
        f_stream = fopen(path_stream, "w");
        if (!f_stream) {
            fprintf(stderr, "Cannot open %s for writing\n", path_stream);
            free(histogram);
            free(records);
            return 1;
        }
        fprintf(f_stream, "p_start,gap\n");
    }
    uint64_t stream_written = 0;

    printf("Analysis of prime gaps in the range [2, %lu]\n", (unsigned long) N);
    if (stride > 0) {
        printf("Stream: every %lu-th gap -> %s\n",
               (unsigned long) stride, path_stream);
    }
    printf("=========================================================\n");

    clock_t t_start = clock();

    /* Iterator initialization */
    primesieve_iterator it;
    primesieve_init(&it);

    uint64_t prev = primesieve_next_prime(&it);
    total_primes = 1;
    uint64_t max_gap = 0;

    /* Main loop */
    uint64_t curr = primesieve_next_prime(&it);
    while (curr <= N) {
        uint64_t gap = curr - prev;
        total_primes++;
        total_gaps++;

        /* Histogram */
        if (gap < MAX_GAP) {
            histogram[gap]++;
        } else {
            overflow_count++;
        }

        /* Stream of sampled gaps */
        if (f_stream && (total_gaps % stride == 0)) {
            fprintf(f_stream, "%lu,%lu\n",
                    (unsigned long) prev, (unsigned long) gap);
            stream_written++;
        }

        /* Record detection */
        if (gap > max_gap) {
            max_gap = gap;
            double merit = (double) gap / log((double) prev);

            if (records_count >= records_capacity) {
                records_capacity *= 2;
                records = realloc(records, records_capacity * sizeof(Record));
            }
            records[records_count].gap = gap;
            records[records_count].p_start = prev;
            records[records_count].merit = merit;
            records_count++;

            printf("New record gap: %lu at p=%lu  (merit=%.3f)\n",
                   (unsigned long) gap, (unsigned long) prev, merit);
            fflush(stdout);
        }

        prev = curr;
        curr = primesieve_next_prime(&it);
    }

    primesieve_free_iterator(&it);

    if (f_stream) {
        fclose(f_stream);
    }

    double t_elapsed = (double) (clock() - t_start) / CLOCKS_PER_SEC;

    /* Write histogram to CSV */
    FILE *f_hist = fopen(path_hist, "w");
    if (!f_hist) {
        fprintf(stderr, "Cannot open %s for writing\n", path_hist);
        free(histogram);
        free(records);
        return 1;
    }

    fprintf(f_hist, "gap,count\n");
    for (int g = 1; g < MAX_GAP; g++) {
        if (histogram[g] > 0) {
            fprintf(f_hist, "%d,%lu\n", g, (unsigned long) histogram[g]);
        }
    }
    fclose(f_hist);

    /* Write records to CSV */
    FILE *f_rec = fopen(path_rec, "w");
    if (!f_rec) {
        fprintf(stderr, "Cannot open %s for writing\n", path_rec);
        free(histogram);
        free(records);
        return 1;
    }

    fprintf(f_rec, "gap,p_start,ln_p,merit\n");
    for (size_t i = 0; i < records_count; i++) {
        fprintf(f_rec, "%lu,%lu,%.6f,%.6f\n",
                (unsigned long) records[i].gap,
                (unsigned long) records[i].p_start,
                log((double) records[i].p_start),
                records[i].merit);
    }
    fclose(f_rec);

    /* Summary */
    printf("\n=========================================================\n");
    printf("Summary:\n");
    printf("  Range:               [2, %lu]\n", (unsigned long) N);
    printf("  Number of primes:    %lu\n", (unsigned long) total_primes);
    printf("  Number of gaps:      %lu\n", (unsigned long) total_gaps);
    printf("  Largest gap:         %lu\n", (unsigned long) max_gap);
    printf("  Number of records:   %zu\n", records_count);
    printf("  Running time:        %.2f s\n", t_elapsed);
    if (overflow_count > 0) {
        printf("  WARNING: %lu gaps >= %d (not stored in histogram)\n",
               (unsigned long) overflow_count, MAX_GAP);
    }
    printf("\nOutput files:\n");
    printf("  %s - histogram of all gaps\n", path_hist);
    printf("  %s - record gaps\n", path_rec);
    if (stride > 0) {
        printf("  %s - %lu sampled gaps (stride=%lu)\n",
               path_stream, (unsigned long) stream_written,
               (unsigned long) stride);
    }

    free(histogram);
    free(records);
    return 0;
}
