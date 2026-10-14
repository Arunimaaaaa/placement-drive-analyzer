"""Step 1-2: parse the WhatsApp export and keep only company announcements.

Input : chat.txt            (raw export, private, never committed)
Output: announcements.csv   (filtered + anonymised announcements)
"""
import re
import pandas as pd

# ---- Step 1: turn the chat into a table ----
PATTERN = re.compile(r'^(\d{2}/\d{2}/\d{4}), (\d{1,2}:\d{2})\s?([ap]m) - (.*)$')

messages = []

with open('chat.txt', encoding='utf-8') as f:
    for line in f:
        line = line.rstrip('\n').replace(' ', ' ')
        m = PATTERN.match(line)
        if m:
            date, time, ampm, rest = m.groups()
            if ': ' in rest:
                sender, text = rest.split(': ', 1)
            else:
                sender, text = 'SYSTEM', rest
            messages.append({'date': date, 'time': f'{time} {ampm}', 'sender': sender, 'text': text})
        elif messages:
            messages[-1]['text'] += '\n' + line

df = pd.DataFrame(messages)
df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')

# Permanent ID = the message's position in the full chat.
# It never changes when filters change, and new messages only get added at the end,
# so every later file (extracted.csv, corrections) can safely point to it.
df.insert(0, 'msg_id', range(len(df)))

print('Messages:', len(df))
print('From', df['date'].min().date(), 'to', df['date'].max().date())

# ---- Step 2: keep only company announcements ----
KEYWORDS = r'placement|drive|hiring|lpa|ctc|stipend|ppo|internship'
PAY_WORDS = r'lpa|ctc|stipend'

# always drop: results and private details
DROP_ALWAYS = r'congratulations|final selection|superset id|roll number|password|passcode'
# drop only when the message has no pay info (real drives mention pay; name lists don't)
DROP_UNLESS_PAY = r'shortlist|selected students'

ann = df[df['sender'] != 'SYSTEM']
ann = ann[ann['text'].str.contains(KEYWORDS, case=False)]
ann = ann[ann['text'].str.len() > 200]
ann = ann[~ann['text'].str.contains(DROP_ALWAYS, case=False)]
is_list = ann['text'].str.contains(DROP_UNLESS_PAY, case=False)
has_pay = ann['text'].str.contains(PAY_WORDS, case=False)
ann = ann[~is_list | has_pay]

ann = ann.drop(columns=['sender'])

PHONE = r'(\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}'
EMAIL = r'[\w.+-]+@[\w-]+\.[\w.]+'
ann['text'] = ann['text'].str.replace(PHONE, '[PHONE]', regex=True)
ann['text'] = ann['text'].str.replace(EMAIL, '[EMAIL]', regex=True)
ann['text'] = ann['text'].str.replace(r'https?://chat\.whatsapp\.com/\S+', '[LINK REMOVED]', regex=True)

print('Announcements kept:', len(ann))
ann.to_csv('announcements.csv', index=False)
