"""Data cleaning & validation pipeline.

Implements every step mandated by the project brief and logs exactly what was
removed / fixed so the cleaning report can be cited in the research paper:

1. Validate cost and sales values (numeric coercion + accounting identity
   ``Sales - Cost = Gross Profit`` within a $0.02 tolerance).
2. Remove zero-sales or invalid profit records.
3. Handle missing unit values (drop rows with missing / non-positive units –
   margin-per-unit is undefined for them).
4. Standardise product and division labels
   (whitespace collapse + known fixes such as
   ``'Wonka Bar -Scrumdiddlyumptious'`` -> ``'Wonka Bar - Scrumdiddlyumptious'``).

Derived columns appended: parsed dates, calendar features, per-row
profitability metrics and the factory attribution from the brief's
product/factory correlation table.

Run as a script (``python -m src.data_prep``) to rebuild the processed CSV
and print the machine-readable cleaning report.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import config


def _std_label(value: pd.Series) -> pd.Series:
    """Trim, collapse internal whitespace and title-normalise a text column."""
    return value.astype(str).str.replace(r"\s+", " ", regex=True).str.strip()


def clean(raw_csv=config.RAW_CSV) -> tuple[pd.DataFrame, dict]:
    """Clean the raw extract. Returns (clean_df, cleaning_report)."""
    df = pd.read_csv(raw_csv)
    report: dict = {"rows_raw": int(len(df))}

    # ---- 0. standardised internal column names ---------------------------- #
    df.columns = [c.strip().lower().replace(" ", "_").replace("/", "_") for c in df.columns]

    # ---- duplicates -------------------------------------------------------- #
    dupes = int(df.duplicated().sum())
    df = df.drop_duplicates()
    report["exact_duplicates_removed"] = dupes
    report["duplicate_row_ids_removed"] = int(len(df) - len(df.drop_duplicates("row_id")))
    df = df.drop_duplicates("row_id")

    # ---- numeric coercion & validation ------------------------------------ #
    for col in ("sales", "units", "gross_profit", "cost"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    n_coerced = int(df[["sales", "units", "gross_profit", "cost"]].isna().any(axis=1).sum())
    report["rows_with_non_numeric_financials_removed"] = n_coerced
    df = df.dropna(subset=["sales", "units", "gross_profit", "cost"])

    # ---- remove zero-sales / invalid profit records ----------------------- #
    mask_valid = (
        (df["sales"] > 0)
        & (df["cost"] >= 0)
        & (df["gross_profit"] >= 0)          # gross profit must be non-negative
        & (df["gross_profit"] <= df["sales"])  # profit cannot exceed sales
    )
    report["invalid_or_zero_sales_profit_records_removed"] = int((~mask_valid).sum())
    df = df[mask_valid]

    # ---- handle missing unit values ---------------------------------------- #
    bad_units = int((df["units"] <= 0).sum())
    report["rows_with_missing_or_nonpositive_units_removed"] = bad_units
    df = df[df["units"] > 0]
    df["units"] = df["units"].round().astype(int)

    # ---- accounting identity: Sales - Cost = Gross Profit ------------------ #
    deviation = (df["sales"] - df["cost"] - df["gross_profit"]).abs()
    report["identity_tolerance_usd"] = config.IDENTITY_TOL
    report["identity_violations_removed"] = int((deviation > config.IDENTITY_TOL).sum())
    report["identity_max_abs_deviation_usd"] = round(float(deviation.max()), 6)
    df = df[deviation <= config.IDENTITY_TOL].copy()

    # ---- label standardisation -------------------------------------------- #
    for col in ("division", "region", "product_name", "ship_mode", "city",
                "state_province", "country_region"):
        df[col] = _std_label(df[col])
    before = df["product_name"].copy()
    df["product_name"] = df["product_name"].replace(config.PRODUCT_LABEL_FIXES)
    report["product_labels_standardised"] = {
        old: {"new": new, "rows_fixed": int((before == old).sum())}
        for old, new in config.PRODUCT_LABEL_FIXES.items()
    }
    report["division_labels"] = sorted(df["division"].unique().tolist())
    report["n_products_after_standardisation"] = int(df["product_name"].nunique())

    # ---- dates -------------------------------------------------------------- #
    df["order_date"] = pd.to_datetime(df["order_date"], format="%d-%m-%Y", errors="coerce")
    df["ship_date"] = pd.to_datetime(df["ship_date"], format="%d-%m-%Y", errors="coerce")
    report["unparseable_order_dates_removed"] = int(df["order_date"].isna().sum())
    df = df.dropna(subset=["order_date"]).copy()
    df["order_year"] = df["order_date"].dt.year
    df["order_quarter"] = df["order_date"].dt.to_period("Q").astype(str)
    df["order_month"] = df["order_date"].dt.to_period("M").astype(str)
    # Raw lead time kept for transparency only (ship dates run 2026-2030 in the
    # source extract - a documented source-data limitation).
    df["ship_lead_days_raw"] = (df["ship_date"] - df["order_date"]).dt.days

    # ---- factory attribution (brief's correlation table) ------------------- #
    df["factory"] = df["product_name"].map(config.PRODUCT_FACTORY).fillna("Unmapped")
    report["rows_unmapped_to_factory"] = int((df["factory"] == "Unmapped").sum())

    # ---- per-row profitability metrics -------------------------------------- #
    df["gross_margin_pct"] = 100.0 * df["gross_profit"] / df["sales"]
    df["profit_per_unit"] = df["gross_profit"] / df["units"]
    df["revenue_per_unit"] = df["sales"] / df["units"]
    df["cost_per_unit"] = df["cost"] / df["units"]
    df["cost_ratio_pct"] = 100.0 * df["cost"] / df["sales"]

    report["rows_clean"] = int(len(df))
    report["order_date_min"] = str(df["order_date"].min().date())
    report["order_date_max"] = str(df["order_date"].max().date())
    report["totals"] = {
        "sales_usd": round(float(df["sales"].sum()), 2),
        "cost_usd": round(float(df["cost"].sum()), 2),
        "gross_profit_usd": round(float(df["gross_profit"].sum()), 2),
        "units": int(df["units"].sum()),
        "overall_gross_margin_pct": round(100.0 * df["gross_profit"].sum() / df["sales"].sum(), 2),
    }
    return df.reset_index(drop=True), report


def build_processed(raw_csv=config.RAW_CSV, out_csv=config.PROCESSED_CSV) -> pd.DataFrame:
    df, report = clean(raw_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(json.dumps(report, indent=2))
    return df


if __name__ == "__main__":
    build_processed()
