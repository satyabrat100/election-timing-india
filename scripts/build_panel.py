"""Build the state-year panel used in the paper.

Inputs (../data):
  election_calendar.csv            assembly and Lok Sabha elections, 2010-2024
  cag_state_finances_2013_2023.csv  CAG State Finances 2022-23 (Decadal Analysis), Rs crore
  gsdp_constant_2011_12.csv        GSDP at constant 2011-12 prices (RBI Handbook), Rs lakh
Output (../results/panel.csv)
"""
import pandas as pd, numpy as np, os
D = os.path.join(os.path.dirname(__file__), '..', 'data')
R = os.path.join(os.path.dirname(__file__), '..', 'results')

def fy_of(date):
    """Fiscal year label 'YYYY-YY' containing the date (April-March)."""
    y = date.year if date.month >= 4 else date.year - 1
    return y

cal = pd.read_csv(os.path.join(D, 'election_calendar.csv'), parse_dates=['poll_end', 'result_date'])
ae = cal[cal.state != 'Lok Sabha'].copy()
ae['fy'] = ae.result_date.apply(fy_of)
# run-up fiscal year: the fiscal year holding most of the 12 months before polling
ae['runup_fy'] = np.where(ae.poll_end.dt.month.isin([4, 5, 6, 7, 8, 9]), ae.fy - 1, ae.fy)

g = pd.read_csv(os.path.join(D, 'gsdp_constant_2011_12.csv'))
g['fy'] = g.Year.str[:4].astype(int)
f = pd.read_csv(os.path.join(D, 'cag_state_finances_2013_2023.csv'))
f['fy'] = f.Year.str[:4].astype(int)
# Telangana did not exist in 2013-14 (zeros) and the 2013-14 Andhra Pradesh accounts are for the
# undivided state, so 2013-14 values for both are set to missing
num = ['Revenue Receipts', 'Revenue Expenditure', 'Capital Expenditure', 'Committed Expenditure',
       'Fiscal Surplus(+)/Deficit(-)', 'Revenue Surplus(+)/Deficit(-)', 'Outstanding Debt']
f.loc[f.State.isin(['Telangana', 'Andhra Pradesh']) & (f.fy == 2013), num] = np.nan
f = f.rename(columns={'Revenue Receipts': 'rr', 'Revenue Expenditure': 're', 'Capital Expenditure': 'ce',
                      'Committed Expenditure': 'committed', 'Fiscal Surplus(+)/Deficit(-)': 'fiscal_bal',
                      'Revenue Surplus(+)/Deficit(-)': 'rev_bal', 'Outstanding Debt': 'debt'})

states = sorted(set(g.State) | set(f.State))
idx = pd.MultiIndex.from_product([states, range(2010, 2024)], names=['State', 'fy'])
p = pd.DataFrame(index=idx).reset_index()
p = p.merge(g[['State', 'fy', 'gsdp_const_2011_12_lakh']], on=['State', 'fy'], how='left')
p = p.merge(f[['State', 'fy', 'rr', 're', 'ce', 'committed', 'fiscal_bal', 'rev_bal', 'debt']], on=['State', 'fy'], how='left')
p = p.sort_values(['State', 'fy'])
p['g_gsdp'] = 100 * np.log(p.gsdp_const_2011_12_lakh).groupby(p.State).diff()
for v in ['re', 'ce', 'rr', 'committed']:
    p['g_' + v] = 100 * np.log(p[v]).groupby(p.State).diff()
# nominal GSDP not in the inputs; scale fiscal balance by revenue receipts instead
p['fd_rr'] = -100 * p.fiscal_bal / p.rr
p['ce_share'] = 100 * p.ce / (p.ce + p.re)

def flag(col, sub=None):
    s = ae if sub is None else ae[sub]
    key = set(zip(s.State if 'State' in s else s.state, s[col]))
    return [int((a, b) in key) for a, b in zip(p.State, p.fy)]

ae = ae.rename(columns={'state': 'State'})
p['elec'] = flag('fy')
p['runup'] = flag('runup_fy')
p['elec_sim'] = flag('fy', ae.with_lok_sabha == 1)
p['runup_sim'] = flag('runup_fy', ae.with_lok_sabha == 1)
p['elec_sched'] = flag('fy', ae.scheduled == 1)
p['runup_sched'] = flag('runup_fy', ae.scheduled == 1)
p['post'] = p.groupby('State').elec.shift(1).fillna(0).astype(int)
p['post_sim'] = p.groupby('State').elec_sim.shift(1).fillna(0).astype(int)
os.makedirs(R, exist_ok=True)
p.to_csv(os.path.join(R, 'panel.csv'), index=False)
ae.to_csv(os.path.join(R, 'assembly_elections_fy.csv'), index=False)
print(p.describe().T[['count', 'mean', 'std']].round(2))
print('assembly elections in sample:', len(ae), ' with Lok Sabha:', ae.with_lok_sabha.sum())
