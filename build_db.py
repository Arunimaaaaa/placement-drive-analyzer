"""Step 5: load the cleaned data into a SQLite database.

Input : clean.csv
Output: placements.db with two tables
  - announcements : one row per announcement (no message text, only extracted fields)
  - companies     : one row per company, built from all its posts
"""
import sqlite3
import pandas as pd

df = pd.read_csv('clean.csv')

announcements = df[['msg_id', 'date', 'company', 'role', 'type',
                    'ctc_lpa_min', 'ctc_lpa_max', 'fixed_ctc_lpa',
                    'stipend_per_month', 'bond_years',
                    'eligible_branches', 'min_criteria', 'location', 'deadline']]

companies = (df.dropna(subset=['company'])
               .query("company != 'Multiple companies'")
               .groupby('company')
               .agg(total_posts=('msg_id', 'count'),
                    first_post=('date', 'min'),
                    last_post=('date', 'max'))
               .reset_index())

con = sqlite3.connect('placements.db')
announcements.to_sql('announcements', con, if_exists='replace', index=False)
companies.to_sql('companies', con, if_exists='replace', index=False)
con.close()

print('placements.db: announcements =', len(announcements), 'rows, companies =', len(companies), 'rows')
