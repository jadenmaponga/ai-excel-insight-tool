"""
insights.py - AI Insight Generation
Tries OpenAI first, falls back to Ollama, then rule-based summary.
"""

import os
import pandas as pd


def generate_insights(df: pd.DataFrame, stats: dict) -> str:
    """
    Returns a plain-text AI analysis.
    Tries: 1) OpenAI  2) Ollama  3) Rule-based fallback
    """
    prompt = _build_prompt(df, stats)

    # Try OpenAI
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
        except Exception as e:
            pass  # fall through to Ollama

    # Try Ollama (local, free)
    try:
        import ollama
        resp = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}],
        )
        return resp["message"]["content"].strip()
    except Exception:
        pass

    # Rule-based fallback (always works, no API needed)
    return _rule_based_insights(df, stats)


def _build_prompt(df: pd.DataFrame, stats: dict) -> str:
    summary = df.describe(include="all").to_string()
    sample  = df.head(5).to_string()
    metric  = stats.get("metric_name", "value")
    total   = stats.get("total", 0)
    avg     = stats.get("average", 0)

    return f"""You are a senior business data analyst. Analyze this dataset summary and provide:
1. Key business insights (3-4 bullet points)
2. Top performing segments
3. Any anomalies or red flags
4. One actionable recommendation

Dataset summary:
{summary}

Sample rows:
{sample}

Total {metric}: {total:,.2f}
Average {metric}: {avg:,.2f}

Be concise, business-focused, and specific to the numbers. Max 250 words."""


def _rule_based_insights(df: pd.DataFrame, stats: dict) -> str:
    lines = []
    metric = stats.get("metric_name", "metric")
    total  = stats.get("total",   0)
    avg    = stats.get("average", 0)
    rows   = stats.get("rows",    0)

    lines.append(f"📊 **Dataset Overview**: {rows} records analysed across {stats.get('columns',0)} columns.")
    lines.append(f"💰 **Total {metric}**: {total:,.2f} | Average per record: {avg:,.2f}")

    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(include="object").columns.tolist()

    if cat_cols and num_cols:
        cat = cat_cols[0]
        val = num_cols[0]
        top = df.groupby(cat)[val].sum().idxmax()
        top_val = df.groupby(cat)[val].sum().max()
        lines.append(f"🏆 **Top performer**: {top} leads '{cat}' with {top_val:,.2f} in '{val}'.")

        bottom = df.groupby(cat)[val].sum().idxmin()
        lines.append(f"⚠️  **Lowest performer**: {bottom} has the lowest {val} — worth investigating.")

    if num_cols:
        std = df[num_cols[0]].std()
        mean = df[num_cols[0]].mean()
        if std > mean * 0.5:
            lines.append(f"📈 **High variability** detected in '{num_cols[0]}' — consider segmenting the data further.")

    lines.append("💡 **Recommendation**: Focus resources on top-performing segments while reviewing underperformers for improvement opportunities.")

    return "\n\n".join(lines)