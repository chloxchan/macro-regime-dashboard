# User Manual: Macro Regime & Sector Rotation Dashboard

## 1. Overview

This dashboard classifies the U.S. economy into one of four macro regimes each month — Goldilocks, Reflation, Stagflation, or Deflationary Slowdown — based on industrial production growth and inflation trends. It then shows how each S&P sector historically performs within each regime, and backtests a simple sector-rotation strategy against a buy-and-hold benchmark.

**Live app URL:** _(add your Streamlit Community Cloud URL here once deployed)_
**Data sources:** FRED (macro data), Yahoo Finance (sector ETF prices)
**Update frequency:** Data refreshes automatically every 24 hours (cached)

---

## 2. Getting Started

### Running Locally
1. Open Terminal and navigate to the project folder:
   ```
   cd ~/Projects/macro-regime-dashboard
   ```
2. Activate the virtual environment:
   ```
   source .venv/bin/activate
   ```
3. Launch the app:
   ```
   streamlit run app.py
   ```
4. Your browser will open automatically to `http://localhost:8501`. If it doesn't, paste that URL manually into any browser.

### Using the Live Version
Simply visit the deployed URL — no installation needed. First load may take 20-40 seconds while data downloads; subsequent visits are faster due to caching.

---

## 3. Dashboard Layout

### Top Metrics Row
Four boxes at the top show the most recent reading for:
- **Current Regime** — this month's classification
- **Latest CPI YoY** — year-over-year inflation rate
- **Latest IndPro YoY** — year-over-year industrial production growth
- **10Y-2Y Spread** — Treasury yield curve slope (negative values often signal recession risk)

### Sidebar Filters (left side of screen)
- **Regimes to include**: Check/uncheck which of the four regimes to display in the sector heatmap below. Useful for isolating a single regime's sector behavior.
- **Date range slider**: Drag either end to narrow the historical window analyzed. Useful for focusing on a specific era (e.g. post-2020).

### Chart 1: S&P 500 Colored by Macro Regime
A log-scale price chart of the S&P 500 from 1998 to present, with each month color-coded by its detected regime:
- Green = Goldilocks
- Blue = Reflation
- Red = Stagflation
- Gray = Deflationary Slowdown

**How to read it:** Look for clustering — e.g. red dots concentrated around 2022 (inflation shock) or gray dots around 2008-2009 (financial crisis) confirm the model is capturing real historical episodes correctly.

### Chart 2: Average Monthly Sector Returns by Regime
A heatmap showing which sectors historically outperform or underperform in each regime. Green cells indicate positive average monthly returns; red cells indicate negative.

**How to read it:** Scan each row (sector) across the four regime columns to see which environment favors that sector. Energy and Real Estate typically show the widest swings; Utilities and Consumer Staples stay more stable across all regimes.

### Chart 3: Regime Rotation Strategy vs Equal-Weight Benchmark
A cumulative growth chart comparing two approaches:
- **Blue line**: A strategy that rotates monthly into the 3 sectors that have historically performed best in the current regime (using only past data, no lookahead).
- **Orange dashed line**: A simple benchmark that holds all 10 sectors equally weighted at all times.

Below the chart, annualized Sharpe ratios for both approaches are displayed for direct comparison.

**How to read it:** If the blue line consistently sits below the orange line, naive regime rotation is underperforming a passive approach — a common and informative finding, not a flaw in the model.

---

## 4. Interpreting the Regimes

| Regime | Growth | Inflation | Typical Historical Context |
|---|---|---|---|
| Goldilocks | Positive | Below 2.5% | Steady expansion, low inflation (e.g. mid-2010s) |
| Reflation | Positive | Above 2.5% | Growth with rising prices (e.g. 2021-2022 recovery) |
| Stagflation | Negative | Above 2.5% | Weak growth, high inflation (e.g. 1970s, 2022) |
| Deflationary Slowdown | Negative | Below 2.5% | Recession, falling prices (e.g. 2008-2009, 2020) |

---

## 5. Known Limitations

- Regime classification uses only two macro variables (growth and inflation); it does not account for monetary policy stance, credit conditions, or geopolitical shocks directly.
- The rotation backtest ignores transaction costs, taxes, and slippage — real-world implementation would underperform the backtested figures shown.
- Sector ETF history only extends to 1998, limiting the sample to roughly three full business cycles.
- Regime labels can lag real-time conditions since GDP/inflation data is reported with a delay of several weeks to months.

---

## 6. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Blank page or spinning indefinitely | Data pull from FRED/Yahoo Finance is slow or rate-limited | Wait 60 seconds and refresh; check internet connection |
| "KeyError: FRED_API_KEY" | Secrets file missing or misconfigured | Confirm `.streamlit/secrets.toml` contains `FRED_API_KEY = "yourkey"` |
| Charts show no data for recent months | FRED/Yahoo Finance hasn't published the latest month yet | Normal — economic data has natural reporting lags |
| App looks outdated | Cache hasn't refreshed yet | Cache clears every 24 hours automatically; restart the app to force a refresh |

---

## 7. For Developers

**Tech stack:** Python, Streamlit, Plotly, pandas, scikit-learn, yfinance, fredapi
**Repo structure:**
```
macro-regime-dashboard/
├── app.py
├── requirements.txt
├── .streamlit/secrets.toml (not committed to GitHub)
└── .gitignore
```
**To modify regime thresholds:** Edit the `label_regime()` function in `app.py` — current thresholds are 0% for growth and 2.5% for inflation.
**To add new sectors or asset classes:** Add tickers to the `sector_etfs` dictionary inside `load_sectors()`.
