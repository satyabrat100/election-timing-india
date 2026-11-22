"""Facts about India's election calendar, 2014-2023 (two full Lok Sabha terms).

Outputs ../results/calendar.json and ../figures/fig1_calendar.png
Assumption (sensitivity): length of the Model Code of Conduct for an assembly election,
L_S in {35, 45, 60} days; for the Lok Sabha we use the reported 80 days of 2024.
"""
import pandas as pd, numpy as np, json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B = os.path.join(os.path.dirname(__file__), '..')
cal = pd.read_csv(os.path.join(B, 'data', 'election_calendar.csv'), parse_dates=['poll_end', 'result_date'])
g = pd.read_csv(os.path.join(B, 'data', 'gsdp_constant_2011_12.csv'))
w = g[g.Year == '2018-19'].set_index('State').gsdp_const_2011_12_lakh
w = w / w.sum()

ae = cal[(cal.state != 'Lok Sabha') & (cal.result_date >= '2014-01-01') & (cal.result_date < '2024-01-01')].copy()
ae['w'] = ae.state.map(w).fillna(0)
ae['year'] = ae.result_date.dt.year
# election windows: result dates within 45 days of each other belong to one window
d = sorted(set(ae.result_date))
windows, cur = [], [d[0]]
for x in d[1:]:
    if (x - cur[-1]).days <= 45:
        cur.append(x)
    else:
        windows.append(cur); cur = [x]
windows.append(cur)
win_id = {x: i for i, ws in enumerate(windows) for x in ws}
ae['window'] = ae.result_date.map(win_id)
per_year = ae.groupby('year').agg(n_states=('state', 'count'), gdp_share=('w', 'sum'),
                                  windows=('window', 'nunique')).reset_index()
off = ae[ae.with_lok_sabha == 0]
res = {
    'assembly_elections_2014_2023': int(len(ae)),
    'with_lok_sabha': int(ae.with_lok_sabha.sum()),
    'windows_2014_2023': len(windows),
    'windows_per_term': round(len(windows) / 2, 1),
    'years_with_assembly_election': int(per_year.year.nunique()),
    'gdp_share_voting_off_cycle_per_term': round(float(off.w.sum() / 2), 3),
    'gdp_share_with_ls_per_term': round(float(ae[ae.with_lok_sabha == 1].w.sum() / 2), 3),
    'per_year': per_year.round(3).to_dict(orient='records'),
}
# GDP-weighted days under a Model Code of Conduct per year
for L in (35, 45, 60):
    days = (off.w * L).groupby(off.year).sum()
    res[f'mcc_gdp_days_offcycle_per_year_L{L}'] = round(float(days.sum() / 10), 1)
res['mcc_gdp_days_ls_per_year'] = round(80 / 5, 1)
json.dump(res, open(os.path.join(B, 'results', 'calendar.json'), 'w'), indent=1)
print(json.dumps(res, indent=1))

fig, ax = plt.subplots(figsize=(7, 3.4))
ax.bar(per_year.year, 100 * per_year.gdp_share, color='#4C72B0')
for _, r in per_year.iterrows():
    ax.text(r.year, 100 * r.gdp_share + 1, f"{int(r.n_states)} states\n{int(r.windows)} window(s)", ha='center', fontsize=7)
ax.set_ylabel('Share of GSDP in states voting (%)')
ax.set_xticks(per_year.year)
ax.set_ylim(0, 60)
ax.set_title('Assembly elections by year, 2014-2023 (Lok Sabha polls in 2014 and 2019)', fontsize=9)
for s in ('top', 'right'):
    ax.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(B, 'figures', 'fig1_calendar.png'), dpi=300)
