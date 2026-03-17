import pandas as pd
import plotly.express as px

def _best_col(df):
    num_cols = df.select_dtypes(include="number").columns.tolist()
    num_cols = [c for c in num_cols if not any(k in c for k in ["id","index","row"])]
    preferred = ["total_sales","total_revenue","revenue","sales","amount","total"]
    return next((c for c in preferred if c in num_cols), num_cols[0] if num_cols else None)

def _best_cat(df):
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    skip = ["date","time","id","code","currency","unknown","name_id"]
    cat_cols = [c for c in cat_cols if not any(k in c.lower() for k in skip)]
    preferred = ["product_name","category","region","product","type","segment"]
    return next((c for c in preferred if c in cat_cols), cat_cols[0] if cat_cols else None)

def quick_stats(df):
    stats = {}
    val = _best_col(df)
    if val:
        stats["total"] = df[val].sum()
        stats["average"] = df[val].mean()
        stats["max_val"] = df[val].max()
        stats["min_val"] = df[val].min()
        stats["metric_name"] = val.replace("_"," ").title()
    stats["rows"] = len(df)
    stats["columns"] = len(df.columns)
    return stats

def auto_charts(df):
    charts = []
    val = _best_col(df)
    cat = _best_cat(df)
    date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

    if not val:
        return charts

    COLORS = ["#2563EB","#10B981","#F59E0B","#EF4444","#8B5CF6",
              "#EC4899","#14B8A6","#F97316","#06B6D4","#84CC16"]

    if cat:
        grouped = df.groupby(cat)[val].sum().nlargest(10).reset_index()
        grouped.columns = [cat, val]
        fig = px.bar(
            grouped, x=val, y=cat, orientation="h",
            title=f"{val.replace('_',' ').title()} by {cat.replace('_',' ').title()}",
            color=cat, color_discrete_sequence=COLORS, text=val
        )
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter, sans-serif", size=12, color="#1E293B"),
            title=dict(font=dict(size=14, color="#1E293B"), x=0),
            showlegend=False,
            margin=dict(l=10, r=60, t=40, b=10),
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9",
                      title=val.replace("_"," ").title()),
            yaxis=dict(showgrid=False, title=""),
            height=380
        )
        charts.append({"title": f"Top {cat.replace('_',' ').title()}", "fig": fig})

        grouped2 = df.groupby(cat)[val].sum().nlargest(8).reset_index()
        grouped2.columns = [cat, val]
        fig2 = px.pie(
            grouped2, values=val, names=cat,
            title=f"{val.replace('_',' ').title()} Share by {cat.replace('_',' ').title()}",
            color_discrete_sequence=COLORS, hole=0.4
        )
        fig2.update_traces(textposition="outside", textinfo="percent+label",
                           pull=[0.05]*len(grouped2))
        fig2.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter, sans-serif", size=11, color="#1E293B"),
            title=dict(font=dict(size=14, color="#1E293B"), x=0),
            legend=dict(orientation="v", x=1.05, y=0.5),
            margin=dict(l=10, r=120, t=40, b=10),
            height=380
        )
        charts.append({"title": f"{cat.replace('_',' ').title()} Share", "fig": fig2})

    if date_cols:
        d = date_cols[0]
        trend = df.groupby(df[d].dt.to_period("M"))[val].sum().reset_index()
        trend[d] = trend[d].dt.to_timestamp()
        fig3 = px.line(
            trend, x=d, y=val,
            title=f"{val.replace('_',' ').title()} Trend Over Time",
            markers=True, color_discrete_sequence=["#2563EB"]
        )
        fig3.update_traces(line=dict(width=2.5), marker=dict(size=7))
        fig3.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter, sans-serif", size=12, color="#1E293B"),
            title=dict(font=dict(size=14, color="#1E293B"), x=0),
            xaxis=dict(showgrid=True, gridcolor="#F1F5F9", title=""),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9",
                      title=val.replace("_"," ").title()),
            margin=dict(l=10, r=10, t=40, b=10),
            height=350
        )
        charts.append({"title": "Trend Over Time", "fig": fig3})

    cat_cols = [c for c in df.select_dtypes(include="object").columns
                if not any(k in c.lower() for k in ["date","time","id","currency"])]
    if len(cat_cols) >= 2 and cat:
        cat2 = next((c for c in cat_cols if c != cat), None)
        if cat2:
            grouped3 = df.groupby(cat2)[val].sum().nlargest(8).reset_index()
            grouped3.columns = [cat2, val]
            fig4 = px.bar(
                grouped3, x=cat2, y=val,
                title=f"{val.replace('_',' ').title()} by {cat2.replace('_',' ').title()}",
                color=cat2, color_discrete_sequence=COLORS, text=val
            )
            fig4.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
            fig4.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Inter, sans-serif", size=12, color="#1E293B"),
                title=dict(font=dict(size=14, color="#1E293B"), x=0),
                showlegend=False,
                xaxis=dict(showgrid=False, title=""),
                yaxis=dict(showgrid=True, gridcolor="#F1F5F9",
                          title=val.replace("_"," ").title()),
                margin=dict(l=10, r=10, t=40, b=10),
                height=350
            )
            charts.append({"title": f"By {cat2.replace('_',' ').title()}", "fig": fig4})

    return charts
