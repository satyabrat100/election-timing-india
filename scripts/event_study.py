"""Event study, stacked (heterogeneity-robust) estimates, placebo election dates,
alternative definitions of simultaneity and minimum detectable effects (Section 6).

Output: ../results/event_study.json, ../figures/fig4_event_study.png
"""
import pandas as pd, numpy as np, json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B = os.path.join(os.path.dirname(__file__), '..')
R = os.path.join(B, 'results')
rng = np.random.default_rng(20261122)
p = pd.read_csv(os.path.join(R, 'panel.csv'))
ae = pd.read_csv(os.path.join(R, 'assembly_elections_fy.csv'))
w = lambda x: x.clip(x.quantile(0.025), x.quantile(0.975))
for c in ['g_ce', 'g_re', 'g_rr']:
    p[c + '_w'] = w(p[c])


def demean2(df, cols, a='State', b='fy'):
    X = df[cols].astype(float).copy()
    for _ in range(300):
        X0 = X.copy()
        X = X - X.groupby(df[a]).transform('mean')
        X = X - X.groupby(df[b]).transform('mean')
        if np.abs(X - X0).to_numpy().max() < 1e-10:
            break
    return X


def ols_cl(d, y, xs, a='State', b='fy', cl='State'):
    d = d.dropna(subset=[y] + xs)
    W = demean2(d, [y] + xs, a, b)
    Y, X = W[y].to_numpy(), W[xs].to_numpy()
    XtXi = np.linalg.pinv(X.T @ X)
    bhat = XtXi @ X.T @ Y
    e = Y - X @ bhat
    g = d[cl].to_numpy()
    meat = np.zeros((len(xs), len(xs)))
    for k in np.unique(g):
        s = X[g == k].T @ e[g == k]
        meat += np.outer(s, s)
    m, n = len(np.unique(g)), len(Y)
    V = m / (m - 1) * XtXi @ meat @ XtXi
    return bhat, np.sqrt(np.diag(V)), n, m


def evt_vars(d, years_by_state, prefix='e'):
    """Dummies for years relative to the election year: -2,-1,0,+1,+2 (reference: other years)."""
    out = {}
    for k in (-2, -1, 0, 1, 2):
        out[f'{prefix}{k:+d}'] = [int(any(fy - e == k for e in years_by_state.get(s, []))) for s, fy in zip(d.State, d.fy)]
    return pd.DataFrame(out, index=d.index)


ey = ae.groupby('State').fy.apply(list).to_dict()
EV = ['e-2', 'e+0', 'e+1', 'e+2']  # reference: year -1
res = {'event': {}, 'stacked': {}, 'placebo': {}, 'alt_sim': {}, 'mde': {}}
samples = {'g_ce_w': (2014, 2022), 'g_re_w': (2014, 2022), 'fd_rr': (2013, 2022), 'ce_share': (2013, 2022), 'g_gsdp': (2012, 2021)}
for y, (a, b) in samples.items():
    d = p[(p.fy >= a) & (p.fy <= b)].copy()
    d = pd.concat([d, evt_vars(d, ey)], axis=1)
    bh, se, n, m = ols_cl(d, y, EV)
    res['event'][y] = {k: [round(float(bh[i]), 3), round(float(se[i]), 3)] for i, k in enumerate(EV)}
    res['event'][y]['_n'] = int(n)
    # minimum detectable effect (80% power, 5% two-sided) for the election-year coefficient
    res['mde'][y] = round(float(2.8 * se[1]), 2)

# stacked event study: one sub-panel per election episode, window -1..+1, clean controls
# (states with no assembly election in t-1, t or t+1), episode-specific unit and year effects.
# Comparing +1 with -1 is the post-minus-pre design with clean controls.
def stacked(y, a, b):
    rows = []
    for i, r in ae.iterrows():
        if not (a <= r.fy <= b):
            continue
        win = range(r.fy - 1, r.fy + 2)
        ctrl = [s for s in p.State.unique() if s != r.State and not any(abs(e - r.fy) <= 1 for e in ey.get(s, []))]
        sub = p[p.State.isin([r.State] + ctrl) & p.fy.isin(win) & (p.fy >= a) & (p.fy <= b)].copy()
        sub['ep'] = i
        sub['treated'] = (sub.State == r.State).astype(int)
        sub['rel'] = sub.fy - r.fy
        sub['sim'] = int(r.with_lok_sabha)
        rows.append(sub)
    S = pd.concat(rows)
    S['unit'] = S.ep.astype(str) + '_' + S.State
    S['epyr'] = S.ep.astype(str) + '_' + S.fy.astype(str)
    for k in (-1, 0, 1):
        S[f'r{k:+d}'] = ((S.treated == 1) & (S.rel == k)).astype(int)
    xs = ['r+0', 'r+1']  # reference: year -1
    bh, se, n, m = ols_cl(S, y, xs, a='unit', b='epyr', cl='State')
    out = {k: [round(float(bh[i]), 3), round(float(se[i]), 3)] for i, k in enumerate(xs)}
    # simultaneous vs other episodes: post (+1) minus pre (-1) difference
    S['r+1_sim'] = S['r+1'] * S.sim
    S['r+0_sim'] = S['r+0'] * S.sim
    bh2, se2, _, _ = ols_cl(S, y, xs + ['r+0_sim', 'r+1_sim'], a='unit', b='epyr', cl='State')
    out['r+0_sim'] = [round(float(bh2[2]), 3), round(float(se2[2]), 3)]
    out['r+1_sim'] = [round(float(bh2[3]), 3), round(float(se2[3]), 3)]
    # same, dropping 2019-20 episodes (post year 2020-21) and 2020-21 itself
    S2 = S[~S.fy.isin([2020])]
    bh3, se3, _, _ = ols_cl(S2, y, xs + ['r+0_sim', 'r+1_sim'], a='unit', b='epyr', cl='State')
    out['r+1_sim_nocovid'] = [round(float(bh3[3]), 3), round(float(se3[3]), 3)]
    out['_n'], out['_episodes'] = int(n), int(S.ep.nunique())
    return out


for y, (a, b) in samples.items():
    res['stacked'][y] = stacked(y, a, b)

# placebo: shift every state's election years by a random common offset (1-4 years, mod 5)
# and re-estimate the run-up and simultaneity coefficients of Table 2
fis = p[(p.fy >= 2014) & (p.fy <= 2022)].copy()
for y in ['ce_share', 'g_rr_w', 'g_ce_w']:
    draws = []
    for rep in range(500):
        d = fis.copy()
        off = {s: int(rng.integers(1, 5)) for s in d.State.unique()}
        d['runup_p'] = 0
        for s in d.State.unique():
            idx = d.State == s
            d.loc[idx, 'runup_p'] = p[p.State == s].set_index('fy').runup.reindex(d.loc[idx, 'fy'] - off[s]).fillna(0).to_numpy()
        bh, se, n, m = ols_cl(d, y, ['runup_p'])
        draws.append(bh[0])
    bh, se, n, m = ols_cl(fis, y, ['runup'])
    draws = np.array(draws)
    res['placebo'][y] = {'actual_runup_b': round(float(bh[0]), 3), 'placebo_p5': round(float(np.percentile(draws, 5)), 3),
                         'placebo_p95': round(float(np.percentile(draws, 95)), 3),
                         'share_abs_ge_actual': round(float((np.abs(draws) >= abs(bh[0])).mean()), 3)}

# alternative definition: simultaneous = results within 6 months of a Lok Sabha result
ls = pd.to_datetime(['2014-05-16', '2019-05-23'])
ae['rd'] = pd.to_datetime(ae.result_date)
ae['near'] = ae.rd.apply(lambda x: int(min(abs((x - l).days) for l in ls) <= 183))
near = set(zip(ae[ae.near == 1].State, ae[ae.near == 1].runup_fy))
p['runup_near'] = [int((s, f) in near) for s, f in zip(p.State, p.fy)]
fis = p[(p.fy >= 2014) & (p.fy <= 2022)]
for y in ['ce_share', 'g_rr_w', 'fd_rr', 'g_ce_w']:
    bh, se, n, m = ols_cl(fis, y, ['runup', 'runup_near', 'post'])
    res['alt_sim'][y] = {'runup_near': [round(float(bh[1]), 3), round(float(se[1]), 3)], 'n_near_episodes': int(ae.near.sum())}
json.dump(res, open(os.path.join(R, 'event_study.json'), 'w'), indent=1)
print(json.dumps(res, indent=1))

# figure: event-study coefficients with 95% confidence intervals
fig, axes = plt.subplots(1, 3, figsize=(9, 3.0))
labs = {'fd_rr': 'Fiscal deficit (% of revenue receipts)', 'ce_share': 'Capital share of spending (pp)', 'g_gsdp': 'GSDP growth (pp)'}
for ax, y in zip(axes, labs):
    st = res['event'][y]
    ks = [-2, -1, 0, 1, 2]
    bb = [st['e-2'][0], 0, st['e+0'][0], st['e+1'][0], st['e+2'][0]]
    ss = [st['e-2'][1], 0, st['e+0'][1], st['e+1'][1], st['e+2'][1]]
    ax.errorbar(ks, bb, yerr=1.96 * np.array(ss), fmt='o', color='#4C72B0', capsize=3)
    ax.axhline(0, color='black', lw=0.6)
    ax.set_title(labs[y], fontsize=8)
    ax.set_xticks(ks)
    ax.set_xlabel('Years relative to election', fontsize=8)
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(B, 'figures', 'fig4_event_study.png'), dpi=300)
