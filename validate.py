"""Step 4a: automatic check of the AI's numbers.

For every number the AI extracted, check that it actually appears in the
original message (in any common Indian format). Rows that fail are printed
for a manual check.
"""
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 250)

ann = pd.read_csv('announcements.csv')
out = pd.read_csv('extracted.csv')

# put the original message next to each AI answer (matched on the permanent ID)
df = out.merge(ann[['msg_id', 'text']], on='msg_id')

print(df['type'].value_counts(), '\n')


def appears(value, text, lakh=True):
    if pd.isna(value):
        return True
    t = text.lower().replace(',', '')
    v = float(value)
    options = [f'{v:g}']
    if v >= 1000:
        options.append(f'{v/1000:g}k')                  # 15000 -> 15k
        if v >= 100000:
            options.append(f'{v/100000:g}l')            # 100000 -> 1l / 1 lakh
            options.append(f'{v/100000:g} la')
    elif lakh:
        options.append(f'{v*100000:g}')                 # 4 LPA -> 400000
    return any(o in t for o in options)


# stipends are always rupees, so the lakh conversion is switched off for them
NUM_COLS = ['ctc_lpa_min', 'ctc_lpa_max', 'fixed_ctc_lpa', 'stipend_per_month']

problems = []
for _, row in df.iterrows():
    bad = [c for c in NUM_COLS
           if not appears(row[c], row['text'], lakh=(c != 'stipend_per_month'))]
    if bad:
        problems.append({'msg_id': row['msg_id'], 'company': row['company'],
                         'check_these': ', '.join(bad),
                         **{c: row[c] for c in bad}})

print('Rows to check by hand:', len(problems))
print(pd.DataFrame(problems).to_string())
