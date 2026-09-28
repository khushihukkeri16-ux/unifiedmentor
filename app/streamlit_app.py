"""Nassau Candy Distributor — Product Line Profitability & Margin Performance.

Streamlit live-analytics dashboard. Run:
    streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import analytics, config, data_prep  # noqa: E402

# --------------------------------------------------------------------------- #
# Page & style
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Nassau Candy — Profitability Intelligence",
    page_icon="🍬",
    layout="wide",
    initial_sidebar_state="expanded",
)

DIV_COLOR = {"Chocolate": "#8B5A2B", "Sugar": "#E8590C", "Other": "#1864AB"}
QUAD_COLOR = {
    "Star (High Profit / High Margin)": "#2B8A3E",
    "Cash Trap (High Sales / Low Margin)": "#E8590C",
    "Hidden Gem (Low Profit / High Margin)": "#1864AB",
    "Laggard (Low Sales / Low Profit)": "#868E96",
}
FLAG_COLOR = {"Healthy": "#2B8A3E", "Acceptable": "#FAB005",
              "At Risk": "#E8590C", "Critical": "#C92A2A"}

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.6rem;}
      div[data-testid="stMetricValue"] {font-size: 1.55rem;}
      .small-note {color:#868e96; font-size:0.82rem;}
      .risk-pill {padding:2px 10px; border-radius:12px; font-weight:600;
                  font-size:0.8rem; color:#fff; display:inline-block;}
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
@st.cache_data(show_spinner="Cleaning & validating raw order data…")
def load_clean() -> tuple[pd.DataFrame, dict]:
    return data_prep.clean()


def fmt_usd(x: float, dec: int = 0) -> str:
    return f"${x:,.{dec}f}"


df_all, clean_report = load_clean()

# --------------------------------------------------------------------------- #
# Sidebar — user capabilities
# --------------------------------------------------------------------------- #
st.sidebar.image(
    "https://img.icons8.com/emoji/96/candy-emoji.png", width=58)
st.sidebar.title("Filters & Controls")

min_d, max_d = df_all["order_date"].min().date(), df_all["order_date"].max().date()
date_range = st.sidebar.date_input(
    "📅 Order date range",
    value=(min_d, max_d), min_value=min_d, max_value=max_d,
    help="Filters every module to orders placed in this window.",
)
if not isinstance(date_range, tuple) or len(date_range) != 2:
    date_range = (min_d, max_d)

divisions = sorted(df_all["division"].unique())
sel_div = st.sidebar.multiselect(
    "🏭 Division", divisions, default=divisions)

regions = sorted(df_all["region"].unique())
sel_region = st.sidebar.multiselect(
    "🗺️ Region (optional)", regions, default=regions,
    help="Atlantic, Gulf, Interior, Pacific")

margin_threshold = st.sidebar.slider(
    "🎯 Margin-risk threshold (%)", min_value=5, max_value=60,
    value=int(config.AT_RISK_MARGIN), step=1,
    help="Products below this gross margin are flagged 'At Risk' / 'Critical' "
         "and routed to repricing, cost-renegotiation or discontinuation review."
)

product_search = st.sidebar.text_input(
    "🔎 Product search", placeholder="e.g. wonka, nerds, gobstopper…",
    help="Free-text filter on product name (case-insensitive).",
).strip()

st.sidebar.markdown("---")
show_lines = st.sidebar.checkbox("Show sample of filtered records", value=False)

# --------------------------------------------------------------------------- #
# Apply filters
# --------------------------------------------------------------------------- #
mask = (
    df_all["order_date"].dt.date.between(*date_range)
    & df_all["division"].isin(sel_div)
    & df_all["region"].isin(sel_region)
)
if product_search:
    mask &= df_all["product_name"].str.contains(product_search, case=False, na=False)
df = df_all[mask].copy()

if df.empty:
    st.warning("No records match the current filters. Widen the date range, "
               "division/region selection or clear the product search.")
    st.stop()

K = analytics.kpis(df)
prod_flag = analytics.flag_products(analytics.product_table(df), margin_threshold)
div_t = analytics.division_table(df)

# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
st.title("🍬 Nassau Candy Distributor — Product Line Profitability & Margin Performance")
st.caption(
    f"Live analytics over **{len(df):,}** order lines "
    f"({K['orders']:,} orders · {df['product_name'].nunique()} products) · "
    f"{date_range[0]:%d %b %Y} – {date_range[1]:%d %b %Y} · "
    f"divisions: {', '.join(sel_div) or '—'}"
)

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Sales", fmt_usd(K["sales_usd"]))
c2.metric("Gross Profit", fmt_usd(K["gross_profit_usd"]))
c3.metric("Gross Margin", f"{K['gross_margin_pct']:.1f}%",
          help="Gross Profit ÷ Sales")
c4.metric("Units Sold", f"{K['units']:,}")
c5.metric("Profit / Unit", fmt_usd(K["profit_per_unit_usd"], 2),
          help="Gross Profit ÷ Units")
n_risk = int((prod_flag["margin_flag"].isin(["At Risk", "Critical"])).sum())
c6.metric("Products at Margin Risk", n_risk,
          delta=f"threshold {margin_threshold}%", delta_color="inverse")

(tab_overview, tab_products, tab_divisions, tab_diag, tab_pareto) = st.tabs([
    "📈 Executive Overview",
    "🏆 Product Profitability",
    "🏭 Division Performance",
    "🧯 Cost vs Margin Diagnostics",
    "📊 Profit Concentration (Pareto)",
])

# --------------------------------------------------------------------------- #
# TAB 1 — Executive overview
# --------------------------------------------------------------------------- #
with tab_overview:
    left, right = st.columns([3, 2])
    mm = analytics.monthly_margin_series(df)
    with left:
        st.subheader("Monthly sales & gross margin")
        fig = go.Figure()
        fig.add_bar(x=mm["month_dt"], y=mm["sales"], name="Sales ($)",
                    marker_color="#FFD8A8")
        fig.add_scatter(x=mm["month_dt"], y=mm["gross_margin_pct"],
                        name="Gross margin (%)", yaxis="y2",
                        line=dict(color="#2B8A3E", width=2.5), mode="lines+markers")
        fig.update_layout(
            yaxis=dict(title="Sales ($)", gridcolor="#eee"),
            yaxis2=dict(title="Margin %", overlaying="y", side="right",
                        range=[0, 100], showgrid=False),
            legend=dict(orientation="h", y=1.12),
            margin=dict(l=10, r=10, t=30, b=10), height=380)
        fig.update_xaxes(dtick="M3", tickformat="%b %Y")
        st.plotly_chart(fig, width="stretch")
        st.caption("Product-level pricing is fixed per SKU in this dataset, so margin "
                   "movement is **assortment-mix driven**, not discount driven.")

    with right:
        st.subheader("Margin by region")
        reg = analytics.region_table(df).sort_values("total_sales")
        fig = px.bar(reg, x="total_sales", y="region", orientation="h",
                     color="gross_margin_pct", color_continuous_scale="YlOrBr",
                     custom_data=["gross_margin_pct", "total_gross_profit", "total_sales"],
                     labels={"total_sales": "Sales ($)", "region": "",
                             "gross_margin_pct": "Margin %"})
        fig.update_traces(
            hovertemplate="%{y}<br>Sales $%{x:,.0f}<br>Margin %{customdata[0]:.1f}%"
                          "<br>Profit $%{customdata[1]:,.0f}<extra></extra>")
        fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=250,
                          coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")
        st.dataframe(
            reg[["region", "total_sales", "total_gross_profit", "gross_margin_pct"]]
            .sort_values("total_sales", ascending=False)
            .rename(columns={"total_sales": "Sales $", "total_gross_profit": "Profit $",
                             "gross_margin_pct": "Margin %", "region": "Region"})
            .style.format({"Sales $": "${:,.0f}", "Profit $": "${:,.0f}",
                           "Margin %": "{:.1f}%"}),
            hide_index=True, width="stretch", height=180)

    st.subheader("Factory footprint & attributed margin")
    fc1, fc2 = st.columns([2, 3])
    fac = analytics.factory_table(df)
    fac_known = fac.dropna(subset=["latitude"])
    with fc1:
        fig = px.scatter_geo(fac_known, lat="latitude", lon="longitude",
                             scope="usa",
                             size="total_gross_profit", color="gross_margin_pct",
                             color_continuous_scale="RdYlGn", range_color=[0, 80],
                             hover_name="factory",
                             custom_data=["total_sales", "total_gross_profit",
                                          "gross_margin_pct"],
                             labels={"gross_margin_pct": "Margin %"},
                             size_max=42)
        fig.update_traces(
            hovertemplate="%{hovertext}<br>Sales $%{customdata[0]:,.0f}<br>"
                          "Profit $%{customdata[1]:,.0f}<br>Margin %{customdata[2]:.1f}%"
                          "<extra></extra>")
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=380,
                          coloraxis_colorbar=dict(title="Margin %"))
        st.plotly_chart(fig, width="stretch")
    with fc2:
        st.dataframe(
            fac[["factory", "total_sales", "total_gross_profit", "gross_margin_pct",
                 "profit_share_pct", "cost_ratio_pct"]]
            .rename(columns={
                "factory": "Factory", "total_sales": "Sales $",
                "total_gross_profit": "Profit $", "gross_margin_pct": "Margin %",
                "profit_share_pct": "% of Profit", "cost_ratio_pct": "Cost Ratio %"})
            .sort_values("Profit $", ascending=False)
            .style.format({"Sales $": "${:,.0f}", "Profit $": "${:,.0f}",
                           "Margin %": "{:.1f}%", "% of Profit": "{:.1f}%",
                           "Cost Ratio %": "{:.1f}%"}),
            hide_index=True, width="stretch", height=300)
        st.caption("Products attributed to the five contracted factories using the "
                   "correlation table in the project brief. **The Other Factory** "
                   "(Kazookles) drags portfolio-wide margins.")

# --------------------------------------------------------------------------- #
# TAB 2 — Product profitability
# --------------------------------------------------------------------------- #
with tab_products:
    st.subheader("Product profitability leaderboard")
    top_n = st.slider("Products shown in charts", 5, 15, 15)
    view = prod_flag.head(top_n)

    cA, cB = st.columns(2)
    with cA:
        d = view.sort_values("total_gross_profit")
        fig = px.bar(d, x="total_gross_profit", y="product_name", orientation="h",
                     color="division", color_discrete_map=DIV_COLOR,
                     custom_data=["total_sales", "gross_margin_pct", "profit_per_unit"],
                     labels={"total_gross_profit": "Gross profit ($)",
                             "product_name": "", "division": "Division"})
        fig.update_traces(hovertemplate="%{y}<br>Profit $%{x:,.0f}"
                                        "<br>Sales $%{customdata[0]:,.0f}"
                                        "<br>Margin %{customdata[1]:.1f}%"
                                        "<br>$/unit $%{customdata[2]:,.2f}<extra></extra>")
        fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=430,
                          title="Ranked by gross profit")
        st.plotly_chart(fig, width="stretch")
    with cB:
        d = view.sort_values("gross_margin_pct")
        fig = px.bar(d, x="gross_margin_pct", y="product_name", orientation="h",
                     color="division", color_discrete_map=DIV_COLOR,
                     custom_data=["total_gross_profit", "margin_flag"],
                     labels={"gross_margin_pct": "Gross margin (%)",
                             "product_name": "", "division": "Division"})
        fig.add_vline(x=margin_threshold, line_dash="dash", line_color="#C92A2A")
        fig.add_annotation(x=margin_threshold, y=1.02, yref="paper",
                           text=f"risk threshold {margin_threshold}%",
                           showarrow=False, font=dict(color="#C92A2A", size=10))
        fig.update_traces(hovertemplate="%{y}<br>Margin %{x:.1f}%"
                                        "<br>Profit $%{customdata[0]:,.0f}"
                                        "<br>Flag: %{customdata[1]}<extra></extra>")
        fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=430,
                          title="Ranked by gross margin (%)",
                          xaxis=dict(range=[0, 100]))
        st.plotly_chart(fig, width="stretch")

    st.subheader("Profit–margin quadrant map")
    q = prod_flag
    fig = px.scatter(
        q, x="gross_margin_pct", y="total_gross_profit", size="total_sales",
        color="quadrant", color_discrete_map=QUAD_COLOR, hover_name="product_name",
        custom_data=["division", "total_sales", "profit_share_pct", "recommended_action"],
        labels={"gross_margin_pct": "Gross margin (%)",
                "total_gross_profit": "Total gross profit ($)", "quadrant": "Quadrant"},
        size_max=55)
    fig.update_traces(hovertemplate="%{hovertext} (%{customdata[0]})<br>Margin %{x:.1f}%"
                                    "<br>Profit $%{y:,.0f} · Sales $%{customdata[1]:,.0f}"
                                    "<br>Profit share %{customdata[2]:.1f}%"
                                    "<br>Action: %{customdata[3]}<extra></extra>")
    fig.add_hline(y=q["total_gross_profit"].median(), line_dash="dot", line_color="gray")
    fig.add_vline(x=q["gross_margin_pct"].median(), line_dash="dot", line_color="gray")
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=460,
                      legend=dict(orientation="h", y=-0.14))
    st.plotly_chart(fig, width="stretch")
    st.caption("Quadrants split at portfolio medians — **Stars** protect profit, "
               "**Cash Traps** move volume at weak margin, **Hidden Gems** earn quietly, "
               "**Laggards** fail on both axes.")

    st.subheader("Full product table")
    show_cols = {
        "product_name": "Product", "division": "Division", "factory": "Factory",
        "total_sales": "Sales $", "total_gross_profit": "Profit $",
        "gross_margin_pct": "Margin %", "profit_per_unit": "Profit/Unit $",
        "revenue_share_pct": "Revenue %", "profit_share_pct": "Profit %",
        "quadrant": "Quadrant", "margin_flag": "Margin Flag",
        "recommended_action": "Recommended Action",
    }
    tbl = prod_flag[list(show_cols)].rename(columns=show_cols)
    st.dataframe(
        tbl.style
        .format({"Sales $": "${:,.2f}", "Profit $": "${:,.2f}", "Margin %": "{:.2f}%",
                 "Profit/Unit $": "${:,.2f}", "Revenue %": "{:.2f}%",
                 "Profit %": "{:.2f}%"})
        .map(lambda v: f"background-color:{FLAG_COLOR.get(v, '#fff')}22;"
                       f"color:{FLAG_COLOR.get(v, '#212529')};font-weight:600",
             subset=["Margin Flag"]),
        hide_index=True, width="stretch", height=420)
    st.download_button("⬇️ Download product profitability table (CSV)",
                       tbl.to_csv(index=False).encode(),
                       "product_profitability.csv", "text/csv")

# --------------------------------------------------------------------------- #
# TAB 3 — Division performance
# --------------------------------------------------------------------------- #
with tab_divisions:
    cA, cB = st.columns(2)
    with cA:
        st.subheader("Revenue vs profit by division")
        d = div_t.sort_values("total_sales")
        fig = go.Figure()
        fig.add_bar(y=d["division"], x=d["total_sales"], name="Sales", orientation="h",
                    marker_color="#D0BFFF")
        fig.add_bar(y=d["division"], x=d["total_gross_profit"], name="Gross profit",
                    orientation="h", marker_color="#5F3DC4")
        fig.update_layout(barmode="group", height=320,
                          margin=dict(l=10, r=10, t=30, b=10),
                          xaxis_title="USD", legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig, width="stretch")
        st.caption("The **Other** division takes 6.8% of revenue but only 4.6% of "
                   "profit — a 2.2 pp dilution driven by Kazookles (7.7% margin).")

    with cB:
        st.subheader("Margin distribution by division (order-line level)")
        fig = px.box(df, x="division", y="gross_margin_pct", color="division",
                     color_discrete_map=DIV_COLOR, points="outliers",
                     labels={"division": "", "gross_margin_pct": "Gross margin (%)"})
        fig.add_hline(y=K["gross_margin_pct"], line_dash="dash", line_color="#C92A2A")
        fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10),
                          showlegend=False)
        st.plotly_chart(fig, width="stretch")
        st.caption("Chocolate margins are tightly clustered (fixed price–cost ladders); "
                   "**Other** is spread wide — symptomatic of structural pricing issues.")

    cC, cD = st.columns(2)
    with cC:
        st.subheader("Share of sales vs share of profit")
        long = div_t.melt(id_vars="division",
                          value_vars=["revenue_share_pct", "profit_share_pct"],
                          var_name="measure", value_name="share")
        long["measure"] = long["measure"].map(
            {"revenue_share_pct": "Revenue share", "profit_share_pct": "Profit share"})
        fig = px.bar(long, x="division", y="share", color="measure", barmode="group",
                     color_discrete_map={"Revenue share": "#ADB5BD",
                                         "Profit share": "#E8590C"},
                     labels={"share": "Share (%)", "division": "", "measure": ""})
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=30, b=10),
                          legend=dict(orientation="h", y=1.12))
        fig.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
        st.plotly_chart(fig, width="stretch")

    with cD:
        st.subheader("Monthly margin by division (mix volatility)")
        md = analytics.monthly_margin_series(df, "division")
        fig = px.line(md, x="month_dt", y="gross_margin_pct", color="division",
                      color_discrete_map=DIV_COLOR, markers=True,
                      labels={"month_dt": "", "gross_margin_pct": "Margin %",
                              "division": ""})
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=30, b=10),
                          legend=dict(orientation="h", y=1.12))
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(fig, width="stretch")

    st.subheader("Division scorecard")
    show = div_t[["division", "total_sales", "total_gross_profit", "gross_margin_pct",
                  "revenue_share_pct", "profit_share_pct",
                  "revenue_vs_profit_imbalance_pp", "profit_per_unit",
                  "margin_volatility_std", "efficiency_class"]].rename(columns={
        "division": "Division", "total_sales": "Sales $",
        "total_gross_profit": "Profit $", "gross_margin_pct": "Margin %",
        "revenue_share_pct": "Revenue %", "profit_share_pct": "Profit %",
        "revenue_vs_profit_imbalance_pp": "Rev−Profit Imbalance (pp)",
        "profit_per_unit": "Profit/Unit $", "margin_volatility_std": "Margin σ (pp)",
        "efficiency_class": "Efficiency Class"})
    st.dataframe(show.style.format({
        "Sales $": "${:,.2f}", "Profit $": "${:,.2f}", "Margin %": "{:.2f}%",
        "Revenue %": "{:.2f}%", "Profit %": "{:.2f}%",
        "Rev−Profit Imbalance (pp)": "{:+.2f}", "Profit/Unit $": "${:,.2f}",
        "Margin σ (pp)": "{:.2f}"}), hide_index=True, width="stretch")
    st.caption("Positive imbalance = revenue over-earns vs profit (margin-dilutive). "
               "Margin σ = std-dev of monthly margin (pp) — a volatility KPI.")

# --------------------------------------------------------------------------- #
# TAB 4 — Cost vs margin diagnostics
# --------------------------------------------------------------------------- #
with tab_diag:
    st.subheader("Cost–sales scatter (order lines)")
    sample = df
    fig = px.scatter(
        sample, x="sales", y="cost", color="division", size="gross_profit",
        color_discrete_map=DIV_COLOR, hover_name="product_name", log_x=True, log_y=True,
        custom_data=["gross_margin_pct", "cost_ratio_pct", "units"],
        labels={"sales": "Sales $ (log)", "cost": "Cost $ (log)",
                "division": "Division", "gross_profit": "Profit $"},
        size_max=18, opacity=0.55)
    # break-even guides: cost = k*sales
    xs = np.logspace(np.log10(df["sales"].min()), np.log10(df["sales"].max()), 50)
    for k, lbl in [(0.5, "cost = 50%"), (0.75, "cost = 75%"), (0.95, "cost = 95%")]:
        fig.add_scatter(x=xs, y=k * xs, mode="lines", name=lbl,
                        line=dict(dash="dot", width=1), showlegend=True,
                        hoverinfo="skip")
    fig.update_traces(
        hovertemplate="%{hovertext}<br>Sales $%{x:,.2f} · Cost $%{y:,.2f}"
                      "<br>Margin %{customdata[0]:.1f}% · Cost ratio %{customdata[1]:.1f}%"
                      "<extra></extra>", selector=dict(mode="markers"))
    fig.update_layout(height=470, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, width="stretch")
    st.caption("Points riding above the 50% guide are **cost-heavy, margin-poor**. "
               "Kazookles lines sit on the 95% guide — price barely covers cost.")

    st.subheader(f"Margin-risk register  (threshold {margin_threshold}%)")
    risk = prod_flag[prod_flag["gross_margin_pct"] < margin_threshold]
    if risk.empty:
        st.success(f"No product below the {margin_threshold}% threshold. "
                   "Raise the slider to stress-test weaker SKUs.")
    else:
        st.warning(f"**{len(risk)} product(s)** below threshold require action:",
                   icon="⚠️")
        rr = risk[["product_name", "division", "factory", "total_sales",
                   "total_gross_profit", "gross_margin_pct", "cost_ratio_pct",
                   "cost_per_unit", "revenue_per_unit", "margin_flag",
                   "recommended_action"]].rename(columns={
            "product_name": "Product", "division": "Division", "factory": "Factory",
            "total_sales": "Sales $", "total_gross_profit": "Profit $",
            "gross_margin_pct": "Margin %", "cost_ratio_pct": "Cost Ratio %",
            "cost_per_unit": "Cost/Unit $", "revenue_per_unit": "Price/Unit $",
            "margin_flag": "Flag", "recommended_action": "Action"})
        st.dataframe(rr.style.format({
            "Sales $": "${:,.2f}", "Profit $": "${:,.2f}", "Margin %": "{:.2f}%",
            "Cost Ratio %": "{:.1f}%", "Cost/Unit $": "${:,.2f}",
            "Price/Unit $": "${:,.2f}"}).map(
            lambda v: f"background-color:{FLAG_COLOR.get(v, '#fff')}33;font-weight:600",
            subset=["Flag"]), hide_index=True, width="stretch")

    st.subheader("Cost structure classification")
    cd1, cd2 = st.columns(2)
    with cd1:
        heavy = prod_flag[prod_flag["cost_heavy_margin_poor"]]
        st.markdown("**Cost-heavy / margin-poor products**")
        if heavy.empty:
            st.info("None under current filters.")
        else:
            st.dataframe(
                heavy[["product_name", "cost_ratio_pct", "gross_margin_pct",
                       "recommended_action"]].rename(columns={
                    "product_name": "Product", "cost_ratio_pct": "Cost Ratio %",
                    "gross_margin_pct": "Margin %", "recommended_action": "Action"})
                .style.format({"Cost Ratio %": "{:.1f}%", "Margin %": "{:.1f}%"}),
                hide_index=True, width="stretch")
    with cd2:
        st.markdown("**Unit economics — where does a dollar go?**")
        ue = prod_flag.sort_values("total_sales", ascending=False).head(10)
        fig = go.Figure()
        fig.add_bar(y=ue["product_name"], x=ue["profit_per_unit"],
                    name="Profit / unit", orientation="h", marker_color="#2B8A3E")
        fig.add_bar(y=ue["product_name"], x=ue["cost_per_unit"],
                    name="Cost / unit", orientation="h", marker_color="#CED4DA")
        fig.update_layout(barmode="stack", height=420,
                          margin=dict(l=10, r=10, t=20, b=10),
                          xaxis_title="USD per unit",
                          yaxis=dict(autorange="reversed"),
                          legend=dict(orientation="h", y=1.08))
        st.plotly_chart(fig, width="stretch")
        st.caption("Kazookles charges $3.25/unit against a $3.00 cost — a 7.7% margin "
                   "that one ingredient-price shock would push negative.")

# --------------------------------------------------------------------------- #
# TAB 5 — Profit concentration
# --------------------------------------------------------------------------- #
with tab_pareto:
    metric = st.radio("Pareto basis", ["Gross profit", "Revenue"], horizontal=True)
    col = "gross_profit" if metric == "Gross profit" else "sales"
    ptab, ps = analytics.pareto(df, col)

    h1, h2, h3, h4, h5 = st.columns(5)
    h1.metric("Products for 80%", f"{ps['products_for_80pct']} of {ps['n_entities']}",
              delta=f"{ps['pct_products_for_80pct']}% of catalogue")
    h2.metric("Top-product share", f"{ps['top1_share_pct']}%")
    h3.metric("Top-3 share", f"{ps['top3_share_pct']}%")
    h4.metric("Top-5 share", f"{ps['top5_share_pct']}%")
    h5.metric("HHI (0–100)", f"{ps['hhi_0_100']}", delta=ps["dependency_risk"] + " dependency",
              delta_color="inverse")

    names = ptab["product_name"]
    fig = go.Figure()
    fig.add_bar(x=names, y=ptab["share_pct"], name=f"Share of {metric.lower()}",
                marker_color="#339AF0", marker_line_color="#1864AB")
    fig.add_scatter(x=names, y=ptab["cum_share_pct"], name="Cumulative share",
                    yaxis="y2", line=dict(color="#C92A2A", width=2.5),
                    mode="lines+markers")
    fig.add_hline(y=80, yref="y2", line_dash="dash", line_color="#C92A2A")
    fig.add_shape(type="line", x0=ps["products_for_80pct"] - 0.5,
                  x1=ps["products_for_80pct"] - 0.5, y0=0, y1=100, yref="y2",
                  line=dict(dash="dot", color="gray"))
    fig.update_layout(
        yaxis=dict(title="Share (%)", range=[0, max(25, ptab["share_pct"].max() * 1.1)]),
        yaxis2=dict(title="Cumulative (%)", overlaying="y", side="right",
                    range=[0, 105], showgrid=False),
        margin=dict(l=10, r=10, t=30, b=10), height=440,
        legend=dict(orientation="h", y=1.12))
    fig.update_xaxes(tickangle=60)
    st.plotly_chart(fig, width="stretch")

    cA, cB = st.columns(2)
    with cA:
        st.markdown("**Over-dependency indicators**")
        msg = (f"- **{ps['pct_products_for_80pct']}%** of products generate 80% of "
               f"{metric.lower()} — a steep 80/80 curve.\n"
               f"- The 5 Wonka Bar SKUs alone hold **{ps['top5_share_pct']}%** of "
               f"{metric.lower()}.\n"
               f"- HHI of **{ps['hhi_0_100']}** ⇒ **{ps['dependency_risk']}** "
               "concentration risk. The Chocolate division is single-point-of-failure "
               "for group profitability.")
        st.markdown(msg)
    with cB:
        st.markdown("**Geographic congestion (order-line load by state)**")
        state = (df.groupby("state_province")
                 .agg(lines=("row_id", "count"), sales=("sales", "sum"),
                      gp=("gross_profit", "sum"))
                 .sort_values("sales", ascending=False).head(8).reset_index())
        state["share_pct"] = 100 * state["sales"] / df["sales"].sum()
        fig = px.bar(state, x="state_province", y="sales",
                     color="share_pct", color_continuous_scale="OrRd",
                     custom_data=["lines", "share_pct", "gp"],
                     labels={"state_province": "", "sales": "Sales $",
                             "share_pct": "% of sales"})
        fig.update_traces(hovertemplate="%{x}<br>Sales $%{y:,.0f} "
                                        "(%{customdata[1]:.1f}%)<br>%{customdata[0]:,} "
                                        "order lines<extra></extra>")
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10),
                          coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")
        st.caption("California, New York and Texas absorb ~40% of sales — the "
                   "congestion-prone corridors where a disruption bites hardest.")

    st.dataframe(
        ptab.rename(columns={
            "product_name": "Product", "value": f"{metric} $",
            "share_pct": "Share %", "cum_share_pct": "Cumulative %",
            "entity_share_pct": "% of Catalogue"})
        .style.format({f"{metric} $": "${:,.2f}", "Share %": "{:.2f}%",
                       "Cumulative %": "{:.2f}%", "% of Catalogue": "{:.2f}%"}),
        hide_index=True, width="stretch")

# --------------------------------------------------------------------------- #
# Optional raw record viewer
# --------------------------------------------------------------------------- #
if show_lines:
    st.subheader("Filtered order lines (sample)")
    st.dataframe(df.head(500), width="stretch")

# --------------------------------------------------------------------------- #
# Footer
# --------------------------------------------------------------------------- #
st.markdown("---")
st.markdown(
    "<span class='small-note'>Data: Nassau_Candy_Distributor.csv — "
    f"{clean_report['rows_clean']:,} validated order lines "
    f"({clean_report['order_date_min']} → {clean_report['order_date_max']}). "
    "Pipeline: identity-validated (Sales − Cost = Gross Profit, "
    f"max deviation ${clean_report['identity_max_abs_deviation_usd']}), labels "
    "standardised, zero-sales/missing-unit rules enforced. "
    "Deliverables: research paper · executive summary · this dashboard. "
    "Built for Unified Mentor.</span>",
    unsafe_allow_html=True)
