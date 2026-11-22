"""Sensitivity bounds on the economic gains from synchronising elections (Section 7).

All quantities are per five-year term in per cent of one year's GDP unless stated.
Parameters are drawn uniformly from the ranges in Table 6 of the paper (assumptions, not data).
Inputs from the calendar analysis: off-cycle GDP share voting per term and windows per term.
Output: ../results/calibration.json
"""
import numpy as np, json, os
B = os.path.join(os.path.dirname(__file__), '..')
cal = json.load(open(os.path.join(B, 'results', 'calendar.json')))
rng = np.random.default_rng(20261122)
N = 200_000
U = lambda a, b: rng.uniform(a, b, N)

m_off = cal['gdp_share_voting_off_cycle_per_term']      # 0.92
K = cal['windows_per_term']                              # 11 windows per term, incl. the Lok Sabha window
GDP = 300.0                                              # Rs lakh crore, FY2024 (implied by HLC: 1.5% = 4.5)

# 1 administrative cost: ECI share of the 2024 total (10-15% of Rs 1.35 lakh crore)
adm_ls = U(0.10, 0.15) * 1.35 / GDP * 100                # % of GDP for one Lok Sabha election
f_adm = U(0.2, 0.6)                                      # share of assembly administrative cost that is fixed per window
g_admin = adm_ls * m_off * f_adm
# 2 campaign spending (non-ECI part), resource cost share and share saved by merging
camp_ls = (1.35 / GDP * 100) * (1 - U(0.10, 0.15))
rho = U(0.5, 1.0)                                        # assembly campaigns per term relative to one Lok Sabha campaign
s_c, r_c = U(0.2, 0.6), U(0.1, 0.5)
g_campaign = camp_ls * rho * s_c * r_c
# 3 Model Code of Conduct: output lost per GDP-weighted day, as a fraction kappa of daily GDP
kappa = U(0.0005, 0.01)
L_S = U(35, 60)
g_mcc = m_off * L_S * kappa / 365 * 100
# 4 central attention diverted during off-cycle windows (theta = share of an MCC day's cost)
theta = U(0.0, 0.2)
g_attn = (K - 1) * L_S * theta * kappa / 365 * 100
# 5 political budget cycle: each state still votes once per term under any calendar, so the
# election-year deficit rise (Section 6.2) is not removed by synchronisation (baseline = 0).
# Scenario in Section 7.4: synchronisation removes the whole rise and all of it is waste.
g_pbc = np.zeros(N)
RR_GDP = 35.13 / GDP                                     # state revenue receipts / GDP (28 states, 2022-23)
pbc_upper = 0.0413 * RR_GDP * 100                        # election-year deficit rise, % of GDP per term
# cost of synchronisation: larger one-off uncertainty shock when all governments are at stake
rho_e, lam = U(0.1, 0.5), U(0.25, 0.75)                 # correlation of shocks; state stake relative to national
dI = 0.074 * 2 * rho_e * lam * m_off                     # Section 4.2: 2 rho u_N u_S m_off, scaled by the 7.4% national effect
Ip, loss = U(0.10, 0.20), U(0.1, 0.3)                    # private investment / GDP; share of deferral that is lost
c_unc = dI * Ip * loss * 100

G_sync = g_admin + g_campaign + g_mcc + g_attn + g_pbc - c_unc
# two-cycle calendar: Lok Sabha window + one mid-term bundle holding a share q of states
q = 0.5
share_windows = (K - 2) / (K - 1)
# baseline (Section 4.2): the extra uncertainty comes from the covariance of national and state
# shocks and is linear in the share of states synchronised, so the bundle with (1 - q) of states
# bears (1 - q) of it; Section 7.3 uses (1 - q)^eta with eta = 2, 3 for a convex cost
G_two = (share_windows * (g_admin + g_campaign + g_attn + g_pbc) + (1 - q) * g_mcc - (1 - q) * c_unc)
# Lok Sabha duration: polling span cut from 44 to 27 days (7 phases at the 2014 average gap)
g_dur = (44 - 27) * kappa / 365 * 100

pct = lambda x: {k: round(float(v), 4) for k, v in zip(['p5', 'p50', 'p95', 'max'], [*np.percentile(x, [5, 50, 95]), x.max()])}
res = {
    'inputs': {'m_off': m_off, 'K': K, 'GDP_lakh_crore': GDP},
    'components_per_term_pct_gdp': {k: pct(v) for k, v in
                                    {'admin': g_admin, 'campaign': g_campaign, 'mcc': g_mcc, 'attention': g_attn,
                                     'pbc': g_pbc, 'uncertainty_cost': c_unc}.items()},
    'G_sync_per_term': pct(G_sync), 'G_sync_per_year': pct(G_sync / 5),
    'G_two_per_term': pct(G_two), 'G_two_per_year': pct(G_two / 5),
    'share_two_of_sync_median': round(float(np.median(G_two[G_sync > 0] / G_sync[G_sync > 0])), 3),
    'prob_G_sync_negative': round(float((G_sync < 0).mean()), 3),
    'prob_G_two_gt_G_sync': round(float((G_two > G_sync).mean()), 3),
    'claimed_hlc_pct_gdp': 1.5,
    'ratio_claim_to_p95_sync_per_term': round(1.5 / float(np.percentile(G_sync, 95)), 1),
    'break_even_accountability_rs_crore_per_year_p50_p95': [round(float(np.percentile(G_sync / 5, q_)) / 100 * GDP * 1e5, 0) for q_ in (50, 95)],
    'duration_saving_per_ls_pct_gdp': pct(g_dur),
    'pbc_upper_per_term_pct_gdp': round(float(pbc_upper), 3),
    'G_sync_with_pbc_removed_per_term': pct(G_sync + pbc_upper),
    'horizon_gain_needed_pct_gdp_per_year_for_claim': round(float((1.5 - np.median(G_sync)) / 5), 3),
    'accountability_break_even_pct_state_spending': {
        'dpi_0.16_p50': round(float(np.percentile(G_sync / 5, 50) / 100 * GDP / 42.44 / 0.16 * 100), 2),
        'dpi_0.16_p95': round(float(np.percentile(G_sync / 5, 95) / 100 * GDP / 42.44 / 0.16 * 100), 2),
        'dpi_0.21_p50': round(float(np.percentile(G_sync / 5, 50) / 100 * GDP / 42.44 / 0.21 * 100), 2),
        'dpi_0.21_p95': round(float(np.percentile(G_sync / 5, 95) / 100 * GDP / 42.44 / 0.21 * 100), 2)},
}
json.dump(res, open(os.path.join(B, 'results', 'calibration.json'), 'w'), indent=1)
print(json.dumps(res, indent=1))


# ---------------------------------------------------------------------------------------------
# Robustness of the calibration (Section 7.3): alternative distributions, correlated parameters,
# alternative curvature of the uncertainty cost, parameter importance and break-even values.
# ---------------------------------------------------------------------------------------------
from scipy import stats


def draw(kind, lo, hi, z=None):
    """Draw N values on [lo, hi]. kind: 'u' uniform, 'pert' PERT (mode at midpoint), 'log' log-uniform.
    z: optional standard-normal draws (for a Gaussian copula)."""
    u = stats.norm.cdf(z) if z is not None else rng.uniform(0, 1, N)
    if kind == 'u':
        return lo + (hi - lo) * u
    if kind == 'log':
        return np.exp(np.log(lo) + (np.log(hi) - np.log(lo)) * u)
    if kind == 'pert':
        a_, b_ = 3.0, 3.0  # symmetric PERT = Beta(3,3)
        return lo + (hi - lo) * stats.beta.ppf(u, a_, b_)


def simulate(kind='u', corr=0.0, eta=1.0):
    Z = rng.standard_normal((N, 6))
    if corr:
        # copula: kappa, theta, L_S share one factor; rho_c, s_c, r_c share another
        f1, f2 = rng.standard_normal(N), rng.standard_normal(N)
        Z[:, 0:3] = np.sqrt(corr) * f1[:, None] + np.sqrt(1 - corr) * Z[:, 0:3]
        Z[:, 3:6] = np.sqrt(corr) * f2[:, None] + np.sqrt(1 - corr) * Z[:, 3:6]
    kk = 'log' if kind == 'log' else kind
    kap = draw(kk, 0.0005, 0.01, Z[:, 0]); th = draw('u' if kind == 'log' else kind, 0.0, 0.2, Z[:, 1]); LS = draw(kind if kind != 'log' else 'u', 35, 60, Z[:, 2])
    rh = draw(kind if kind != 'log' else 'u', 0.5, 1.0, Z[:, 3]); sc = draw(kind if kind != 'log' else 'u', 0.2, 0.6, Z[:, 4]); rc = draw(kind if kind != 'log' else 'u', 0.1, 0.5, Z[:, 5])
    adm = draw('u', 0.10, 0.15) * 1.35 / GDP * 100 * m_off * draw('u', 0.2, 0.6)
    camp = (1.35 / GDP * 100) * (1 - draw('u', 0.10, 0.15)) * rh * sc * rc
    mcc = m_off * LS * kap / 365 * 100
    att = (K - 1) * LS * th * kap / 365 * 100
    pbc = np.zeros(N)
    unc = 0.074 * 2 * draw('u', 0.1, 0.5) * draw('u', 0.25, 0.75) * m_off * draw('u', 0.10, 0.20) * draw('u', 0.1, 0.3) * 100
    Gs = adm + camp + mcc + att + pbc - unc
    sw = (K - 2) / (K - 1)
    Gt = sw * (adm + camp + att + pbc) + (1 - q) * mcc - (1 - q) ** eta * unc
    return Gs, Gt, dict(kappa=kap, theta=th, L_S=LS, rho_campaign=rh, share_saved=sc, resource_share=rc)


rob = {}
for name, kw in {'uniform': {}, 'pert': {'kind': 'pert'}, 'loguniform_kappa': {'kind': 'log'},
                 'correlated_0.5': {'corr': 0.5}, 'eta_2': {'eta': 2.0}, 'eta_3': {'eta': 3.0}}.items():
    Gs, Gt, prm = simulate(**kw)
    rob[name] = {'sync_p50': round(float(np.median(Gs)), 3), 'sync_p95': round(float(np.percentile(Gs, 95)), 3),
                 'two_p50': round(float(np.median(Gt)), 3),
                 'share_two_of_sync_p50': round(float(np.median(Gt[Gs > 0] / Gs[Gs > 0])), 3),
                 'prob_two_ge_sync': round(float((Gt >= Gs).mean()), 3)}
    if name == 'uniform':
        rob['spearman_with_G_sync'] = {k: round(float(stats.spearmanr(v, Gs)[0]), 3) for k, v in prm.items()}
res['robustness'] = rob

# break-even: kappa (share of a day's output lost per MCC day) needed for the per-term gain to equal
# each interpretation of the claim, with all other parameters at their median
med = lambda a, b: (a + b) / 2
A0 = (med(0.10, 0.15) * 1.35 / GDP * 100 * m_off * med(0.2, 0.6) + (1.35 / GDP * 100) * (1 - med(0.10, 0.15)) * med(0.5, 1.0) * med(0.2, 0.6) * med(0.1, 0.5)
      - 0.074 * 2 * med(0.1, 0.5) * med(0.25, 0.75) * m_off * med(0.10, 0.20) * med(0.1, 0.3) * 100)
Bk = (m_off * med(35, 60) + (K - 1) * med(35, 60) * med(0, 0.2)) / 365 * 100
res['break_even_kappa_pct_daily_output'] = {
    'one_off_1.5pct_per_term': round(float((1.5 - A0) / Bk * 100), 1),
    'level_shift_1.5pct_every_year': round(float((7.5 - A0) / Bk * 100), 1)}
# common basis: the claim versus the calibrated gain, both in % of one year's GDP per five-year term
res['common_basis'] = {
    'claim_one_off_per_term': 1.5, 'claim_permanent_level_per_term': 7.5,
    'calib_sync_p50': res['G_sync_per_term']['p50'], 'calib_sync_p95': res['G_sync_per_term']['p95'],
    'ratio_one_off_to_p50': round(1.5 / res['G_sync_per_term']['p50'], 1),
    'ratio_one_off_to_p95': round(1.5 / res['G_sync_per_term']['p95'], 1),
    'ratio_level_to_p95': round(7.5 / res['G_sync_per_term']['p95'], 1)}
json.dump(res, open(os.path.join(B, 'results', 'calibration.json'), 'w'), indent=1)
print(json.dumps({k: res[k] for k in ['robustness', 'break_even_kappa_pct_daily_output', 'common_basis']}, indent=1))


# ---------------------------------------------------------------------------------------------
# Scenario tables (Sections 7.3 and 7.5): fixed values of kappa; share of the election-year
# deficit rise treated as avoidable waste.
# ---------------------------------------------------------------------------------------------
base_nokappa = g_admin + g_campaign - c_unc                       # components that do not depend on kappa
kap_per = (m_off * L_S + (K - 1) * L_S * theta) / 365 * 100       # gain per unit of kappa
two_nokappa = share_windows * (g_admin + g_campaign) - (1 - q) * c_unc
two_kap_per = (share_windows * (K - 1) * L_S * theta + (1 - q) * m_off * L_S) / 365 * 100
sc = {}
for lab, kv in [('zero', 0.0), ('very_low_0.05pct', 0.0005), ('high_1pct', 0.01)]:
    gs, gt = base_nokappa + kv * kap_per, two_nokappa + kv * two_kap_per
    sc[lab] = {'sync_p50': round(float(np.median(gs)), 3), 'sync_p95': round(float(np.percentile(gs, 95)), 3),
               'prob_sync_negative': round(float((gs < 0).mean()), 3), 'two_p50': round(float(np.median(gt)), 3)}
sc['baseline_range'] = {'sync_p50': res['G_sync_per_term']['p50'], 'sync_p95': res['G_sync_per_term']['p95'],
                        'prob_sync_negative': res['prob_G_sync_negative'], 'two_p50': res['G_two_per_term']['p50']}
res['kappa_scenarios'] = sc
ws = {}
for w_ in (0.0, 0.25, 0.5, 1.0):
    g_ = G_sync + w_ * pbc_upper
    ws[str(w_)] = {'added': round(float(w_ * pbc_upper), 3), 'sync_p50': round(float(np.median(g_)), 3),
                   'sync_p95': round(float(np.percentile(g_, 95)), 3)}
res['waste_scenarios'] = ws
json.dump(res, open(os.path.join(B, 'results', 'calibration.json'), 'w'), indent=1)
print(json.dumps({'kappa': sc, 'waste': ws}, indent=1))
