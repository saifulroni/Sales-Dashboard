"""
Superstore Sales Analysis
-------------------------
Reproduces the numbers shown in the Power BI dashboard, cleans the raw data,
and generates the supporting charts used in docs/PROJECT_REPORT.md.

Run from the repository root:
    python analysis/sales_analysis.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "SuperStore_Sales_Dataset.csv"
OUT_DATA = ROOT / "data" / "processed"
OUT_IMG = ROOT / "images"
OUT_DATA.mkdir(parents=True, exist_ok=True)
OUT_IMG.mkdir(parents=True, exist_ok=True)

BLUE, ORANGE, RED, GREY = "#118DFF", "#E8956B", "#D64550", "#8A94A6"
plt.rcParams.update(
    {
        "figure.dpi": 140,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titleweight": "bold",
        "font.size": 10,
    }
)


# ----------------------------------------------------------------------------
# 1. LOAD & CLEAN
# ----------------------------------------------------------------------------
def load_and_clean() -> pd.DataFrame:
    # utf-8-sig strips the BOM; the first header also carries an Excel artefact
    df = pd.read_csv(RAW, encoding="utf-8-sig")
    df = df.rename(columns={df.columns[0]: "Row ID"})

    # Drop the two completely empty helper columns left over from Excel
    df = df.drop(columns=[c for c in ("ind1", "ind2") if c in df.columns])

    # Dates are stored day-first (e.g. 7/1/2019 = 7 January 2019)
    for col in ("Order Date", "Ship Date"):
        df[col] = pd.to_datetime(df[col], format="%d/%m/%Y")

    # 'Returns' is 1 for returned lines and blank otherwise -> make explicit flag
    df["Returned"] = df["Returns"].fillna(0).astype(int)
    df = df.drop(columns="Returns")

    # Derived fields (mirrors the AvgShipDay calculated column in Power BI)
    df["Ship Days"] = (df["Ship Date"] - df["Order Date"]).dt.days
    df["Year"] = df["Order Date"].dt.year
    df["Month"] = df["Order Date"].dt.month
    df["Month Name"] = df["Order Date"].dt.month_name()
    df["Quarter"] = "Q" + df["Order Date"].dt.quarter.astype(str)
    df["Profit Margin %"] = (df["Profit"] / df["Sales"] * 100).round(2)
    df["Loss Making"] = (df["Profit"] < 0).astype(int)
    return df


def safe_ratio(a, b):
    return a / b if b else float("nan")


def summarise(df: pd.DataFrame, by: str) -> pd.DataFrame:
    g = (
        df.groupby(by)
        .agg(
            Sales=("Sales", "sum"),
            Profit=("Profit", "sum"),
            Units=("Quantity", "sum"),
            Orders=("Order ID", "nunique"),
        )
        .sort_values("Sales", ascending=False)
    )
    g["Margin %"] = (g["Profit"] / g["Sales"] * 100).round(1)
    g["Sales Share %"] = (g["Sales"] / g["Sales"].sum() * 100).round(1)
    return g.round(2)


# ----------------------------------------------------------------------------
# 2. KPI VALIDATION  (dashboard vs. raw data)
# ----------------------------------------------------------------------------
def kpis(df: pd.DataFrame) -> pd.DataFrame:
    k = {
        "Total Sales": df["Sales"].sum(),
        "Total Profit": df["Profit"].sum(),
        "Profit Margin %": df["Profit"].sum() / df["Sales"].sum() * 100,
        "Units Sold": df["Quantity"].sum(),
        "Unique Orders": df["Order ID"].nunique(),
        "Unique Customers": df["Customer ID"].nunique(),
        "Avg Order Value": df.groupby("Order ID")["Sales"].sum().mean(),
        "Avg Delivery Days": df["Ship Days"].mean(),
        "Returned Lines": int(df["Returned"].sum()),
        "Returned Sales": df.loc[df["Returned"] == 1, "Sales"].sum(),
        "Loss-making Lines": int(df["Loss Making"].sum()),
        "Losses from those lines": df.loc[df["Profit"] < 0, "Profit"].sum(),
    }
    return pd.DataFrame({"Value": k}).round(2)


# ----------------------------------------------------------------------------
# 3. CHARTS
# ----------------------------------------------------------------------------
def fmt_k(x, _=None):
    return f"{x/1000:,.0f}K"


def chart_yoy(df):
    m = df.pivot_table(index="Month", columns="Year", values="Sales", aggfunc="sum")
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(labels, m[2019], marker="o", color=BLUE, label="2019")
    ax.plot(labels, m[2020], marker="o", color=ORANGE, label="2020")
    ax.yaxis.set_major_formatter(fmt_k)
    ax.set_title("Monthly Sales: 2019 vs 2020")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT_IMG / "01_monthly_sales_yoy.png")
    plt.close(fig)


def chart_category_margin(df):
    g = summarise(df, "Category")
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(g.index, g["Margin %"], color=[BLUE, ORANGE, RED])
    ax.bar_label(bars, fmt="%.1f%%")
    ax.set_title("Profit Margin by Category")
    ax.set_ylabel("Margin %")
    fig.tight_layout()
    fig.savefig(OUT_IMG / "02_category_margin.png")
    plt.close(fig)


def chart_subcat_profit(df):
    g = summarise(df, "Sub-Category").sort_values("Profit")
    colors = [RED if v < 0 else BLUE for v in g["Profit"]]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(g.index, g["Profit"], color=colors)
    ax.xaxis.set_major_formatter(fmt_k)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_title("Total Profit by Sub-Category")
    fig.tight_layout()
    fig.savefig(OUT_IMG / "03_subcategory_profit.png")
    plt.close(fig)


def chart_state(df):
    g = df.groupby("State").agg(Sales=("Sales", "sum"), Profit=("Profit", "sum")).sort_values("Sales", ascending=False).head(12)
    x = range(len(g))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    w = 0.4
    ax.bar([i - w / 2 for i in x], g["Sales"], w, color=BLUE, label="Sales")
    ax.bar([i + w / 2 for i in x], g["Profit"], w, color=[RED if p < 0 else ORANGE for p in g["Profit"]], label="Profit")
    ax.set_xticks(list(x))
    ax.set_xticklabels(g.index, rotation=40, ha="right")
    ax.yaxis.set_major_formatter(fmt_k)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title("Top 12 States: Sales vs Profit (red = loss-making)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT_IMG / "04_state_sales_vs_profit.png")
    plt.close(fig)


def chart_region(df):
    g = summarise(df, "Region")
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.8))
    axes[0].bar(g.index, g["Sales"], color=BLUE)
    axes[0].yaxis.set_major_formatter(fmt_k)
    axes[0].set_title("Sales by Region")
    bars = axes[1].bar(g.index, g["Margin %"], color=ORANGE)
    axes[1].bar_label(bars, fmt="%.1f%%")
    axes[1].set_title("Profit Margin by Region")
    fig.tight_layout()
    fig.savefig(OUT_IMG / "05_region_sales_margin.png")
    plt.close(fig)


def chart_heatmap(df):
    p = df.pivot_table(index="Region", columns="Category", values="Profit", aggfunc="sum")
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    im = ax.imshow(p.values, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(range(len(p.columns)), p.columns)
    ax.set_yticks(range(len(p.index)), p.index)
    for i in range(p.shape[0]):
        for j in range(p.shape[1]):
            ax.text(j, i, f"{p.values[i, j]:,.0f}", ha="center", va="center", fontsize=9)
    ax.set_title("Profit by Region x Category")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(OUT_IMG / "06_region_category_heatmap.png")
    plt.close(fig)


def main():
    df = load_and_clean()
    df.to_csv(OUT_DATA / "superstore_clean.csv", index=False)

    kpis(df).to_csv(OUT_DATA / "kpi_summary.csv")
    for dim in ("Region", "Category", "Sub-Category", "Segment", "Ship Mode", "Payment Mode", "State", "Year"):
        summarise(df, dim).to_csv(OUT_DATA / f"summary_by_{dim.lower().replace('-', '_').replace(' ', '_')}.csv")

    chart_yoy(df)
    chart_category_margin(df)
    chart_subcat_profit(df)
    chart_state(df)
    chart_region(df)
    chart_heatmap(df)

    print(kpis(df).to_string())
    print(f"\nClean rows: {len(df):,} | Date range: {df['Order Date'].min().date()} to {df['Order Date'].max().date()}")
    print(f"Charts saved to {OUT_IMG}")


if __name__ == "__main__":
    main()
