"""Run every query in queries.sql against placements.db and print the results."""
import re
import sqlite3
import pandas as pd

pd.set_option('display.width', 250)
pd.set_option('display.max_colwidth', 80)

con = sqlite3.connect('placements.db')
blocks = re.split(r'^-- Q(?=\d)', open('queries.sql', encoding='utf-8').read(), flags=re.M)[1:]

for block in blocks:
    title, sql = block.split('\n', 1)
    print('\n=== Q' + title.strip())
    print(pd.read_sql_query(sql, con).to_string(index=False))

con.close()
