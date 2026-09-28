"""Profitability metric calculations and analytical views.

All functions accept the *clean* order-line DataFrame produced by
``src.data_prep.clean`` and return analysis-ready tables used identically by
the EDA script, the research paper and the Streamlit dashboard - so every
deliverable quotes the same numbers.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config

# --------------------------------------------------------------------------- #
# Core KPI tables
# --------------------------------------------------------------------------- #

def kpis(df: pd.DataFrame) -> dict:
    """Headline KPIs for the filtered slice of data."""
    sales, cost, gp, units = (df["sales"].sum(), df["cost"].sum(),
                              df["gross_profit"].sum(), df["units"].sum())
    return {
        "sales_usd": round(sales, 2),
        "cost_usd": round(cost, 2),
        "gross_profit_usd": round(gp, 2),
        "units": int(units),
        "orders": int(df["order_id"].nunique()),
        "gross_margin_pct": round(100 * gp / sales, 2) if sales else np.nan,
        "profit_per_unit_usd": round(gp / units, 2) if units else np.nan,
    }


def _agg(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    g = df.groupby(by, observed=True).agg(
        total_sales=("sales", "sum"),
        total_cost=("cost", "sum"),
        total_gross_profit=("gross_profit", "sum"),
        total_units=("units", "sum"),
        order_lines=("row_id", "count"),
        n_orders=("order_id", "nunique"),
        avg_row_margin_pct=("gross_margin_pct", "mean"),
    ).reset_index()
    g["gross_margin_pct"] = 100 * g["total_gross_profit"] / g["total_sales"]
    g["profit_per_unit"] = g["total_gross_profit"] / g["total_units"]
    g["revenue_per_unit"] = g["total_sales"] / g["total_units"]
    g["cost_per_unit"] = g["total_cost"] / g["total_units"]
    g["cost_ratio_pct"] = 100 * g["total_cost"] / g["total_sales"]
    g["revenue_share_pct"] = 100 * g["total_sales"] / g["total_sales"].sum()
    g["profit_share_pct"] = 100 * g["total_gross_profit"] / g["total_gross_profit"].sum()
    return g


def margin_volatility(df: pd.DataFrame, by: str = "product_name") -> pd.DataFrame:
    """Variability of monthly gross margin per group (std dev & CV)."""
    monthly = (df.groupby([by, "order_month"], observed=True)
                 .agg(s=("sales", "sum"), p=("gross_profit", "sum")).reset_index())
    monthly["m"] = 100 * monthly["p"] / monthly["s"]
    out = (monthly.groupby(by, observed=True)["m"]
           .agg(margin_volatility_std="std", margin_mean="mean", months="count")
           .reset_index())
    out["margin_volatility_cv"] = out["margin_volatility_std"] / out["margin_mean"]
    return out


def product_table(df: pd.DataFrame) -> pd.DataFrame:
    """One row per product: full profitability profile + quadrant + flags."""
    t = _agg(df, ["product_name", "division", "factory"])
    t = t.merge(margin_volatility(df, "product_name"), on="product_name", how="left")

    gp_med, m_med, s_med = (t["total_gross_profit"].median(),
                            t["gross_margin_pct"].median(), t["total_sales"].median())

    def quadrant(r):
        hp, hm = r["total_gross_profit"] >= gp_med, r["gross_margin_pct"] >= m_med
        if hp and hm:
            return "Star (High Profit / High Margin)"
        if hp and not hm:
            return "Cash Trap (High Sales / Low Margin)"
        if not hp and hm:
            return "Hidden Gem (Low Profit / High Margin)"
        return "Laggard (Low Sales / Low Profit)"

    t["quadrant"] = t.apply(quadrant, axis=1)
    t["high_sales_low_margin"] = (t["total_sales"] >= s_med) & (t["gross_margin_pct"] < m_med)
    t["cost_heavy_margin_poor"] = (
        (t["cost_ratio_pct"] >= t["cost_ratio_pct"].median())
        & (t["gross_margin_pct"] < m_med))
    return t.sort_values("total_gross_profit", ascending=False).reset_index(drop=True)


def flag_products(prod: pd.DataFrame, at_risk_margin: float = config.AT_RISK_MARGIN) -> pd.DataFrame:
    """Margin-risk flag + recommended action, driven by the dashboard slider."""
    out = prod.copy()
    bands = config.MARGIN_BANDS
    conds = [
        out["gross_margin_pct"] >= bands["healthy_low"],
        out["gross_margin_pct"] >= bands["acceptable_low"],
        out["gross_margin_pct"] >= at_risk_margin,
    ]
    out["margin_flag"] = np.select(
        conds, ["Healthy", "Acceptable", "At Risk"], default="Critical")

    low_profit = out["profit_share_pct"] < max(2.0, out["profit_share_pct"].median())
    cost_heavy = out["cost_ratio_pct"] >= out["cost_ratio_pct"].median()
    action = np.select(
        [
            (out["gross_margin_pct"] < at_risk_margin)
            & (out["gross_margin_pct"] < config.DISCONTINUATION_MARGIN) & low_profit,
            (out["gross_margin_pct"] < at_risk_margin) & cost_heavy,
            out["gross_margin_pct"] < at_risk_margin,
            out["cost_ratio_pct"] >= config.REPRICE_COST_RATIO,
        ],
        ["Discontinuation Review", "Cost Renegotiation", "Repricing Needed",
         "Cost Renegotiation"],
        default="Maintain / Grow",
    )
    out["recommended_action"] = action
    return out


def division_table(df: pd.DataFrame) -> pd.DataFrame:
    """Division-level financial efficiency view."""
    t = _agg(df, ["division"])
    t["revenue_vs_profit_imbalance_pp"] = t["revenue_share_pct"] - t["profit_share_pct"]
    t = t.merge(margin_volatility(df, "division"), on="division", how="left")
    med = t["gross_margin_pct"].median()
    t["efficiency_class"] = np.where(
        t["gross_margin_pct"] >= med, "Strong Financial Efficiency",
        "Structural Margin Issues")
    return t.sort_values("total_gross_profit", ascending=False).reset_index(drop=True)


def region_table(df: pd.DataFrame) -> pd.DataFrame:
    t = _agg(df, ["region"])
    t["revenue_vs_profit_imbalance_pp"] = t["revenue_share_pct"] - t["profit_share_pct"]
    return t.sort_values("total_gross_profit", ascending=False).reset_index(drop=True)


def factory_table(df: pd.DataFrame) -> pd.DataFrame:
    t = _agg(df, ["factory"])
    coords = pd.DataFrame(
        [{"factory": k, **v} for k, v in config.FACTORIES.items()])
    return t.merge(coords, on="factory", how="left")


# --------------------------------------------------------------------------- #
# Pareto / concentration analysis
# --------------------------------------------------------------------------- #

def pareto(df: pd.DataFrame, value_col: str, by: str = "product_name") -> tuple[pd.DataFrame, dict]:
    """Cumulative-share Pareto table + concentration indicators."""
    t = df.groupby(by, observed=True)[value_col].sum().sort_values(ascending=False)
    t = t.rename("value").reset_index()
    total = t["value"].sum()
    t["share_pct"] = 100 * t["value"] / total
    t["cum_share_pct"] = t["share_pct"].cumsum()
    t["entity_share_pct"] = 100 * (np.arange(len(t)) + 1) / len(t)

    n80 = int((t["cum_share_pct"] < 100 * config.PARETO_TARGET).sum() + 1)
    shares = t["share_pct"].to_numpy()
    hhi = float((shares ** 2).sum() / 100)  # 0-100 scale (HHI/100)
    summary = {
        "n_entities": int(len(t)),
        "products_for_80pct": n80,
        "pct_products_for_80pct": round(100 * n80 / len(t), 1),
        "top1_share_pct": round(shares[0], 1),
        "top3_share_pct": round(shares[:3].sum(), 1),
        "top5_share_pct": round(shares[:5].sum(), 1),
        "hhi_0_100": round(hhi, 2),
        "dependency_risk": ("High" if hhi >= 18 else "Moderate" if hhi >= 10 else "Low"),
    }
    return t, summary


def monthly_margin_series(df: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    keys = ["order_month"] + ([by] if by else [])
    m = (df.groupby(keys, observed=True)
           .agg(sales=("sales", "sum"), gross_profit=("gross_profit", "sum"))
           .reset_index())
    m["gross_margin_pct"] = 100 * m["gross_profit"] / m["sales"]
    m["month_dt"] = pd.to_datetime(m["order_month"])
    return m.sort_values("month_dt")
