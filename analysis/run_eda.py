"""Generate every figure and table quoted in the research paper.

Reads the clean dataset via `src` (single source of truth), writes PNG charts
to reports/figures/ and CSV tables to reports/tables/. Run:
    python3 analysis/run_eda.py
"""
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import analytics, config, data_prep  # noqa: E402

plt.rcParams.update({
    "figure.dpi": 130, "font.size": 10, "axes.titlesize": 12,
    "axes.titleweight": "bold", "axes.grid": True, "grid.alpha": 0.25,
    "axes.spines.top": False, "axes.spines.right": False,
})
PALETTE = {"Chocolate": "#8B5A2B", "Sugar": "#E8590C", "Other": "#1864AB"}
FIG = config.FIGURES_DIR
TAB = config.REPORTS_DIR / "tables"


def short(name: str) -> str:
    return (name.replace("Wonka Bar - ", "WB: ").replace("Chocolate", "Choc"))


def fig_product_margin_bar(pt: pd.DataFrame, kpi: dict):
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    d = pt.sort_values("gross_margin_pct")
    colors = [PALETTE[x] for x in d["division"]]
    ax.barh([short(p) for p in d["product_name"]], d["gross_margin_pct"], color=colors)
    ax.axvline(kpi["gross_margin_pct"], color="#C92A2A", ls="--", lw=1.4)
    ax.text(kpi["gross_margin_pct"] + 0.6, 0.2,
            f"Portfolio avg {kpi['gross_margin_pct']:.1f}%", color="#C92A2A", fontsize=9)
    for y, (v, gp) in enumerate(zip(d["gross_margin_pct"], d["total_gross_profit"])):
        ax.text(v + 0.6, y, f"{v:.1f}%  (${gp:,.0f} GP)", va="center", fontsize=8.5)
    ax.set_xlim(0, 105)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_xlabel("Gross margin (% of sales)")
    ax.set_title("Gross margin by product — profit dollars annotated")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in PALETTE.values()]
    ax.legend(handles, PALETTE.keys(), loc="lower right", frameon=False, title="Division")
    fig.tight_layout()
    fig.savefig(FIG / "fig1_product_margin.png")
    plt.close(fig)


def fig_product_quadrant(pt: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9.5, 6))
    gp_med, m_med = pt["total_gross_profit"].median(), pt["gross_margin_pct"].median()
    for div, sub in pt.groupby("division"):
        ax.scatter(sub["gross_margin_pct"], sub["total_gross_profit"],
                   s=np.clip(sub["total_sales"] / 35, 25, 900),
                   color=PALETTE[div], alpha=0.75, label=div, edgecolors="white")
    # deterministic label placement to avoid collisions in the Star cluster
    offsets = {
        "Wonka Bar - Scrumdiddlyumptious": (-10, 22),
        "Wonka Bar - Triple Dazzle Caramel": (-95, -30),
        "Wonka Bar - Milk Chocolate": (-80, 18),
        "Wonka Bar - Nutty Crunch Surprise": (12, -6),
        "Wonka Bar - Fudge Mallows": (-60, -34),
    }
    for _, r in pt.iterrows():
        ax.annotate(short(r["product_name"]), (r["gross_margin_pct"], r["total_gross_profit"]),
                    textcoords="offset points",
                    xytext=offsets.get(r["product_name"], (6, 5)), fontsize=8)
    ax.axvline(m_med, color="gray", ls=":", lw=1)
    ax.axhline(gp_med, color="gray", ls=":", lw=1)
    ax.text(0.99, 0.02, "Cash Trap\n(high sales, low margin)", transform=ax.transAxes,
            ha="right", fontsize=8.5, color="#495057")
    ax.text(0.01, 0.96, "Hidden Gem\n(high margin, low profit)", transform=ax.transAxes,
            fontsize=8.5, color="#495057")
    ax.text(0.99, 0.96, "Star\n(high profit, high margin)", transform=ax.transAxes,
            ha="right", fontsize=8.5, color="#495057")
    ax.xaxis.set_major_formatter(mtick.PercentFormatter())
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.0f}"))
    ax.set_xlabel("Gross margin (%)")
    ax.set_ylabel("Total gross profit ($)  —  bubble size = total sales")
    ax.set_title("Product profitability quadrant map")
    ax.legend(frameon=False, title="Division", loc="center left")
    fig.tight_layout()
    fig.savefig(FIG / "fig2_product_quadrant.png")
    plt.close(fig)


def fig_division_panel(dt: pd.DataFrame):
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.2))
    order = dt.sort_values("total_sales", ascending=False)
    colors = [PALETTE[d] for d in order["division"]]
    x = np.arange(len(order))
    w = 0.38
    axes[0].bar(x - w / 2, order["total_sales"], w, label="Sales", color=colors, alpha=0.55)
    axes[0].bar(x + w / 2, order["total_gross_profit"], w, label="Gross profit", color=colors)
    axes[0].set_xticks(x, order["division"])
    axes[0].yaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.0f}"))
    axes[0].set_title("Revenue vs profit")
    axes[0].legend(frameon=False, fontsize=8)

    axes[1].bar(order["division"], order["gross_margin_pct"], color=colors)
    axes[1].axhline(65.91, color="#C92A2A", ls="--", lw=1.2)
    axes[1].text(2.0, 66.6, "portfolio 65.9%", color="#C92A2A", fontsize=8)
    for i, v in enumerate(order["gross_margin_pct"]):
        axes[1].text(i, v + 1, f"{v:.1f}%", ha="center", fontsize=9, fontweight="bold")
    axes[1].set_ylim(0, 85)
    axes[1].yaxis.set_major_formatter(mtick.PercentFormatter())
    axes[1].set_title("Gross margin by division")

    axes[2].bar(order["division"], order["revenue_share_pct"], color="#ADB5BD",
                label="Revenue share")
    axes[2].bar(order["division"], order["profit_share_pct"], color=colors,
                alpha=0.85, label="Profit share")
    axes[2].yaxis.set_major_formatter(mtick.PercentFormatter())
    axes[2].set_title("Revenue vs profit share")
    axes[2].legend(frameon=False, fontsize=8)
    fig.suptitle("Division-level financial performance", fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG / "fig3_division_panel.png", bbox_inches="tight")
    plt.close(fig)


def fig_pareto(pr: pd.DataFrame, pp: pd.DataFrame, rs: dict, ps: dict):
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6), sharex=False)
    for ax, d, summ, label, color in (
            (axes[0], pr, rs, "Revenue", "#1864AB"), (axes[1], pp, ps, "Gross profit", "#2B8A3E")):
        names = [short(p) for p in d["product_name"]]
        ax.bar(names, d["share_pct"], color=color, alpha=0.8)
        ax2 = ax.twinx()
        ax2.plot(names, d["cum_share_pct"], color="#C92A2A", marker="o", ms=4)
        ax2.axhline(80, color="#C92A2A", ls="--", lw=1)
        ax2.axvline(summ["products_for_80pct"] - 0.5, color="gray", ls=":", lw=1)
        ax2.text(0.02, 0.02,
                 f"{summ['products_for_80pct']} of {summ['n_entities']} products "
                 f"({summ['pct_products_for_80pct']}%) = 80% of {label.lower()}",
                 transform=ax2.transAxes, fontsize=8.5,
                 bbox=dict(fc="white", ec="gray", alpha=0.85))
        ax.set_xticks(range(len(names)), names, rotation=60, ha="right", fontsize=7.5)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
        ax2.set_ylim(0, 105)
        ax.grid(False)
        ax.set_ylabel("Share of " + label.lower())
        ax2.set_ylabel("Cumulative share")
        ax.set_title(f"{label} Pareto  (HHI = {summ['hhi_0_100']}, "
                     f"{summ['dependency_risk']} dependency)")
    fig.suptitle("Profit concentration (Pareto) analysis", fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG / "fig4_pareto.png", bbox_inches="tight")
    plt.close(fig)


def fig_cost_scatter(df: pd.DataFrame, pt: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9.5, 6))
    rng = np.random.default_rng(7)
    for div, sub in df.groupby("division"):
        ax.scatter(sub["sales"], sub["cost_ratio_pct"], s=10, alpha=0.25,
                   color=PALETTE[div], label=f"{div} order lines")
    label_xy = {
        "Wonka Bar - Milk Chocolate": (12, 10),
        "Wonka Bar - Triple Dazzle Caramel": (-175, 16),
        "Wonka Bar - Fudge Mallows": (-30, -22),
        "Wonka Bar - Scrumdiddlyumptious": (-150, -26),
        "Wonka Bar - Nutty Crunch Surprise": (-92, -38),
    }
    for _, r in pt.iterrows():
        dy = rng.uniform(-1.2, 1.2)
        ax.annotate(short(r["product_name"]), (r["total_sales"], r["cost_ratio_pct"]),
                    textcoords="offset points",
                    xytext=label_xy.get(r["product_name"], (6, dy * 4)), fontsize=8,
                    fontweight="bold", color="#212529")
        ax.scatter(r["total_sales"], r["cost_ratio_pct"], s=60, marker="D",
                   facecolors="none", edgecolors="#C92A2A", linewidths=1.4, zorder=5)
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.0f}"))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.axhline(50, color="gray", ls="--", lw=1)
    ax.text(df["sales"].min() * 1.05, 52, "cost = 50% of sales", fontsize=8, color="#495057")
    ax.set_xlabel("Sales ($, log scale)")
    ax.set_ylabel("Cost ratio (Cost ÷ Sales, %)")
    ax.set_title("Cost structure diagnostics — order lines (dots) & product totals (red diamonds)")
    ax.legend(frameon=False, loc="upper right", markerscale=2)
    fig.tight_layout()
    fig.savefig(FIG / "fig5_cost_scatter.png")
    plt.close(fig)


def fig_monthly(df: pd.DataFrame):
    mm = analytics.monthly_margin_series(df)
    md = analytics.monthly_margin_series(df, "division")
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.2))
    axes[0].plot(mm["month_dt"], mm["gross_margin_pct"], marker="o", ms=3.5,
                 color="#2B8A3E", label="Gross margin %")
    axb = axes[0].twinx()
    axb.bar(mm["month_dt"], mm["sales"], width=22, color="#ADB5BD", alpha=0.6, label="Sales $")
    axes[0].yaxis.set_major_formatter(mtick.PercentFormatter())
    axes[0].set_ylim(60, 70)
    axb.yaxis.set_major_formatter(mtick.StrMethodFormatter("${x:,.0f}"))
    axb.grid(False)
    axes[0].set_title("Monthly margin vs sales (portfolio)")
    axes[0].set_ylabel("Gross margin %")
    axb.set_ylabel("Sales $")

    for div, sub in md.groupby("division"):
        axes[1].plot(sub["month_dt"], sub["gross_margin_pct"], marker="o", ms=3,
                     label=div, color=PALETTE[div])
    axes[1].yaxis.set_major_formatter(mtick.PercentFormatter())
    axes[1].set_title("Monthly margin by division (mix-driven volatility)")
    for ax in axes:
        ax.tick_params(axis="x", rotation=45)
    axes[1].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "fig6_monthly_margin.png")
    plt.close(fig)


def fig_factory(ft: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    d = ft.dropna(subset=["latitude"]).sort_values("gross_margin_pct")
    ax.barh(d["factory"], d["gross_margin_pct"], color="#5F3DC4")
    for y, (v, pshare, f) in enumerate(zip(d["gross_margin_pct"], d["profit_share_pct"],
                                           d["factory"])):
        ax.text(v + 0.8, y, f"{v:.1f}% margin · {pshare:.1f}% of profit", va="center",
                fontsize=9)
    ax.set_xlim(0, 95)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_xlabel("Gross margin of attributed products (%)")
    ax.set_title("Factory-level margin profile (products attributed per brief mapping)")
    fig.tight_layout()
    fig.savefig(FIG / "fig7_factory_margin.png")
    plt.close(fig)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    df, report = data_prep.clean()
    kpi = analytics.kpis(df)
    pt = analytics.flag_products(analytics.product_table(df))
    dt = analytics.division_table(df)
    ft = analytics.factory_table(df)
    pr, rs = analytics.pareto(df, "sales")
    pp, ps = analytics.pareto(df, "gross_profit")

    fig_product_margin_bar(pt, kpi)
    fig_product_quadrant(pt)
    fig_division_panel(dt)
    fig_pareto(pr, pp, rs, ps)
    fig_cost_scatter(df, pt)
    fig_monthly(df)
    fig_factory(ft)

    pt.round(4).to_csv(TAB / "product_profitability.csv", index=False)
    dt.round(4).to_csv(TAB / "division_performance.csv", index=False)
    ft.round(4).to_csv(TAB / "factory_performance.csv", index=False)
    pr.round(4).to_csv(TAB / "pareto_revenue.csv", index=False)
    pp.round(4).to_csv(TAB / "pareto_profit.csv", index=False)
    analytics.region_table(df).round(4).to_csv(TAB / "region_performance.csv", index=False)
    print("figures ->", FIG)
    print("tables  ->", TAB)
    for f in sorted(FIG.glob("*.png")):
        print(" ", f.name)


if __name__ == "__main__":
    main()
