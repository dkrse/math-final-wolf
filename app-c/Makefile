CC      := gcc
CFLAGS  := -O3 -Wall
LDLIBS  := -lprimesieve -lm

BUILD   := build
STATIC_LIB := /usr/local/lib/libprimesieve.a

BINS := $(BUILD)/main $(BUILD)/main-csv $(BUILD)/main-csv-static $(BUILD)/main-autocorr

.PHONY: all clean
all: $(BINS)

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/main: main.c | $(BUILD)
	$(CC) $(CFLAGS) $< -o $@ $(LDLIBS)

$(BUILD)/main-csv: main-csv.c | $(BUILD)
	$(CC) $(CFLAGS) $< -o $@ $(LDLIBS)

$(BUILD)/main-csv-static: main-csv-static.c | $(BUILD)
	$(CC) $(CFLAGS) $< -o $@ $(STATIC_LIB) -lm -lstdc++

$(BUILD)/main-autocorr: main-autocorr.c | $(BUILD)
	$(CC) $(CFLAGS) $< -o $@ $(STATIC_LIB) -lm -lstdc++

clean:
	rm -rf $(BUILD)
