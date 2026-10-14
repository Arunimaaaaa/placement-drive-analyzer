"""Step 4b: apply the fixes found during validation and manual review.

Input : extracted.csv   (raw AI output, left untouched)
Output: clean.csv       (corrected, company names standardised)

Every change is written down here with a reason, so the before/after is auditable.
"""
import pandas as pd

df = pd.read_csv('extracted.csv')
ann = pd.read_csv('announcements.csv')

# ---- 1. Standardise company names (the AI wrote the same company several ways) ----
ALIASES = {
    'Nowvertical': 'NowVertical',
    'TATA Group': 'Tata Group',
    'CoreStyl AI Pvt. Ltd.': 'CoreStyl AI',
    'CoreStyl AI Pvt. Ltd': 'CoreStyl AI',
    'Carwale': 'CarWale',
    'Capgemini / EduBridge': 'Capgemini',
    'Protco Technologies Pvt. Ltd.': 'Protco Technologies',
    'Protoco': 'Protco Technologies',
    'Newgen Software Technologies Limited': 'Newgen',
    'Selec Controls': 'Selec Control',
    'Hexaware Technologies': 'Hexaware',
    'BlackCarrot Ventures Private Limited': 'BlackCarrot Ventures',
    'FOX Solutions Pvt. Ltd.': 'FOX Solutions',
    'Codemines Solutions Pvt Ltd': 'Codemines',
    'Codemine': 'Codemines',
    'Intellipaaat Software Solutions Pvt. Ltd.': 'Intellipaat',
    'Quantum Phinance Pvt. Ltd': 'Quantum Phinance',
    'Siemens Limited': 'Siemens',
}
df['company_raw'] = df['company']
df['company'] = df['company'].replace(ALIASES)

# ---- 2. Rule: the AI invented "no bond" (0) for messages that never mention a bond ----
df = df.merge(ann[['msg_id', 'text']], on='msg_id', how='left')
invented_bond = (df['bond_years'] == 0) & ~df['text'].str.contains('bond', case=False)
print('Rule: bond_years 0 -> empty for', invented_bond.sum(),
      'rows whose message never mentions a bond')
df.loc[invented_bond, 'bond_years'] = None
df = df.drop(columns=['text'])

# ---- 3. Row-level fixes from the manual review: (msg_id, column, correct value, reason) ----
CORRECTIONS = [
    # wrong values
    (706, 'stipend_per_month', 10000, 'message says 10,000-15,000; we record the guaranteed lower end'),
    (1193, 'stipend_per_month', 40000, 'AI took the Mechanical track (75,000); IT-relevant Digital & AI track is 40,000'),
    (1410, 'company', 'Unnamed core-engineering firm (Mahape)', 'company name is not in the message'),
    # wrong type
    (1193, 'type', 'internship_ppo', 'Destination Dr. Reddy\'s is an internship hiring drive with PPO chance, not a contest'),
    (1246, 'type', 'internship', 'JP Morgan message never mentions a PPO'),
    (1475, 'type', 'competition', 'Nykaa creator campaign on Unstop, not a direct internship'),
    (720, 'type', 'notice', 'TCS registration reminder pointing to a circular; the drive details are msg 1012'),
    (952, 'type', 'notice', 'just a LinkedIn link about TCS NQT, not a drive'),
    # duplicates (same drive posted again)
    (716, 'type', 'duplicate', 'repost of the CoreStyl AI internship in msg 706'),
    (1285, 'type', 'duplicate', 'ExcelR drive-day logistics; the drive itself is msg 1273'),
    (1299, 'type', 'duplicate', 'repost of Destination Dr. Reddy\'s (msg 1193)'),
    (1300, 'type', 'duplicate', 'repost of Destination Dr. Reddy\'s (msg 1193)'),
]

for msg_id, col, value, reason in CORRECTIONS:
    df.loc[df['msg_id'] == msg_id, col] = value
    print('Fixed', msg_id, col, '->', value, '|', reason)

df.to_csv('clean.csv', index=False)
print('Saved clean.csv with', len(CORRECTIONS), 'corrections +', invented_bond.sum(), 'rule fixes')
