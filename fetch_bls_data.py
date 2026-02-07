"""
Fetch BLS metro-level Leisure & Hospitality employment data.
BLS API v2 (public, no key required - limited to 25 series / 20 years per request)
"""

import requests
import json
import pandas as pd
import time

BLS_API_URL = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'

# Metro areas and their BLS state+area codes for CES series
# Series format: SMU + {state FIPS 2-digit} + {MSA code 5-digit} + {industry} + {datatype}
# Industry 70000000 = Leisure & Hospitality, Datatype 01 = All Employees (thousands)
metros = {
    'Washington DC':   {'state': '11', 'msa': '47900'},
    'Baltimore':       {'state': '24', 'msa': '12580'},
    'Philadelphia':    {'state': '42', 'msa': '37980'},
    'Boston':          {'state': '25', 'msa': '14460'},
    'Pittsburgh':      {'state': '42', 'msa': '38300'},
    'St. Louis':       {'state': '29', 'msa': '41180'},
    'Charlotte':       {'state': '37', 'msa': '16740'},
    'Richmond':        {'state': '51', 'msa': '40060'},
    'Nashville':       {'state': '47', 'msa': '34980'},
    'Columbus OH':     {'state': '39', 'msa': '18140'},
}

def build_series_id(state, msa, industry='70000000', datatype='01'):
    return f'SMU{state}{msa}{industry}{datatype}'

def fetch_bls_series(series_ids, start_year, end_year):
    """Fetch data from BLS API. Max 25 series per request."""
    payload = json.dumps({
        'seriesid': series_ids,
        'startyear': str(start_year),
        'endyear': str(end_year),
    })
    headers = {'Content-type': 'application/json'}
    r = requests.post(BLS_API_URL, data=payload, headers=headers, timeout=60)
    return r.json()

# Build series IDs
series_map = {}
for metro_name, codes in metros.items():
    sid = build_series_id(codes['state'], codes['msa'])
    series_map[sid] = metro_name
    print(f"  {metro_name}: {sid}")

# Fetch in two batches (2000-2012, 2013-2024) due to 20-year limit
all_data = {}

for start, end in [(2000, 2012), (2013, 2024)]:
    print(f"\nFetching {start}-{end}...")
    result = fetch_bls_series(list(series_map.keys()), start, end)

    if result.get('status') != 'REQUEST_SUCCEEDED':
        print(f"  Error: {result.get('message', 'unknown')}")
        # Try each series individually to find which ones work
        for sid, name in series_map.items():
            result2 = fetch_bls_series([sid], start, end)
            if result2.get('status') == 'REQUEST_SUCCEEDED':
                series_data = result2['Results']['series'][0]['data']
                if series_data:
                    print(f"  {name}: {len(series_data)} records")
                    if name not in all_data:
                        all_data[name] = []
                    all_data[name].extend(series_data)
            else:
                print(f"  {name}: FAILED - {sid}")
            time.sleep(1)  # Rate limit
    else:
        for series in result['Results']['series']:
            sid = series['seriesID']
            name = series_map.get(sid, sid)
            records = series['data']
            print(f"  {name}: {len(records)} records")
            if name not in all_data:
                all_data[name] = []
            all_data[name].extend(records)
    time.sleep(2)  # Rate limit between batches

# Convert to DataFrame
print("\nProcessing...")
frames = {}
for metro_name, records in all_data.items():
    rows = []
    for r in records:
        year = int(r['year'])
        month = int(r['period'].replace('M', ''))
        if month == 13:  # Annual average, skip
            continue
        date = pd.Timestamp(year=year, month=month, day=1)
        value = float(r['value'])
        rows.append({'date': date, metro_name: value})
    if rows:
        df = pd.DataFrame(rows).set_index('date').sort_index()
        frames[metro_name] = df

if frames:
    employment = pd.concat(frames.values(), axis=1).sort_index()
    employment.to_csv('data/bls_leisure_hospitality_employment.csv')
    print(f"\nSaved: data/bls_leisure_hospitality_employment.csv")
    print(f"Shape: {employment.shape}")
    print(f"Date range: {employment.index[0]} to {employment.index[-1]}")
    print(f"\nMetros with data:")
    for col in employment.columns:
        valid = employment[col].notna().sum()
        print(f"  {col}: {valid} months")
else:
    print("\nNo data retrieved!")
