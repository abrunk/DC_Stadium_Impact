"""
Claim: "The stadium will create 3,500 jobs and boost local economic activity"
Test: Did DC's Leisure & Hospitality sector grow beyond what comparable metros predict?

Treatment: Washington DC metro area
Controls: Comparable metros without new stadiums around 2008
Intervention: March 2008 (stadium opens - using opening date here because
              employment effects require the stadium to actually be operating)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from causalimpact import CausalImpact

# ============================================================
# 1. LOAD AND PREPARE DATA
# ============================================================

emp = pd.read_csv('data/bls_leisure_hospitality_employment.csv',
                  parse_dates=['date'], index_col='date')

print("=" * 70)
print("ANALYSIS 2: EMPLOYMENT - JOB CREATION CLAIM")
print("=" * 70)
print(f"\nData: Monthly Leisure & Hospitality employment (thousands)")
print(f"Source: BLS Current Employment Statistics (CES)")
print(f"Date range: {emp.index[0].strftime('%Y-%m')} to {emp.index[-1].strftime('%Y-%m')}")
print(f"Metros: {list(emp.columns)}")

# Control metros: those that did NOT get new major sports stadiums around 2008
# Excluding: None of these got new stadiums during our study window
control_metros = [
    'Baltimore',
    'Philadelphia',
    'Boston',
    'Pittsburgh',
    'St. Louis',
    'Richmond',
    'Nashville',
    'Columbus OH',
]

# ============================================================
# 2. PRE-TREATMENT TREND VISUALIZATION
# ============================================================

# Index to Jan 2000 = 100
emp_indexed = emp.div(emp.iloc[0]) * 100

fig, ax = plt.subplots(figsize=(14, 8))

for metro in control_metros:
    ax.plot(emp_indexed.index, emp_indexed[metro],
            color='gray', alpha=0.4, linewidth=0.8)

ax.plot(emp_indexed.index, emp_indexed['Washington DC'],
        color='#E41A1C', linewidth=2.5, label='Washington DC')
ax.plot([], [], color='gray', alpha=0.6, linewidth=0.8, label='Control metros (gray)')

events = {
    '2004-12-01': 'Deal\napproved',
    '2008-03-30': 'Stadium\nopens',
    '2020-03-01': 'COVID',
}
for date_str, label in events.items():
    event_date = pd.Timestamp(date_str)
    ax.axvline(event_date, color='gray', linestyle='--', alpha=0.5)
    ax.annotate(label, xy=(event_date, ax.get_ylim()[1] * 0.97 if 'COVID' not in label else ax.get_ylim()[1] * 0.5),
                fontsize=8, ha='center', va='top', color='gray')

ax.set_title('Metro Leisure & Hospitality Employment (Indexed: Jan 2000 = 100)', fontsize=14)
ax.set_ylabel('Employment Index (Jan 2000 = 100)')
ax.legend(loc='upper left', fontsize=10)
ax.xaxis.set_major_locator(mdates.YearLocator(2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
sns.despine()
plt.tight_layout()
plt.savefig('figures/employment_trends_indexed.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: figures/employment_trends_indexed.png")

# ============================================================
# 3. CAUSAL IMPACT - STADIUM OPENING (Mar 2008)
# ============================================================

print()
print("-" * 70)
print("CausalImpact: DC Leisure & Hospitality Employment")
print("Intervention: Stadium opening (March 2008)")
print("-" * 70)

ci_cols = ['Washington DC'] + control_metros
ci_data = emp[ci_cols].dropna()

# Pre-period: Jan 2000 through Feb 2008 (before stadium opens)
# Post-period: Mar 2008 through Dec 2019 (stop before COVID)
pre_period = ['2000-01-01', '2008-02-01']
post_period = ['2008-03-01', '2019-12-01']

ci_data_study = ci_data.loc[:'2019-12-01']

print(f"Pre-period:  Jan 2000 to Feb 2008 ({len(ci_data_study.loc[:'2008-02-01'])} months)")
print(f"Post-period: Mar 2008 to Dec 2019 ({len(ci_data_study.loc['2008-03-01':'2019-12-01'])} months)")
print(f"Control metros: {len(control_metros)}")
print()

impact = CausalImpact(ci_data_study, pre_period, post_period)
print(impact.summary())
print()
print(impact.summary(output='report'))

fig = impact.plot(figsize=(14, 10))
plt.suptitle('CausalImpact: Did Nationals Park Boost DC Leisure & Hospitality Employment?',
             fontsize=13, y=1.02)
plt.tight_layout()
plt.savefig('figures/causalimpact_employment.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: figures/causalimpact_employment.png")

# ============================================================
# 4. ROBUSTNESS: INTERVENTION AT DEAL APPROVAL (Dec 2004)
# ============================================================

print()
print("-" * 70)
print("Robustness: Intervention at deal approval (Dec 2004)")
print("-" * 70)

pre_period_alt = ['2000-01-01', '2004-11-01']
post_period_alt = ['2004-12-01', '2019-12-01']

impact_alt = CausalImpact(ci_data_study, pre_period_alt, post_period_alt)
print(impact_alt.summary())

fig = impact_alt.plot(figsize=(14, 10))
plt.suptitle('Robustness: Intervention at Deal Approval (Dec 2004) - Employment',
             fontsize=13, y=1.02)
plt.tight_layout()
plt.savefig('figures/causalimpact_employment_robustness.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: figures/causalimpact_employment_robustness.png")

# ============================================================
# 5. SUMMARY
# ============================================================

print()
print("=" * 70)
print("EMPLOYMENT SUMMARY")
print("=" * 70)
print()
for metro in ['Washington DC'] + control_metros:
    v2000 = emp.loc['2000-01-01', metro]
    v2008 = emp.loc['2008-03-01', metro]
    v2019 = emp.loc['2019-12-01', metro]
    g1 = (v2008/v2000 - 1) * 100
    g2 = (v2019/v2008 - 1) * 100
    marker = ' <-- TREATMENT' if metro == 'Washington DC' else ''
    print(f"  {metro:20s}  2000: {v2000:6.1f}K  2008: {v2008:6.1f}K ({g1:+.1f}%)  2019: {v2019:6.1f}K ({g2:+.1f}%){marker}")

print("\nAnalysis complete.")
