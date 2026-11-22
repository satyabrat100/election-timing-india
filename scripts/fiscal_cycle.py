"""Election cycles in Indian state finances and GSDP growth.

Two-way fixed-effects regressions (state and year effects) with standard errors clustered by
state and wild-cluster-bootstrap p-values (Rademacher weights, 4,999 draws, null imposed).
Output: ../results/fiscal_cycle.json
"""
import pandas as pd, numpy as np, json, os
R = os.path.join(os.path.dirname(__file__), '..', 'results')
rng = np.random.default_rng(20261122)
p = pd.read_csv(os.path.join(R, 'panel.csv'))


def winsor(x, q=0.025):
    lo, hi = x.quantile(q), x.quantile(1 - q)
    return x.clip(lo, hi)


def demean2(df, cols):
    """Two-way within transformation by alternating projections (unbalanced panel)."""
    X = df[cols].astype(float).copy()
    for _ in range(200):
        X0 = X.copy()
        X = X - X.groupby(df.State).transform('mean')
        X = X - X.groupby(df.fy).transform('mean')
        if np.abs(X - X0).to_numpy().max() < 1e-10:
            break
    return X


def fe_reg(df, y, xs, B=4999):
    d = df.dropna(subset=[y] + xs).copy()
    W = demean2(d, [y] + xs)
    Y, X = W[y].to_numpy(), W[xs].to_numpy()
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ Y
    e = Y - X @ b
    cl = d.State.to_numpy()
    G = np.unique(cl)
    meat = sum(np.outer(X[cl == g].T @ e[cl == g], X[cl == g].T @ e[cl == g]) for g in G)
    n, k, m = len(Y), X.shape[1] + d.State.nunique() + d.fy.nunique() - 1, len(G)
    c = m / (m - 1) * (n - 1) / (n - k)
    V = c * XtX_inv @ meat @ XtX_inv
    se = np.sqrt(np.diag(V))
    out = {}
    for j, v in enumerate(xs):
        # wild cluster bootstrap with the null b_j = 0 imposed
        Xr = np.delete(X, j, axis=1)
        br = np.linalg.lstsq(Xr, Y, rcond=None)[0] if Xr.shape[1] else np.zeros(0)
        er = Y - (Xr @ br if Xr.shape[1] else 0)
        fit = Y - er
        t0 = b[j] / se[j]
        idx = {g: np.where(cl == g)[0] for g in G}
        cnt = 0
        for _ in range(B):
            w = rng.choice([-1.0, 1.0], size=m)
            ys = fit.copy()
            for gi, g in enumerate(G):
                ys[idx[g]] += w[gi] * er[idx[g]]
            bs = XtX_inv @ X.T @ ys
            es = ys - X @ bs
            meat_s = sum(np.outer(X[idx[g]].T @ es[idx[g]], X[idx[g]].T @ es[idx[g]]) for g in G)
            se_s = np.sqrt(np.diag(c * XtX_inv @ meat_s @ XtX_inv))[j]
            cnt += abs(bs[j] / se_s) >= abs(t0)
        out[v] = {'b': round(float(b[j]), 3), 'se': round(float(se[j]), 3),
                  't': round(float(t0), 2), 'p_wild': round(cnt / B, 3)}
    out['_n'] = int(n)
    out['_states'] = int(m)
    out['_mean_y'] = round(float(d[y].mean()), 2)
    return out


res = {}
p['g_ce_w'] = winsor(p.g_ce)
p['g_re_w'] = winsor(p.g_re)
p['g_rr_w'] = winsor(p.g_rr)
fis = p[(p.fy >= 2014) & (p.fy <= 2022)]
X1 = ['runup', 'runup_sim', 'post']
for y in ['g_ce_w', 'g_re_w', 'g_rr_w', 'fd_rr', 'ce_share']:
    res['fiscal_' + y] = fe_reg(fis, y, X1)
# robustness: scheduled elections only; election-year timing; excluding Covid year 2020-21
p['runup_unsched'] = p.runup - p.runup_sched
res['rob_sched_g_ce_w'] = fe_reg(fis.assign(runup_unsched=p.runup_unsched), 'g_ce_w', ['runup_sched', 'runup_unsched', 'runup_sim', 'post'])
res['rob_elecyear_g_ce_w'] = fe_reg(fis, 'g_ce_w', ['elec', 'elec_sim', 'post'])
res['rob_nocovid_g_ce_w'] = fe_reg(fis[fis.fy != 2020], 'g_ce_w', X1)
res['rob_nocovid_g_re_w'] = fe_reg(fis[fis.fy != 2020], 'g_re_w', X1)
res['rob_raw_g_ce'] = fe_reg(fis, 'g_ce', X1)
big = fis[~fis.State.isin(['Sikkim', 'Arunachal Pradesh'])]
for y in ['ce_share', 'g_rr_w', 'fd_rr']:
    res['rob_noNEsmall_' + y] = fe_reg(big, y, X1)

# GSDP growth around elections, 2012-13 to 2021-22
gd = p[(p.fy >= 2012) & (p.fy <= 2021)]
res['gsdp_runup'] = fe_reg(gd, 'g_gsdp', ['runup', 'runup_sim', 'post', 'post_sim'])
res['gsdp_runup_nocovid'] = fe_reg(gd[~gd.fy.isin([2020, 2021])], 'g_gsdp', ['runup', 'runup_sim', 'post', 'post_sim'])

# Episode comparison in the style of the post-minus-pre test: g(t+1) - g(t-1) around election year t
ae = pd.read_csv(os.path.join(R, 'assembly_elections_fy.csv'))
gg = p.set_index(['State', 'fy']).g_gsdp
yr = p.groupby('fy').g_gsdp.mean()
rows = []
for _, r in ae.iterrows():
    a, bb = (r.State, r.fy + 1), (r.State, r.fy - 1)
    if a in gg.index and bb in gg.index and pd.notna(gg[a]) and pd.notna(gg[bb]):
        raw = gg[a] - gg[bb]
        adj = raw - (yr[r.fy + 1] - yr[r.fy - 1])
        rows.append({'State': r.State, 'fy': int(r.fy), 'sim': int(r.with_lok_sabha), 'post_minus_pre': raw, 'adj': adj})
ep = pd.DataFrame(rows)
ep.to_csv(os.path.join(R, 'episodes.csv'), index=False)


def diff_stats(e, col):
    s, n = e[e.sim == 1][col], e[e.sim == 0][col]
    d = s.mean() - n.mean()
    se = np.sqrt(s.var(ddof=1) / len(s) + n.var(ddof=1) / len(n))
    # permutation p-value
    allv, k = e[col].to_numpy(), len(s)
    cnt = 0
    for _ in range(20000):
        pi = rng.permutation(len(allv))
        cnt += abs(allv[pi[:k]].mean() - allv[pi[k:]].mean()) >= abs(d)
    return {'sim_mean': round(float(s.mean()), 2), 'nonsim_mean': round(float(n.mean()), 2), 'diff': round(float(d), 2),
            'se': round(float(se), 2), 'p_perm': round(cnt / 20000, 3), 'n_sim': int(len(s)), 'n_nonsim': int(len(n))}


res['episodes_raw'] = diff_stats(ep, 'post_minus_pre')
res['episodes_yearadj'] = diff_stats(ep, 'adj')
res['episodes_raw_pre2019'] = diff_stats(ep[ep.fy < 2019], 'post_minus_pre')
res['episodes_raw_2019'] = diff_stats(ep[ep.fy == 2019], 'post_minus_pre') if (ep[ep.fy == 2019].sim.sum() > 1) else None
# leave-one-simultaneous-episode-out range of the raw difference
loo = []
for i in ep[ep.sim == 1].index:
    e2 = ep.drop(i)
    loo.append(e2[e2.sim == 1].post_minus_pre.mean() - e2[e2.sim == 0].post_minus_pre.mean())
res['episodes_raw_loo_range'] = [round(float(min(loo)), 2), round(float(max(loo)), 2)]
json.dump(res, open(os.path.join(R, 'fiscal_cycle.json'), 'w'), indent=1)
print(json.dumps(res, indent=1))

# event-time dummies (reference: year before the election year) for the fiscal deficit, wild bootstrap
ey = ae.groupby('State').fy.apply(list).to_dict()
for k in (-2, 0, 1, 2):
    p[f'e{k:+d}'] = [int(any(fy - e == k for e in ey.get(s, []))) for s, fy in zip(p.State, p.fy)]
fd = p[(p.fy >= 2013) & (p.fy <= 2022)]
res['event_fd_rr_wild'] = fe_reg(fd, 'fd_rr', ['e-2', 'e+0', 'e+1', 'e+2'], B=1999)
res['event_ce_share_wild'] = fe_reg(fd, 'ce_share', ['e-2', 'e+0', 'e+1', 'e+2'], B=1999)
json.dump(res, open(os.path.join(R, 'fiscal_cycle.json'), 'w'), indent=1)
print(res['event_fd_rr_wild'], res['event_ce_share_wild'])
