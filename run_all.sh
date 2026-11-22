#!/usr/bin/env bash
# Reproduces every table and figure in the paper. Run from this folder: bash run_all.sh
set -e
cd scripts
python3 build_panel.py
python3 calendar_facts.py
python3 fiscal_cycle.py
python3 event_study.py
python3 stacked_full_window.py
python3 calibrate.py
python3 figures.py
echo "Done. Results in results/, figures in figures/."
