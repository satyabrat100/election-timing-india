# Variable dictionary

## data/election_calendar.csv (one row per election)
| Variable | Definition |
|---|---|
| state | State or union territory; "Lok Sabha" for general elections |
| election | Identifier, e.g. AE2016 (assembly election), LS2019 (Lok Sabha) |
| poll_end | Date of the last poll (YYYY-MM-DD) |
| result_date | Date of counting / declaration of results |
| with_lok_sabha | 1 if results were declared together with a Lok Sabha general election |
| scheduled | 1 if held at the end of a full term; 0 if after an early dissolution (Delhi 2015, Telangana 2018) |
Source: compiled by the author from Election Commission of India schedules and results announcements.

## data/cag_state_finances_2013_2023.csv (state x fiscal year, Rs crore)
| Variable | Definition |
|---|---|
| State, Year | State; fiscal year (April-March) |
| Revenue Receipts | Total revenue receipts |
| Revenue Expenditure | Total revenue expenditure |
| Capital Expenditure | Capital outlay |
| Committed Expenditure | Salaries, pensions and interest |
| Public Debt+Public Account Liability, Public Account Liability | Liabilities |
| Revenue Surplus(+)/Deficit(-), Fiscal Surplus(+)/Deficit(-) | Balances |
| Outstanding Debt, Outstanding Guarantees | Stocks at year end |
Source: CAG, State Finances 2022-23: Decadal Analysis, Annexures 1, 4, 5, 11, 12 (machine-readable version, CC BY 4.0).

## data/gsdp_constant_2011_12.csv (state x fiscal year)
| Variable | Definition |
|---|---|
| State, Year | State/UT; fiscal year |
| gsdp_const_2011_12_lakh | GSDP at constant 2011-12 prices, Rs lakh |
Source: RBI, Handbook of Statistics on Indian States 2024-25, Table 22.

## results/panel.csv (constructed by build_panel.py)
| Variable | Definition |
|---|---|
| fy | Fiscal year starting in April of this calendar year |
| g_gsdp, g_re, g_ce, g_rr, g_committed | 100 x log difference of GSDP, revenue expenditure, capital expenditure, revenue receipts, committed expenditure |
| fd_rr | Fiscal deficit as % of revenue receipts |
| ce_share | Capital expenditure as % of revenue plus capital expenditure |
| elec | 1 in the fiscal year in which assembly election results were declared |
| runup | 1 in the fiscal year holding most of the 12 months before polling (election year if polling ended Oct-Mar; previous year if Apr-Sep) |
| elec_sim, runup_sim | Same, for elections held with the Lok Sabha |
| elec_sched, runup_sched | Same, for scheduled elections only |
| post, post_sim | 1 in the year after the election year |
