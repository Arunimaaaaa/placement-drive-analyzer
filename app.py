"""Step 6: dashboard.  Run with:  py -3.13 -m streamlit run app.py"""
import sqlite3
import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title='Placement Drive Analyzer', layout='wide')

OPP_TYPES = ['job', 'internship_ppo', 'internship']
TYPE_LABEL = {'job': 'Job', 'internship_ppo': 'Internship + PPO', 'internship': 'Internship',
              'competition': 'Competition', 'training_or_event': 'Training / event',
              'notice': 'Notice'}
TYPE_COLOR = {'Job': '#2a78d6', 'Internship + PPO': '#eb6834', 'Internship': '#1baf7a'}
BLUE = '#2a78d6'


@st.cache_data
def load():
    con = sqlite3.connect('placements.db')
    df = pd.read_sql_query("SELECT * FROM announcements WHERE type != 'duplicate'", con)
    con.close()
    df['date'] = pd.to_datetime(df['date'])
    df['type_label'] = df['type'].map(TYPE_LABEL)
    return df


df = load()
opps = df[df['type'].isin(OPP_TYPES)].copy()

# ---------------- header ----------------
st.title('Placement Drive Analyzer')
st.caption(f"Two years of a college placement WhatsApp group ({df['date'].min():%b %Y} – "
           f"{df['date'].max():%b %Y}), parsed and structured with an LLM, then validated by hand.")

k1, k2, k3, k4 = st.columns(4)
k1.metric('Announcements analysed', len(df))
k2.metric(f"Real hiring opportunities ({len(opps) / len(df):.0%})", len(opps))
pay_known = (opps['ctc_lpa_max'].notna() | opps['stipend_per_month'].notna()).sum()
k3.metric('Opportunities that state pay', f"{int(pay_known)} of {len(opps)}")
k4.metric('Drives with a service bond', int((opps['bond_years'] > 0).sum()))

# ---------------- filters ----------------
f1, f2, f3 = st.columns([2, 2, 1])
types = f1.multiselect('Opportunity type', [TYPE_LABEL[t] for t in OPP_TYPES],
                       default=[TYPE_LABEL[t] for t in OPP_TYPES])
min_ctc = f2.slider('Minimum CTC (LPA)', 0.0, 12.0, 0.0, 0.5)
no_bond = f3.toggle('Hide drives with a bond')

view = opps[opps['type_label'].isin(types)]
if min_ctc > 0:
    view = view[view['ctc_lpa_max'] >= min_ctc]
if no_bond:
    view = view[~(view['bond_years'] > 0)]

# ---------------- charts ----------------
left, right = st.columns(2)

with left:
    st.subheader('CTC range by company')
    pay = view.dropna(subset=['ctc_lpa_max'])
    if pay.empty:
        st.info('No drives with a stated CTC match these filters.')
    else:
        base = alt.Chart(pay).encode(
            y=alt.Y('company:N', title=None, axis=alt.Axis(labelOverlap=False, labelLimit=180),
                   sort=alt.EncodingSortField('ctc_lpa_max', op='max', order='descending')),
            tooltip=['company', 'type_label', alt.Tooltip('ctc_lpa_min', title='CTC min (LPA)'),
                     alt.Tooltip('ctc_lpa_max', title='CTC max (LPA)'),
                     alt.Tooltip('fixed_ctc_lpa', title='Fixed (LPA)'),
                     alt.Tooltip('bond_years', title='Bond (years)')])
        bars = base.mark_rule(strokeWidth=8, strokeCap='round').encode(
            x=alt.X('ctc_lpa_min:Q', title='CTC (LPA)', scale=alt.Scale(domain=[0, 13])),
            x2='ctc_lpa_max:Q',
            color=alt.Color('type_label:N', title=None,
                            scale=alt.Scale(domain=list(TYPE_COLOR), range=list(TYPE_COLOR.values())),
                            legend=alt.Legend(orient='bottom')))
        dots = base.mark_point(filled=True, size=70).encode(
            x='ctc_lpa_max:Q',
            color=alt.Color('type_label:N', scale=alt.Scale(domain=list(TYPE_COLOR),
                                                           range=list(TYPE_COLOR.values())), legend=None))
        st.altair_chart((bars + dots).properties(height=max(220, 26 * len(pay))), width='stretch')
        st.caption('Bars run from the lowest to the highest CTC stated in the announcement.')

with right:
    st.subheader("What's actually in a placement group")
    mix = df['type_label'].value_counts().rename_axis('type').reset_index(name='posts')
    mix['is_opp'] = mix['type'].isin(TYPE_COLOR)
    chart = alt.Chart(mix).mark_bar(cornerRadius=4, height=18).encode(
        x=alt.X('posts:Q', title='Announcements'),
        y=alt.Y('type:N', sort='-x', title=None),
        color=alt.condition('datum.is_opp', alt.value(BLUE), alt.value('#b4b2a9')),
        tooltip=['type', 'posts'])
    st.altair_chart(chart.properties(height=240), width='stretch')
    st.caption('Blue = real hiring opportunities. The rest are competitions, trainings and notices.')

    st.subheader('Opportunities per month')
    monthly = (opps.set_index('date').resample('MS').size()
               .loc['2026-05':].rename('drives').reset_index())
    line = alt.Chart(monthly).mark_bar(cornerRadius=4, color=BLUE).encode(
        x=alt.X('yearmonth(date):O', title=None),
        y=alt.Y('drives:Q', title='Drives'),
        tooltip=[alt.Tooltip('yearmonth(date):T', title='Month'), 'drives'])
    st.altair_chart(line.properties(height=200), width='stretch')

# ---------------- table ----------------
st.subheader(f'Opportunities ({len(view)})')
table = view[['date', 'company', 'type_label', 'role', 'ctc_lpa_min', 'ctc_lpa_max', 'fixed_ctc_lpa',
              'stipend_per_month', 'bond_years', 'location']].sort_values('date', ascending=False)
st.dataframe(
    table, hide_index=True, width='stretch',
    column_config={
        'date': st.column_config.DateColumn('Posted', format='DD MMM YYYY'),
        'company': 'Company', 'type_label': 'Type', 'role': 'Role',
        'ctc_lpa_min': st.column_config.NumberColumn('CTC min (LPA)', format='%.2f'),
        'ctc_lpa_max': st.column_config.NumberColumn('CTC max (LPA)', format='%.2f'),
        'fixed_ctc_lpa': st.column_config.NumberColumn('Fixed (LPA)', format='%.2f'),
        'stipend_per_month': st.column_config.NumberColumn('Stipend / month (₹)', format='%d'),
        'bond_years': st.column_config.NumberColumn('Bond (yrs)', format='%g'),
        'location': 'Location'})

with st.expander('How this data was built and checked'):
    st.markdown("""
- **Source:** WhatsApp export of the placement group. Names, phone numbers, emails and group links were removed before any processing; the raw chat is never published.
- **Extraction:** Google Gemini read each announcement and returned company, type, CTC, stipend, bond and more as JSON.
- **Validation:** a script checks that every number the AI returned appears in the original message, then every opportunity row was reviewed by hand.
- **Errors found and fixed:** stipends written in lakhs instead of rupees (fixed in the prompt), a "no bond" value invented for 9 messages that never mention a bond, wrong track picked in multi-track offers, mislabelled types, and duplicate reposts. Every fix is logged with a reason in `clean.py`.
- **Limits:** drives shared only as PDFs or images (e.g. CarWale) have no details in the chat, so they can't be analysed.
""")
