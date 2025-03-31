#!/bin/bash

cd "$(dirname "$0")/.." || exit 1
echo "---Handling ToH Results---"
python3 analysis/toh_analysis.py
echo "---Handling STP Results---"
python3 analysis/stp_analysis.py
echo "---Handling WSTP Results---"
python3 analysis/wstp_analysis.py
