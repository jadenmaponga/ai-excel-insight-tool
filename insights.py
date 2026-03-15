import os
import pandas as pd

def generate_insights(df, stats):
    prompt = _build_prompt(df, stats)
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            pass
    return _rule_based_insights(df, stats)

def _build_prompt(df, stats):
    summary = df.describe(include="all").to_string()
    metric = stats.get("metric_name", "value")
    total = stats.get("total", 0)
    avg = stats.get("average", 0)
    return f"""You are a senior business data analyst. Analyze this dataset and provide:
1. Key business insights (3-4 bullet points)
2. Top performing segments
3. Any anomalies or red flags
4. One actionable recommendation

Dataset summary:
{summary}

Total {metric}: {total:,.2f}
Average {metric}: {avg:,.2f}

Be concise and business-focused. Max 250 words."""

def _rule_based_insights(df, stats):
    lines = []
    metric = stats.get("metric_name", "metric")
    total = stats.get("total", 0)
    avg = stats.get("average", 0)
    rows = stats.get("rows", 0)

    lines.append(f"Dataset Overview: {rows} records analysed across {stats.get('columns',0)} columns.")
    lines.append(f"Total {metric}: {total:,.2f} | Average per record: {avg:,.2f}")

    # Use the same best value column as stats — skip id columns
    num_cols = [c for c in df.select_dtypes(include="number").columns
                if not any(k in c.lower() for k in ["id","index","row","num"])]
    cat_cols = [c for c in df.select_dtypes(include="object").columns
                if not any(k in c.lower() for k in ["id","currency","code","unknown"])]

    preferred = ["total_sales","total_revenue","revenue","sales","amount","total"]
    val = next((c for c in preferred if c in num_cols), num_cols[0] if num_cols else None)

    if cat_cols and val:
        cat = cat_cols[0]
        grouped = df.groupby(cat)[val].sum()
        top = grouped.idxmax()
        top_val = grouped.max()
        bottom = grouped.idxmin()
        bottom_val = grouped.min()
        lines.append(f"Top performer: {top} leads '{cat}' with {top_val:,.2f} in {val.replace('_',' ')}.")
        lines.append(f"Lowest performer: {bottom} recorded {bottom_val:,.2f} — worth investigating.")

        if len(grouped) > 2:
            share = (top_val / grouped.sum()) * 100
            lines.append(f"Concentration: {top} accounts for {share:.1f}% of total {val.replace('_',' ')}.")

    if val and df[val].std() > df[val].mean() * 0.5:
        lines.append(f"High variability detected in {val.replace('_',' ')} — consider segmenting further.")

    lines.append("Recommendation: Focus resources on top-performing segments while reviewing underperformers for improvement opportunities.")
    return "\n\n".join(lines)
