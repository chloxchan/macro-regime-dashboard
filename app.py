import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from fredapi import Fred

st.set_page_config(page_title="Macro Regime & Sector Rotation", layout="wide")
st.title("Macro Regime & Sector Rotation Dashboard")
st.caption("Classifies U.S. macro regimes and shows conditional sector ETF performance, 1998-present.")

@st.cache_data(ttl=86400)
def load_macro():
    fred = Fred(api_key=st.secrets["FRED_API_KEY"])
    series_ids = {"T10Y2Y": "T10Y2Y", "UNRATE": "UNRATE", "CPIAUCSL": "CPIAUCSL", "INDPRO": "INDPRO"}
    raw = {name: fred.get_series(sid) for name, sid in series_ids.items()}
    macro = pd.DataFrame(raw)
    macro_m = macro.resample("ME").last()
    macro_m["CPI_YoY"] = macro_m["CPIAUCSL"].pct_change(12) * 100
    macro_m["INDPRO_YoY"] = macro_m["INDPRO"].pct_change(12) * 100
    macro_m["UNRATE_chg"] = macro_m["UNRATE"].diff(3)
    return macro_m.dropna()

@st.cache_data(ttl=86400)
def load_sectors():
    sector_etfs = {
        "XLK": "Technology", "XLF": "Financials", "XLE": "Energy", "XLV": "Health Care",
        "XLI": "Industrials", "XLY": "Cons. Discretionary", "XLP": "Cons. Staples",
        "XLU": "Utilities", "XLB": "Materials", "XLRE": "Real Estate"
    }
    prices = yf.download(list(sector_etfs.keys()), start="1998-12-01", auto_adjust=True, progress=False)["Close"]
    rets = prices.resample("ME").last().pct_change().dropna().rename(columns=sector_etfs)
    return rets

def label_regime(row):
    g_high = row["INDPRO_YoY"] > 0
    i_high = row["CPI_YoY"] > 2.5
    if g_high and not i_high:
        return "Goldilocks"
    elif g_high and i_high:
        return "Reflation"
    elif not g_high and i_high:
        return "Stagflation"
    else:
        return "Deflationary Slowdown"

with st.spinner("Loading macro and market data..."):
    macro_m = load_macro()
    macro_m["regime"] = macro_m.apply(label_regime, axis=1)
    sector_rets = load_sectors()
    merged = sector_rets.join(macro_m[["regime"]], how="inner")

latest_cpi = macro_m["CPI_YoY"].iloc[-1]
latest_indpro = macro_m["INDPRO_YoY"].iloc[-1]
latest_spread = macro_m["T10Y2Y"].iloc[-1]
latest_regime = macro_m["regime"].iloc[-1]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Current Regime", latest_regime)
col2.metric("Latest CPI YoY", f"{latest_cpi:.2f}%")
col3.metric("Latest IndPro YoY", f"{latest_indpro:.2f}%")
col4.metric("10Y-2Y Spread", f"{latest_spread:.2f}")

st.divider()

st.sidebar.header("Filters")
all_regimes = sorted(macro_m["regime"].unique())
regime_filter = st.sidebar.multiselect("Regimes to include", all_regimes, default=all_regimes)
date_min, date_max = macro_m.index.min().date(), macro_m.index.max().date()
date_range = st.sidebar.slider("Date range", min_value=date_min, max_value=date_max, value=(date_min, date_max))

filtered_macro = macro_m[
    (macro_m["regime"].isin(regime_filter)) &
    (macro_m.index.date >= date_range[0]) &
    (macro_m.index.date <= date_range[1])
]
filtered_merged = merged.loc[merged.index.isin(filtered_macro.index)]

st.subheader("S&P 500 Colored by Macro Regime")
spx = yf.download("^GSPC", start="1998-12-01", auto_adjust=True, progress=False)["Close"]
spx_m = spx.resample("ME").last()
spx_m.index = spx_m.index.to_period("M").to_timestamp()

macro_index_normalized = macro_m.index.to_period("M").to_timestamp()
spx_aligned = spx_m.reindex(macro_index_normalized).ffill()
spx_aligned.index = macro_m.index

regime_colors = {"Goldilocks": "#2CA02C", "Reflation": "#1F77B4", "Stagflation": "#D62728", "Deflationary Slowdown": "#7F7F7F"}
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=macro_m.index, y=spx_aligned.values.flatten(), mode="lines",
                           line=dict(color="lightgray", width=1), showlegend=False))
for reg, color in regime_colors.items():
    mask = macro_m["regime"] == reg
    ys = np.where(mask, spx_aligned.values.flatten(), np.nan)
    fig1.add_trace(go.Scatter(x=macro_m.index, y=ys, mode="markers", marker=dict(color=color, size=5), name=reg))
fig1.update_layout(yaxis_type="log", legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5))
fig1.update_xaxes(title_text="Date")
fig1.update_yaxes(title_text="S&P 500 (log)")
st.plotly_chart(fig1, use_container_width=True)

st.subheader("Average Monthly Sector Returns by Regime")
regime_perf = filtered_merged.groupby("regime")[list(sector_rets.columns)].mean() * 100
fig2 = px.imshow(regime_perf.T, text_auto=".2f", aspect="auto", color_continuous_scale="RdYlGn", zmin=-1, zmax=3)
fig2.update_xaxes(title_text="Regime")
fig2.update_yaxes(title_text="Sector")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Regime Rotation Strategy vs Equal-Weight Benchmark")
rotation_returns, dates_out = [], []
regime_series = macro_m["regime"]
for i in range(24, len(sector_rets)):
    date = sector_rets.index[i]
    if date not in regime_series.index:
        continue
    current_regime = regime_series.loc[date]
    hist_mask = (regime_series.index < date) & (regime_series == current_regime)
    hist_rets = sector_rets.reindex(regime_series.index[hist_mask]).dropna(how="all")
    if len(hist_rets) < 6:
        continue
    top3 = hist_rets.mean().nlargest(3).index
    rotation_returns.append(sector_rets.loc[date, top3].mean())
    dates_out.append(date)

rotation_series = pd.Series(rotation_returns, index=dates_out)
benchmark_series = sector_rets.mean(axis=1).reindex(dates_out)
rotation_cum = (1 + rotation_series).cumprod()
benchmark_cum = (1 + benchmark_series).cumprod()

fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=rotation_cum.index, y=rotation_cum.values, name="Regime Rotation", line=dict(color="#1F77B4", width=2.5)))
fig3.add_trace(go.Scatter(x=benchmark_cum.index, y=benchmark_cum.values, name="Equal-Weight Benchmark", line=dict(color="#FF7F0E", width=2.5, dash="dash")))
fig3.update_layout(yaxis_type="log", legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5))
fig3.update_xaxes(title_text="Date")
fig3.update_yaxes(title_text="Cumulative Growth")
st.plotly_chart(fig3, use_container_width=True)

sharpe_rot = (rotation_series.mean() * 12) / (rotation_series.std() * np.sqrt(12))
sharpe_bench = (benchmark_series.mean() * 12) / (benchmark_series.std() * np.sqrt(12))
st.write(f"**Rotation Sharpe:** {sharpe_rot:.2f} | **Benchmark Sharpe:** {sharpe_bench:.2f}")

