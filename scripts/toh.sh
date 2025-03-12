#!/bin/bash

OUTPUT_DIR="data/toh"
weights=(1 1.2 1.5 2 5 10)
epsilons=(1 0.99 0.9 0.75 0.5 0.25 0.1 0.01 0)

OUTPUT_DIR="data/toh"
BASE_CMD="./src/bin/release/balance -d TOH -i 0-100"

# Move to base dir and make dirs for data and heuristics
cd "$(dirname "$0")/.." || exit 1
mkdir -p $OUTPUT_DIR

for i in {10..6..-2}; do
  ho=$i+$((12-i))
  hg=$i+0
  echo "-- Working on $ho $hg --"
  CMD="$BASE_CMD -ho $ho -hg $hg"
  echo "Running initial heuristic"
  $CMD --no-run -w 1 -e 1 > "$OUTPUT_DIR/toh_${i}_init.out"

  # GBFS
  for epsilon in "${epsilons[@]}"; do
    echo "Running GBFS with e=$epsilon"
    $CMD -a GBFS -w 1 -e "$epsilon" > "$OUTPUT_DIR/toh_${i}_gbfs_e${epsilon}.out"
  done

  # Weighted A*
  for weight in "${weights[@]}"; do
    for epsilon in "${epsilons[@]}"; do
      echo "Running WA* with w=$weight and e=$epsilon"
      $CMD -a WA -w "$weight" -e "$epsilon" > "$OUTPUT_DIR/toh_${i}_wa_w${weight}_e${epsilon}.out"
    done
  done

  # IOS
  for weight in "${weights[@]:1}"; do
    for epsilon in "${epsilons[@]}"; do
      echo "Running IOS with w=$weight and e=$epsilon"
      $CMD -a IOS -w "$weight" -e "$epsilon" > "$OUTPUT_DIR/toh_${i}_ios_w${weight}_e${epsilon}.out"
    done
  done
done
