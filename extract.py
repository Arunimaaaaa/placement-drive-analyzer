"""Step 3: ask Gemini to pull structured fields out of each announcement.

Input : announcements.csv
Output: extracted.csv   (raw AI output, never edited by hand)

Re-running is safe: messages already in extracted.csv are skipped,
so a dropped connection never loses finished work.
"""
import os, json, time
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'),
                      http_options=types.HttpOptions(timeout=60000))

MODEL = 'gemini-flash-lite-latest'
OUT = 'extracted.csv'

PROMPT = """You extract details from a college placement WhatsApp announcement (India).
Return ONLY a JSON object with exactly these keys:
company, role, type, ctc_lpa_min, ctc_lpa_max, stipend_per_month,
bond_years, fixed_ctc_lpa, eligible_branches, min_criteria, location, deadline.

type must be one of:
- "job": a company hiring for a full-time role
- "internship_ppo": an internship that can convert to a full-time offer (PPO)
- "internship": an internship with no full-time offer mentioned
- "competition": a hackathon, quiz or challenge, even if the prize includes an internship, PPI or PPO
- "training_or_event": a course, webinar, session, seminar or mock test
- "notice": reminders, instructions, schedules, results or general information

Rules:
- ctc_lpa_min, ctc_lpa_max, fixed_ctc_lpa are in lakhs per annum, e.g. "Rs 4,00,000 per annum" -> 4.
- stipend_per_month is in rupees per month, e.g. "Rs 15K per month" -> 15000. Never write it in lakhs.
- bond_years is a number of years; "no bond" -> 0.
- If only one CTC is given, put it in both ctc_lpa_min and ctc_lpa_max.
- fixed_ctc_lpa is the fixed part only, when the message splits fixed and variable pay; otherwise null.
- If something is not stated, use null. Do not guess.
- If the message lists many different companies, return ONE object with company "Multiple companies" and type "notice".
Announcement:
"""


def ask_gemini(text):
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=PROMPT + text,
                config=types.GenerateContentConfig(response_mime_type='application/json'),
            )
            result = json.loads(response.text)
            if isinstance(result, list):          # safety net: AI sometimes returns a list
                result = result[0] if result else {}
            return result
        except Exception as e:
            print('  attempt', attempt + 1, 'failed:', str(e)[:80])
            time.sleep(20)
    return {}


ann = pd.read_csv('announcements.csv')

rows = []
done = set()
if os.path.exists(OUT):
    old = pd.read_csv(OUT)
    if 'msg_id' in old.columns:
        old = old.dropna(subset=['type'])         # retry rows that failed last time
        rows = old.to_dict('records')
        done = set(old['msg_id'])

todo = ann[~ann['msg_id'].isin(done)]
print(len(done), 'already done,', len(todo), 'to go')

for _, msg in todo.iterrows():
    data = ask_gemini(msg['text'])
    data['msg_id'] = msg['msg_id']
    data['date'] = msg['date']
    rows.append(data)
    pd.DataFrame(rows).to_csv(OUT, index=False)   # save after every message
    print('Done', len(rows), 'of', len(ann), '|', data.get('company'), '|', data.get('type'))
    time.sleep(5)

out = pd.DataFrame(rows).sort_values('msg_id')
out.to_csv(OUT, index=False)
print('Saved', OUT, 'with', len(out), 'rows')
