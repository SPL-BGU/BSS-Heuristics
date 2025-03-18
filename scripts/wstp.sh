#!/bin/bash

OUTPUT_DIR="data/stp"
weights=(1 1.2 1.5 2 5 10 20 50)
epsilons=(1 0.99 0.9 0.75 0.5 0.25 0.1 0.01 0)

OUTPUT_DIR="data/wstp"
CMD="./src/bin/release/balance -d WSTP -ho wmd -hg md -i 0-100"

# Move to base dir and make dirs for data and heuristics
cd "$(dirname "$0")/.." || exit 1
mkdir -p $OUTPUT_DIR

# Run heuristic-init for h/C* and GDRC calculations
echo "Running initial heuristic"
$CMD --no-run -w 1 -e 1 > "$OUTPUT_DIR/wstp_heu_init.out"

# GBFS
for epsilon in "${epsilons[@]}"; do
  echo "Running GBFS with e=$epsilon"
  $CMD -a GBFS -w 1 -e "$epsilon" > "$OUTPUT_DIR/wstp_gbfs_e${epsilon}.out"
done

# Weighted A*
for weight in "${weights[@]}"; do
  for epsilon in "${epsilons[@]}"; do
    echo "Running WA* with w=$weight and e=$epsilon"
    $CMD -a WA -w "$weight" -e "$epsilon" > "$OUTPUT_DIR/wstp_wa_w${weight}_e${epsilon}.out"
  done
done

# IOS
for weight in "${weights[@]}"; do
  for epsilon in "${epsilons[@]}"; do
    echo "Running IOS with w=$weight and e=$epsilon"
    $CMD -a IOS -w "$weight" -e "$epsilon" > "$OUTPUT_DIR/wstp_ios_w${weight}_e${epsilon}.out"
  done
done
