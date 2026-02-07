"""
Claim: "The stadium will catalyze neighborhood revitalization"
Test: Did Navy Yard property values outpace comparable gentrifying DC neighborhoods?

Treatment: Zip codes 20003 (Capitol Hill / Navy Yard) and 20024 (SW Waterfront)
Controls: Other gentrifying DC neighborhoods without a stadium
Intervention: December 2004 (DC Council approves stadium deal, 7-6 vote)

Note: We define the intervention at the APPROVAL date, not the 2008 opening,
because the economic signal to developers and investors began immediately.
Land purchases and speculation in the Navy Yard area started as soon as the
deal was public.
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

df = pd.read_csv('data/zhvi_dc_zips.csv', dtype={'RegionName': str})

# Identify date columns (they start with '20')
date_cols = [c for c in df.columns if c.startswith('20') and '-' in c]
dates = pd.to_datetime(date_cols)

# Define zip code groups
# Treatment: Stadium-adjacent zip codes
treatment_zips = {
    '20003': 'Navy Yard / Capitol Hill South',
    '20024': 'SW Waterfront / Buzzard Point'
}

# Controls: Other DC neighborhoods undergoing gentrification during the same
# period, but WITHOUT a stadium. These capture the broader DC revitalization
# trend that would have affected the Navy Yard area regardless of the stadium.
control_zips = {
    '20001': 'Shaw / Logan Circle / NoMa',
    '20002': 'H Street NE / Trinidad',
    '20009': 'Adams Morgan / U Street',
    '20010': 'Columbia Heights',
    '20011': 'Petworth / Brightwood',
    '20017': 'Brookland / Michigan Park',
    '20018': 'Woodridge / Fort Totten',
}

# Broader context zips (already-established neighborhoods)
context_zips = {
    '20005': 'Downtown / Chinatown',
    '20037': 'West End / Foggy Bottom',
}

# Extract time series for each zip
def get_zip_series(zip_code):
    row = df[df['RegionName'] == zip_code]
    if len(row) == 0:
        return None
    values = row[date_cols].values.flatten().astype(float)
    return pd.Series(values, index=dates, name=zip_code)

# Build the dataset
all_zips = {**treatment_zips, **control_zips}
series_dict = {}
for z in all_zips:
    s = get_zip_series(z)
    if s is not None:
        series_dict[z] = s

data = pd.DataFrame(series_dict)
data.index.name = 'date'

# ============================================================
# 2. PRE-TREATMENT TREND VISUALIZATION
# ============================================================

print("=" * 70)
print("ANALYSIS 1: PROPERTY VALUES - NEIGHBORHOOD REVITALIZATION CLAIM")
print("=" * 70)
print()

# Index to Jan 2000 = 100 for comparison
data_indexed = data.div(data.iloc[0]) * 100

fig, ax = plt.subplots(figsize=(14, 8))

# Plot control zips in gray
for z in control_zips:
    if z in data_indexed.columns:
        ax.plot(data_indexed.index, data_indexed[z],
                color='gray', alpha=0.4, linewidth=0.8,
                label=f'{z} ({control_zips[z]})' if z == list(control_zips.keys())[0] else '_')

# Plot treatment zips highlighted
colors = {'20003': '#E41A1C', '20024': '#377EB8'}
for z in treatment_zips:
    if z in data_indexed.columns:
        ax.plot(data_indexed.index, data_indexed[z],
                color=colors[z], linewidth=2.5,
                label=f'{z} ({treatment_zips[z]})')

# Mark key events
events = {
    '2004-12-01': 'DC Council\napproves deal',
    '2006-03-01': 'Construction\nbegins',
    '2008-03-30': 'Stadium\nopens',
}
for date_str, label in events.items():
    event_date = pd.Timestamp(date_str)
    ax.axvline(event_date, color='gray', linestyle='--', alpha=0.5)
    ax.annotate(label, xy=(event_date, ax.get_ylim()[1] * 0.95),
                fontsize=8, ha='center', va='top', color='gray')

# Add a gray label for control group
ax.plot([], [], color='gray', alpha=0.6, linewidth=0.8, label='Control neighborhoods (gray)')

ax.set_title('DC Neighborhood Home Values (Indexed: Jan 2000 = 100)', fontsize=14)
ax.set_ylabel('Home Value Index (Jan 2000 = 100)')
ax.set_xlabel('')
ax.legend(loc='upper left', fontsize=9)
ax.xaxis.set_major_locator(mdates.YearLocator(2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
sns.despine()
plt.tight_layout()
plt.savefig('figures/property_trends_indexed.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved: figures/property_trends_indexed.png")

# ============================================================
# 3. CAUSAL IMPACT ANALYSIS - 20003 (Navy Yard / Capitol Hill)
# ============================================================

print()
print("-" * 70)
print("CausalImpact: Zip 20003 (Navy Yard / Capitol Hill South)")
print("-" * 70)

# Build the CausalImpact input: first column = treatment, rest = controls
ci_cols_20003 = ['20003'] + list(control_zips.keys())
ci_data_20003 = data[ci_cols_20003].dropna()

# Define periods
# Pre-period: Jan 2000 through Nov 2004 (before Dec 2004 council vote)
# Post-period: Dec 2004 through Dec 2019 (stop before COVID)
pre_start = '2000-01-31'
pre_end = '2004-11-30'
post_start = '2004-12-31'
post_end = '2019-12-31'

# Filter to study period
ci_data_20003 = ci_data_20003.loc[:post_end]

pre_period = [pre_start, pre_end]
post_period = [post_start, post_end]

print(f"Pre-period:  {pre_start} to {pre_end} ({len(ci_data_20003.loc[:pre_end])} months)")
print(f"Post-period: {post_start} to {post_end} ({len(ci_data_20003.loc[post_start:post_end])} months)")
print(f"Control neighborhoods: {len(control_zips)}")
print()

impact_20003 = CausalImpact(ci_data_20003, pre_period, post_period)
print(impact_20003.summary())
print()
print(impact_20003.summary(output='report'))

# Save the CausalImpact plot
fig = impact_20003.plot(figsize=(14, 10))
plt.suptitle('CausalImpact: Did the Stadium Boost Navy Yard (20003) Property Values?',
             fontsize=13, y=1.02)
plt.tight_layout()
plt.savefig('figures/causalimpact_20003.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: figures/causalimpact_20003.png")

# ============================================================
# 4. CAUSAL IMPACT ANALYSIS - 20024 (SW Waterfront)
# ============================================================

print()
print("-" * 70)
print("CausalImpact: Zip 20024 (SW Waterfront / Buzzard Point)")
print("-" * 70)

ci_cols_20024 = ['20024'] + list(control_zips.keys())
ci_data_20024 = data[ci_cols_20024].dropna()
ci_data_20024 = ci_data_20024.loc[:post_end]

impact_20024 = CausalImpact(ci_data_20024, pre_period, post_period)
print(impact_20024.summary())
print()
print(impact_20024.summary(output='report'))

fig = impact_20024.plot(figsize=(14, 10))
plt.suptitle('CausalImpact: Did the Stadium Boost SW Waterfront (20024) Property Values?',
             fontsize=13, y=1.02)
plt.tight_layout()
plt.savefig('figures/causalimpact_20024.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: figures/causalimpact_20024.png")

# ============================================================
# 5. ROBUSTNESS: INTERVENTION AT STADIUM OPENING (Mar 2008)
# ============================================================

print()
print("-" * 70)
print("Robustness Check: Intervention at stadium OPENING (March 2008)")
print("-" * 70)

pre_end_alt = '2008-02-29'
post_start_alt = '2008-03-31'

ci_data_robust = data[ci_cols_20003].dropna().loc[:post_end]

impact_robust = CausalImpact(ci_data_robust,
                              [pre_start, pre_end_alt],
                              [post_start_alt, post_end])
print(impact_robust.summary())

fig = impact_robust.plot(figsize=(14, 10))
plt.suptitle('Robustness: Intervention at Stadium Opening (Mar 2008) - Zip 20003',
             fontsize=13, y=1.02)
plt.tight_layout()
plt.savefig('figures/causalimpact_20003_robustness_opening.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: figures/causalimpact_20003_robustness_opening.png")

# ============================================================
# 6. SUMMARY STATISTICS
# ============================================================

print()
print("=" * 70)
print("SUMMARY: PROPERTY VALUE CHANGES BY NEIGHBORHOOD")
print("=" * 70)
print()

summary_dates = {
    'Jan 2000': '2000-01-31',
    'Dec 2004 (deal approved)': '2004-12-31',
    'Mar 2008 (stadium opens)': '2008-03-31',
    'Dec 2019 (pre-COVID)': '2019-12-31',
}

print(f"{'Zip':>6} {'Neighborhood':<30} ", end='')
for label in summary_dates:
    print(f"{label:>25}", end='')
print()
print("-" * 120)

for z_dict in [treatment_zips, control_zips]:
    for z, name in z_dict.items():
        if z in data.columns:
            print(f"{z:>6} {name:<30} ", end='')
            for label, d in summary_dates.items():
                val = data.loc[d, z] if d in data.index else np.nan
                if pd.notna(val):
                    print(f"{'$' + f'{val:,.0f}':>25}", end='')
                else:
                    print(f"{'N/A':>25}", end='')
            print()
    if z_dict == treatment_zips:
        print("-" * 120)

print()
print("Analysis complete. See figures/ for all plots.")
