"""
analytics.py - Automatic chart and insight generation
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import io
import base64


PALETTE = ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
           "#EC4899", "#14B8A6", "#F97316"]


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def auto_charts(df: pd.DataFrame) -> list[dict]:
    """
    Returns a list of {title, img_b64} dicts.
    Generates the most relevant charts automatically.
    """
    charts = []
    num_cols  = df.select_dtypes(include="number").columns.tolist()
    cat_cols  = df.select_dtypes(include="object").columns.tolist()
    date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

    plt.style.use("seaborn-v0_8-whitegrid")
    bg = "#F8FAFC"

    # ── Bar chart: top category by best numeric column ───────────
    if cat_cols and num_cols:
        cat = cat_cols[0]
        val = _best_value_col(df, num_cols)
        top = df.groupby(cat)[val].sum().nlargest(10).sort_values()
        fig, ax = plt.subplots(figsize=(7, 4), facecolor=bg)
        ax.set_facecolor(bg)
        bars = ax.barh(top.index, top.values, color=PALETTE[:len(top)], edgecolor="none")
        ax.set_title(f"{val.replace('_',' ').title()} by {cat.replace('_',' ').title()}",
                     fontsize=13, fontweight="bold", pad=12)
        ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.tick_params(labelsize=9)
        fig.tight_layout()
        charts.append({"title": f"Top {cat.replace('_',' ').title()} by {val.replace('_',' ').title()}",
                       "img": _fig_to_base64(fig)})
        plt.close(fig)

    # ── Line chart: trend over time ──────────────────────────────
    if date_cols and num_cols:
        d = date_cols[0]
        v = _best_value_col(df, num_cols)
        trend = df.groupby(df[d].dt.to_period("M"))[v].sum().reset_index()
        trend[d] = trend[d].dt.to_timestamp()
        fig, ax = plt.subplots(figsize=(7, 4), facecolor=bg)
        ax.set_facecolor(bg)
        ax.plot(trend[d], trend[v], color=PALETTE[0], linewidth=2.5, marker="o", markersize=4)
        ax.fill_between(trend[d], trend[v], alpha=0.12, color=PALETTE[0])
        ax.set_title(f"{v.replace('_',' ').title()} Over Time",
                     fontsize=13, fontweight="bold", pad=12)
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        fig.autofmt_xdate()
        fig.tight_layout()
        charts.append({"title": f"{v.replace('_',' ').title()} Trend",
                       "img": _fig_to_base64(fig)})
        plt.close(fig)

    # ── Pie chart: second category if exists ─────────────────────
    if len(cat_cols) >= 2 and num_cols:
        cat = cat_cols[1]
        val = _best_value_col(df, num_cols)
        pie_data = df.groupby(cat)[val].sum().nlargest(6)
        if len(pie_data) >= 2:
            fig, ax = plt.subplots(figsize=(6, 4), facecolor=bg)
            ax.set_facecolor(bg)
            wedges, texts, autotexts = ax.pie(
                pie_data.values,
                labels=pie_data.index,
                autopct="%1.1f%%",
                colors=PALETTE[:len(pie_data)],
                startangle=140,
                pctdistance=0.82
            )
            for t in autotexts:
                t.set_fontsize(8)
            ax.set_title(f"{cat.replace('_',' ').title()} Share",
                         fontsize=13, fontweight="bold", pad=12)
            fig.tight_layout()
            charts.append({"title": f"{cat.replace('_',' ').title()} Distribution",
                           "img": _fig_to_base64(fig)})
            plt.close(fig)

    # ── Distribution histogram ────────────────────────────────────
    if num_cols:
        v = _best_value_col(df, num_cols)
        fig, ax = plt.subplots(figsize=(7, 4), facecolor=bg)
        ax.set_facecolor(bg)
        ax.hist(df[v].dropna(), bins=20, color=PALETTE[4], edgecolor="white", alpha=0.85)
        ax.set_title(f"Distribution of {v.replace('_',' ').title()}",
                     fontsize=13, fontweight="bold", pad=12)
        ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        fig.tight_layout()
        charts.append({"title": f"{v.replace('_',' ').title()} Distribution",
                       "img": _fig_to_base64(fig)})
        plt.close(fig)

    return charts


def quick_stats(df: pd.DataFrame) -> dict:
    """Return key headline KPIs from the dataset."""
    stats = {}
    num_cols = df.select_dtypes(include="number").columns.tolist()

    if num_cols:
        v = _best_value_col(df, num_cols)
        stats["total"]   = df[v].sum()
        stats["average"] = df[v].mean()
        stats["max_val"] = df[v].max()
        stats["min_val"] = df[v].min()
        stats["metric_name"] = v.replace("_", " ").title()

    stats["rows"]    = len(df)
    stats["columns"] = len(df.columns)
    return stats


def _best_value_col(df, num_cols):
    """Prefer revenue/sales/total/amount columns, else first numeric."""
    preferred = ["total_revenue", "revenue", "sales", "amount", "total",
                 "total_sales", "price", "value"]
    for p in preferred:
        if p in num_cols:
            return p
    return num_cols[0]