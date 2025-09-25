import streamlit as st
import pandas as pd

import model
import data

st.markdown(
    """
    <style>
    /* Apply clean font styling */
    .stDataFrame, .stMarkdown, .stTextInput, .stDateInput {
        font-family: 'Inter', 'Roboto', 'Segoe UI', sans-serif;
        font-size: 14px;
    }
    /* Make dataframe cells a bit tighter like trading UIs */
    .dataframe td, .dataframe th {
        padding: 4px 8px;
    }
    /* Center top-level MultiIndex headers (Calls, Puts) */
    .dataframe thead tr:first-child th {
        text-align: center !important;
    }
    /* Center the Strike column cells */
    .dataframe tbody tr td:nth-child(4) {
        text-align: center !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.set_page_config(page_title="Options Chain Viewer", layout="wide")

st.title("Options (BTC)")

# Date input
exp = pd.Timestamp.utcnow()
exp = (exp if exp.hour < 8 else exp + pd.Timedelta(days=1)).floor('D')
exp = pd.Timestamp(st.date_input("Expiry Date", value=exp))
st.write(f"Expiry date: **{exp.strftime('%Y-%m-%d')}**")

ticker = 'BTC'
options_data = data.get_options_data(ticker, exp)
options_data['option_type'] = options_data['instrument_name'].str.split('-').str[-1]
options_data['strike'] = options_data['instrument_name'].str.split('-').str[2].astype(int)
exp_days = model.get_days_to_exp(exp) # TODO: use milliseconds instead
options_data['mark'] = options_data.apply(lambda x: model.black_scholes(x.underlying_price, x.strike, exp_days/365, 0, x.mark_iv / 100, x.option_type) / x.underlying_price, axis=1)

df = options_data.pivot_table(index='strike', columns='option_type', values=['mark', 'mark_iv', 'underlying_price'], aggfunc='first').reset_index()
df = pd.DataFrame({
    ("Calls", "Mark"): df[('mark', 'C')],
    ("Calls", "Mark_IV"): df[('mark_iv', 'C')],
    ("Calls", "Underlying_Price"): df[('underlying_price', 'C')],
    ("Strike", ""): df[('strike', '')],
    ("Puts", "Mark"): df[('mark', 'P')],
    ("Puts", "Mark_IV"): df[('mark_iv', 'P')],
    ("Puts", "Underlying_Price"): df[('underlying_price', 'P')],
})
fut_px = options_data.iloc[0].underlying_price
valid_strikes = df[df[("Strike", "")] <= fut_px]
df[('Strike', '')] = df[('Strike', '')].apply(lambda x: f"{x:,.0f}")

for col in [("Calls", "Bid"), ("Calls", "Ask"), ("Puts", "Bid"), ("Puts", "Ask")]:
    df[col] = df[(col[0], 'Mark')] + (0.001 * (1 if col[1] == 'Ask' else -1))
    df[col] = df[col].mask(df[col] <= 0)
    color = 'green' if col[1] == 'Bid' else 'red'
    df[col] = df.apply(lambda x: f"<span style='color:{color};'>{x[col]:.4f}<span><br><span style='font-size:12px;color:gray;'>${x[col] * x[col[0], 'Underlying_Price']:,.2f}</span>" if pd.notna(x[col]) else '-', axis=1)

for col in [("Calls", "Mark"), ("Puts", "Mark")]:
    df[col] = df.apply(lambda x: f"{x[col]:.4f}<br><span style='font-size:12px;color:gray;'>{x[(col[0], 'Mark_IV')]:,.2f}%</span>", axis=1)
df = df[[("Calls", "Bid"), ("Calls", "Mark"), ("Calls", "Ask"), ("Strike", ""), ("Puts", "Bid"), ("Puts", "Mark"), ("Puts", "Ask")]]

if not valid_strikes.empty:
    fut_px_idx = valid_strikes.iloc[-1].name
    futures_text = f"<span style='color:aqua; font-weight:bold;'>Futures: {fut_px:,.0f}</span>"
    df.loc[fut_px_idx, ('Strike', '')] += f'<br>{futures_text}'

html_table = df.to_html(escape=False, index=False)
html_table = html_table.replace(
    '<table border="1" class="dataframe">',
    '<table border="1" class="dataframe" style="width:100%; table-layout:fixed;">'
)
st.markdown(html_table, unsafe_allow_html=True)