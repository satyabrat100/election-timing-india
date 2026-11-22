"""Stacked estimate restricted to episodes with GSDP growth observed in t-1, t and t+1
(the 47 episodes of the post-minus-pre comparison). Output: ../results/stacked_full_window.json"""
import json, os, pandas as pd, numpy as np
ns = {'__file__': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'event_study.py')}
src = open(ns['__file__']).read().split('# placebo:')[0].split('for y, (a, b) in samples.items():\n    res[\'stacked\']')[0]
exec(src, ns)
p, ae, ey, ols_cl = ns['p'], ns['ae'], ns['ey'], ns['ols_cl']
gg = p.set_index(['State', 'fy']).g_gsdp
rows = []
for i, r in ae.iterrows():
    if not all((r.State, r.fy + k) in gg.index and pd.notna(gg[(r.State, r.fy + k)]) for k in (-1, 0, 1)):
        continue
    ctrl = [s for s in p.State.unique() if s != r.State and not any(abs(e - r.fy) <= 1 for e in ey.get(s, []))]
    sub = p[p.State.isin([r.State] + ctrl) & p.fy.isin(range(r.fy - 1, r.fy + 2))].copy()
    sub['ep'], sub['treated'], sub['rel'], sub['sim'] = i, (sub.State == r.State).astype(int), sub.fy - r.fy, int(r.with_lok_sabha)
    rows.append(sub)
S = pd.concat(rows)
S['unit'] = S.ep.astype(str) + '_' + S.State
S['epyr'] = S.ep.astype(str) + '_' + S.fy.astype(str)
for k in (0, 1):
    S[f'r+{k}'] = ((S.treated == 1) & (S.rel == k)).astype(int)
S['r+0_sim'], S['r+1_sim'] = S['r+0'] * S.sim, S['r+1'] * S.sim
b, se, n, m = ols_cl(S, 'g_gsdp', ['r+0', 'r+1', 'r+0_sim', 'r+1_sim'], a='unit', b='epyr', cl='State')
out = {'episodes': int(S.ep.nunique()), 'r+1_sim': [round(float(b[3]), 3), round(float(se[3]), 3)], 'mde_r+1_sim': round(float(2.8 * se[3]), 2)}
json.dump(out, open(os.path.join(os.path.dirname(__file__), '..', 'results', 'stacked_full_window.json'), 'w'), indent=1)
print(out)
