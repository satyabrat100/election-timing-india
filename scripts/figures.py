"""Figures 2 and 3."""
import pandas as pd, numpy as np, os, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B = os.path.join(os.path.dirname(__file__), '..')
ep = pd.read_csv(os.path.join(B, 'results', 'episodes.csv'))

fig, ax = plt.subplots(figsize=(7, 3.4))
for sim, col, lab in [(0, '#999999', 'Not with Lok Sabha'), (1, '#C44E52', 'With Lok Sabha')]:
    e = ep[ep.sim == sim]
    jitter = (np.random.default_rng(1).uniform(-0.15, 0.15, len(e)))
    ax.scatter(e.fy + jitter, e.post_minus_pre, s=22, color=col, label=lab, alpha=0.85)
ax.axhline(0, color='black', lw=0.6)
ax.axvspan(2018.6, 2019.4, color='#F2E6C8', zorder=0)
ax.text(2019, 13, 'post year =\n2020-21 (Covid)', ha='center', fontsize=7)
ax.set_xlabel('Fiscal year of the assembly election (results)')
ax.set_ylabel('Growth after minus growth before (pp)')
ax.legend(frameon=False, fontsize=8, loc='lower left')
for s in ('top', 'right'):
    ax.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(B, 'figures', 'fig2_episodes.png'), dpi=300)

# Figure 3: distribution of gains (re-draw using the calibration script's exact code)
ns = {'__file__': os.path.join(B, 'scripts', 'calibrate.py')}
src = open(ns['__file__']).read().split('pct = lambda')[0]
exec(src, ns)
fig, ax = plt.subplots(figsize=(7, 3.4))
bins = np.linspace(-0.2, 0.6, 81)
ax.hist(ns['G_sync'], bins=bins, alpha=0.6, color='#4C72B0', label='Full synchronisation', density=True)
ax.hist(ns['G_two'], bins=bins, alpha=0.6, color='#DD8452', label='Two-cycle calendar', density=True)
ax.set_xlabel('Gain per five-year term (% of one year\'s GDP)')
ax.set_ylabel('Density')
ax.legend(frameon=False, fontsize=8)
ax.text(0.58, ax.get_ylim()[1] * 0.85, 'HLC claim: 1.5%\n(off the scale)', ha='right', fontsize=7)
for s in ('top', 'right'):
    ax.spines[s].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(B, 'figures', 'fig3_gains.png'), dpi=300)
print('figures done')
