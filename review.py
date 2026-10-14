"""Step 4c: print the real opportunities and save review.csv (original text alongside)
so each row can be checked by eye against its message."""
import pandas as pd

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 300)

df = pd.read_csv('clean.csv')
drives = df[df['type'].isin(['job', 'internship_ppo', 'internship'])]

print(len(drives), 'opportunities')
print(drives[['msg_id', 'date', 'company', 'type', 'ctc_lpa_min', 'ctc_lpa_max',
              'fixed_ctc_lpa', 'stipend_per_month', 'bond_years']].to_string())

ann = pd.read_csv('announcements.csv')
review = drives.merge(ann[['msg_id', 'text']], on='msg_id')
review.to_csv('review.csv', index=False)
print('Saved review.csv')
