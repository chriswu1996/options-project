import model
import pandas as pd
import streamlit as st

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

st.title("Options Demo")

mode_is_intraday = st.toggle("Intraday", value=False)
mode = 'Intraday' if mode_is_intraday else 'Daily'

exp = pd.Timestamp.utcnow()
option_date = (exp if exp.hour < 8 else exp + pd.Timedelta(days=1)).floor('D')  # Daily options on Deribit expire every day at 08:00 UTC
if mode == 'Daily':
    exp = option_date = pd.Timestamp(st.date_input("Expiry Date", value=option_date), tz='UTC')
    exp += pd.Timedelta(hours=8)
    st.write(f"Expiry: **{exp}** UTC")
else:
    exp = exp.replace(second=0, microsecond=0) + pd.Timedelta(minutes=1)
    start = exp + pd.Timedelta(minutes=(-exp.minute % 5))
    end = exp + pd.Timedelta(minutes=30)
    options = [start + pd.Timedelta(minutes=5 * i) for i in range(int((end - start).total_seconds() // 300) + 1)]
    exp = st.selectbox("Expiry (UTC):", options, format_func=lambda d: d.strftime("%I:%M %p"))

ticker = st.selectbox("Ticker", ['BTC', 'ETH'])  # SOL, SUI
df, fut_px = model.get_options_table(option_date, exp, mode, ticker)

for col in [("Calls", "Bid"), ("Calls", "Ask"), ("Puts", "Bid"), ("Puts", "Ask")]:
    df[col] = df[(col[0], 'Mark')] + (0.001 * (1 if col[1] == 'Ask' else -1))
    df[col] = df[col].mask(df[col] <= 0)
    color = 'green' if col[1] == 'Bid' else 'red'
    df[col] = df.apply(lambda x: f"<span style='color:{color};'>{x[col]:.4f}<span><br><span style='font-size:12px;color:gray;'>${x[col] * x[col[0], 'Underlying_Price']:,.2f}</span>" if pd.notna(x[col]) else '-', axis=1)

for col in [("Calls", "Mark"), ("Puts", "Mark")]:
    df[col] = df.apply(lambda x: f"{x[col]:.4f}<br><span style='font-size:12px;color:gray;'>{x[(col[0], 'Mark_IV')]:,.2f}%</span>", axis=1)
df = df[[("Calls", "Bid"), ("Calls", "Mark"), ("Calls", "Ask"), ("Strike", ""), ("Puts", "Bid"), ("Puts", "Mark"), ("Puts", "Ask")]]

valid_strikes = df[df[("Strike", "")] <= fut_px]
df[('Strike', '')] = df[('Strike', '')].apply(lambda x: f"{x:,.0f}")
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