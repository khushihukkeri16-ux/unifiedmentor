# Executive Summary
## Nassau Candy Distributor — Product Line Profitability & Margin Performance

**Scope:** 10,194 validated order lines · 8,549 orders · 15 products · FY2024–FY2025 ·
US & Canada. Full methodology and evidence: `reports/research_paper.md`. Live
monitoring: the Streamlit dashboard (`streamlit run app/streamlit_app.py`).

---

### The numbers that matter

| Measure | Result |
|---|---|
| Sales (FY24–25) | **$141,784** (+44.6% YoY) |
| Gross profit | **$93,443** |
| Gross margin | **65.9%** (flat YoY, +0.13 pp) |
| Units | 38,654 (+43.1% YoY) |
| Profit concentration | **5 of 15 products = 95.1% of profit** (HHI 18.3 → *High*) |
| Structural risk products | **1 (Kazookles, 7.7% margin)** |

### Five things stakeholders should know

1. **The business is healthy and growing.** Revenue +44.6%, profit +44.9% YoY with
   zero margin erosion — a repeatable, margin-accretive growth engine.
2. **Profit rides on a very narrow base.** Five Chocolate "Wonka Bar" SKUs fund 95%
   of gross profit; one supplier, capacity or cocoa-price shock would touch the whole
   P&L. Dependency is rated **High** and should be formally monitored quarterly.
3. **One product is structurally broken.** *Kazookles* earns **$0.25 per $3.25 unit**
   (7.7% margin, costs consume 92.3% of its price) and its volume is still growing —
   growth that *reduces* blended margin. It is the audit case for "looks successful,
   weakens margins."
4. **The Other division dilutes the group.** It books 6.8% of revenue but keeps only
   4.6% of profit (44.8% margin): Kazookles plus a hard 2×-cost pricing ceiling on
   its two premium SKUs (Lickable Wallpaper, Wonka Gum).
5. **There is an unexploited high-margin bench.** Pilot Sugar SKUs (Everlasting
   Gobstopper 80%, Hair Toffee 78%, Laffy Taffy 62%) out-margin every Wonka bar but
   run at <0.3% of revenue — upside waiting on distribution, not on product fixes.

### Decisions requested

| # | Decision | Expected effect |
|---|---|---|
| 1 | Approve **Kazookles 90-day fix-or-exit**: renegotiate cost from $3.00 or reprice from $3.25 toward ≥$4.50; discontinue if 25% margin unreachable | Removes the only structurally loss-adjacent SKU (impact on profit: ≤0.1%) |
| 2 | Authorise **cost-ceiling renegotiation** on Lickable Wallpaper / Wonka Gum (target cost ratio ≤45%) | ≈$170/yr added profit at current volume; more as premium grows |
| 3 | Fund **Sugar-pilot distribution expansion** (Gobstopper, Hair Toffee, Laffy Taffy) | Diversifies the profit base at margins *above* the Chocolate core |
| 4 | Adopt **concentration watch-KPIs** (top-5 SKU profit share, Chocolate division share, factory load at Lot's O' Nuts) with quarterly review | Early warning on the portfolio's single point of failure |

### Monitoring assets handed over

- **Live dashboard** — product leaderboard, division scorecard, cost–margin risk
  register (threshold slider), Pareto dependency view, factory map; filterable by
  date, division, region and product.
- **Reproducible pipeline** — one-command cleaning with machine-readable validation
  report (10,194/10,194 rows pass; Sales − Cost = Gross Profit holds exactly).
- **Research paper** — complete EDA, quadrant/Pareto/cost-diagnostics methodology and
  recommendation register.

*Bottom line: protect the chocolate franchise, fix or exit one broken SKU, and grow
the high-margin bench — Nassau Candy can convert strong growth into stronger margins
with three surgical decisions.*
