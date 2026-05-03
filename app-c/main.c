#include <primesieve.h>
#include <stdio.h>
#include <inttypes.h>

int main() {
    // Iterator - the most memory-efficient approach
    primesieve_iterator it;
    primesieve_init(&it);

    uint64_t prime = primesieve_next_prime(&it);
    uint64_t prev = 0;
    uint64_t max_gap = 0;

    while (prime < 1000000000000ULL) {  // up to 10^12
        if (prev != 0) {
            uint64_t gap = prime - prev;
            if (gap > max_gap) {
                max_gap = gap;
                printf("New record gap: %" PRIu64 " at p=%" PRIu64 "\n", gap, prev);
            }
        }
        prev = prime;
        prime = primesieve_next_prime(&it);
    }

    primesieve_free_iterator(&it);
    return 0;
}
