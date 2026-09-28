# 🍬 Nassau Candy Distributor — Product Line Profitability & Margin Performance Analysis

> Unified Mentor capstone project — turning 10,194 raw order lines into
> product-line margin intelligence: what *truly* drives profit, which divisions
> underperform financially, and where pricing, sourcing or product rationalisation
> is needed.

## Headline results (FY2024–FY2025)

| KPI | Value |
|---|---|
| Total sales | **$141,783.63** (+44.6% YoY) |
| Gross profit | **$93,442.80** |
| Gross margin | **65.91%** (flat YoY) |
| Pareto concentration | **5 of 15 SKUs = 95.1% of profit** (HHI 18.3 — High dependency) |
| Margin-risk product | **Kazookles — 7.7% margin, 92.3% cost ratio** → fix-or-exit |
| Hidden gems | Sugar pilots at 62–80% margin, <0.3% of revenue → scale up |

## Deliverables

| Deliverable | Location |
|---|---|
| 📊 **Streamlit live dashboard** | [`app/streamlit_app.py`](app/streamlit_app.py) |
| 📄 **Research paper** (EDA, insights, recommendations, 7 figures) | [`reports/research_paper.md`](reports/research_paper.md) |
| 📋 **Executive summary** for stakeholders | [`reports/executive_summary.md`](reports/executive_summary.md) |
| 🧼 Cleaned dataset | `data/processed/nassau_candy_clean.csv` (regenerable) |
| 🖼️ Analysis figures & tables | `reports/figures/`, `reports/tables/` |

## Dashboard modules (per project brief)

1. **Product Profitability Overview** — margin leaderboard, profit-contribution
   charts, profit–margin quadrant map, full product table + CSV download
2. **Division Performance Dashboard** — revenue-vs-profit comparison, margin
   distribution by division, division scorecard with imbalance & volatility
3. **Cost vs Margin Diagnostics** — cost–sales scatter with break-even guides,
   margin-risk register, cost-heavy/margin-poor flags, unit economics
4. **Profit Concentration Analysis** — Pareto charts (revenue/profit), dependency
   indicators (top-1/3/5 shares, HHI), geographic congestion view
5. **Executive Overview** — KPI cards, monthly margin trend, region heat bars,
   factory footprint map (uses the brief's factory coordinates & product–factory
   correlation table)

**User capabilities:** date-range selector · division filter (+ region) ·
margin-risk threshold slider (recomputes all risk flags live) · product search ·
optional raw-record viewer.

## Quick start

```bash
pip install -r requirements.txt

# 1) clean & validate the raw extract (prints machine-readable cleaning report)
python -m src.data_prep

# 2) regenerate all paper figures + CSV tables
python analysis/run_eda.py

# 3) launch the live dashboard
streamlit run app/streamlit_app.py
```

## Repository layout

```
├── app/
│   └── streamlit_app.py        # 5-module interactive dashboard
├── src/
│   ├── config.py               # paths, factory coords, product→factory map, thresholds
│   ├── data_prep.py            # cleaning & validation pipeline (brief-mandated rules)
│   └── analytics.py            # KPI engine: product/division/pareto/volatility/flags
├── analysis/
│   └── run_eda.py              # figure + table generator for the paper
├── data/
│   ├── Nassau_Candy_Distributor.csv
│   └── processed/              # cleaned output (10,194 × 31 engineered cols)
├── reports/
│   ├── research_paper.md       # EDA, insights, recommendations
│   ├── executive_summary.md    # stakeholder briefing
│   ├── figures/                # 7 publication figures
│   └── tables/                 # 6 analysis tables (CSV)
├── requirements.txt
└── .streamlit/config.toml      # theme + server settings
```

## Data pipeline guarantees

- **Validation:** every rule in the brief is enforced and logged — numeric coercion,
  accounting identity `Sales − Cost = Gross Profit` (holds exactly, tol $0.02),
  zero-sales/invalid-profit removal, missing-unit handling.
- **Standardisation:** `"Wonka Bar -Scrumdiddlyumptious"` → `"Wonka Bar -
  Scrumdiddlyumptious"` (2,064 rows); whitespace-normalised labels → 15 unique SKUs.
- **Attribution:** each product mapped to its factory via the brief's correlation
  table (0 unmapped rows).
- **Known source quirks (documented, not silently fixed):** ship dates fall in
  2026–2030; unit price/cost constant per SKU → product-level margin volatility is
  structurally zero and mix is reported instead.

## Tech stack

Python 3.11 · pandas · NumPy · Streamlit · Plotly · Matplotlib — one shared
analytics library (`src/`) feeds the paper, the summary and the dashboard, so all
deliverables quote identical numbers.
