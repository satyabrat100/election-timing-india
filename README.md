# Replication package: Election timing and the Indian economy

Reproduces all tables and figures with one command: `bash run_all.sh` (Python 3.11+, packages in requirements.txt). Random seed 20261122.

## Data (data/)
| File | Content | Source |
|---|---|---|
| election_calendar.csv | Last poll date and counting date of every assembly election, 2010-2023, and the 2014, 2019 and 2024 general elections; flags for elections held with the Lok Sabha and for early (unscheduled) elections | Compiled by the author from Election Commission of India schedules and results announcements |
| cag_state_finances_2013_2023.csv | Revenue receipts, revenue and capital expenditure, committed expenditure, fiscal and revenue balance, debt; 28 states, 2013-14 to 2022-23, Rs crore | CAG, State Finances 2022-23: Decadal Analysis (machine-readable version: github.com/Arithmetic-Power-Geometry/CAG-State-Finances-Dataset, CC BY 4.0) |
| gsdp_constant_2011_12.csv | GSDP at constant 2011-12 prices, Rs lakh; 31 states/UTs, 2011-12 to 2021-22 | RBI, Handbook of Statistics on Indian States 2024-25, Table 22 (machine-readable copy from github.com/NANDINISHARMA0103/Indian-States-Fiscal-Panel; checked against the RBI table for West Bengal and Uttarakhand, 2011-12 to 2016-17) |

Variable definitions: data/VARIABLES.md.

## Map of results
| Paper | Script | Output |
|---|---|---|
| Table 1, Figure 1 | calendar_facts.py | results/calendar.json, figures/fig1_calendar.png |
| Table 2 and Section 6.1 robustness | fiscal_cycle.py | results/fiscal_cycle.json |
| Table 3 (event study, wild bootstrap for the deficit), Section 6.3 placebo and alternative definitions, minimum detectable effects, Figure 2 | event_study.py, fiscal_cycle.py | results/event_study.json, results/fiscal_cycle.json (event_fd_rr_wild), figures/fig4_event_study.png |
| Section 6.4: stacked estimate on the 47 full-window episodes | stacked_full_window.py | results/stacked_full_window.json |
| Table 4, Figure 3 | fiscal_cycle.py, figures.py | results/fiscal_cycle.json (episodes_*), results/episodes.csv, figures/fig2_episodes.png |
| Tables 5-10, Sections 7.1-7.7, Figure 4 (kappa scenarios: kappa_scenarios; waste scenarios: waste_scenarios) | calibrate.py, figures.py | results/calibration.json, figures/fig3_gains.png |

Note: figure file names differ from the paper's figure numbers as shown above.

## Software
Python 3.11 or later; numpy, scipy, pandas, matplotlib (versions in requirements.txt). Run time about 5 minutes on a laptop.

## Notes
- Telangana 2013-14 and Andhra Pradesh 2013-14 fiscal values are set to missing (state created June 2014; undivided accounts).
- Election year = fiscal year of results; run-up year = fiscal year holding most of the 12 months before polling.
- Calibration parameters are assumptions (see Table 4 of the paper).
