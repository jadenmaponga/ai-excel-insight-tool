"""
app.py - DataLens  |  Main Streamlit Application
"""

import streamlit as st
import pandas as pd
import io
import base64

from clean_data import clean_dataset
from analytics import auto_charts, quick_stats
from insights  import generate_insights
from pdf_report import generate_pdf

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataLens — Business Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

  .main { background: #F8FAFC; }

  /* Header banner */
  .hero {
    background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 50%, #0EA5E9 100%);
    border-radius: 16px;
    padding: 40px 48px;
    color: white;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: "";
    position: absolute;
    top: -40px; right: -40px;
    width: 200px; height: 200px;
    border-radius: 50%;
    background: rgba(255,255,255,0.07);
  }
  .hero h1 { font-size: 2rem; font-weight: 700; margin: 0 0 8px; }
  .hero p  { font-size: 1rem; opacity: 0.85; margin: 0; }

  /* KPI cards */
  .kpi-card {
    background: white;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    border-left: 4px solid #2563EB;
    margin-bottom: 8px;
  }
  .kpi-label { font-size: 0.75rem; color: #64748B; font-weight: 600;
               text-transform: uppercase; letter-spacing: 0.05em; }
  .kpi-value { font-size: 1.6rem; font-weight: 700; color: #1E293B; margin-top: 4px; }

  /* Section headers */
  .section-header {
    font-size: 1rem; font-weight: 700; color: #1E293B;
    text-transform: uppercase; letter-spacing: 0.06em;
    padding: 0 0 10px; border-bottom: 2px solid #E2E8F0;
    margin: 28px 0 16px;
  }

  /* Upload area */
  .stFileUploader > div > div {
    border: 2px dashed #93C5FD !important;
    border-radius: 12px !important;
    background: #EFF6FF !important;
  }

  /* Change badge */
  .change-badge {
    display: inline-block;
    background: #ECFDF5;
    color: #065F46;
    font-size: 0.78rem;
    padding: 3px 10px;
    border-radius: 20px;
    margin: 3px 4px 3px 0;
    font-family: 'DM Mono', monospace;
    border: 1px solid #A7F3D0;
  }

  /* Insight box */
  .insight-box {
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    line-height: 1.7;
    font-size: 0.95rem;
    color: #334155;
    white-space: pre-wrap;
  }

  /* Dataframe styling */
  [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

  /* Button */
  .stButton > button {
    background: #2563EB; color: white; border: none;
    border-radius: 8px; padding: 8px 20px;
    font-weight: 600; font-family: 'DM Sans', sans-serif;
  }
  .stButton > button:hover { background: #1D4ED8; }

  /* Tab styling */
  .stTabs [data-baseweb="tab"] { font-weight: 600; }

  /* Hide Streamlit branding */
  #MainMenu {visibility: hidden;}
  footer    {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Hero header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>📊 DataLens</h1>
  <p>Upload any Excel or CSV file — your data is automatically cleaned, visualized, and analyzed by AI.</p>
</div>
""", unsafe_allow_html=True)


# ── File upload ────────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Drop your Excel or CSV file here",
    type=["xlsx", "xls", "csv"],
    help="Supports .xlsx, .xls, and .csv files"
)

if not uploaded:
    st.info("👆 Upload a file to get started. The tool will auto-clean your data and generate insights.")
    st.stop()


# ── Process ────────────────────────────────────────────────────────────────────
with st.spinner("Cleaning and analysing your dataset…"):
    cleaned_df, changes = clean_dataset(uploaded)
    stats   = quick_stats(cleaned_df)
    charts  = auto_charts(cleaned_df)


# ── KPI row ────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Key Metrics</div>', unsafe_allow_html=True)

cols = st.columns(4)
metric = stats.get("metric_name", "Value")

with cols[0]:
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-label">Total {metric}</div>
      <div class="kpi-value">{stats.get("total", 0):,.0f}</div>
    </div>""", unsafe_allow_html=True)

with cols[1]:
    st.markdown(f"""
    <div class="kpi-card" style="border-color:#10B981">
      <div class="kpi-label">Average {metric}</div>
      <div class="kpi-value">{stats.get("average", 0):,.2f}</div>
    </div>""", unsafe_allow_html=True)

with cols[2]:
    st.markdown(f"""
    <div class="kpi-card" style="border-color:#F59E0B">
      <div class="kpi-label">Records</div>
      <div class="kpi-value">{stats.get("rows", 0):,}</div>
    </div>""", unsafe_allow_html=True)

with cols[3]:
    st.markdown(f"""
    <div class="kpi-card" style="border-color:#8B5CF6">
      <div class="kpi-label">Columns</div>
      <div class="kpi-value">{stats.get("columns", 0)}</div>
    </div>""", unsafe_allow_html=True)


# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_clean, tab_charts, tab_ai, tab_raw = st.tabs([
    "✅ Cleaned Data", "📈 Charts", "🤖 AI Insights", "🗂 Raw Data"
])


# ── Tab 1: Cleaned data ────────────────────────────────────────────────────────
with tab_clean:
    st.markdown('<div class="section-header">What Was Fixed</div>', unsafe_allow_html=True)
    badges = "".join(f'<span class="change-badge">✓ {c}</span>' for c in changes)
    st.markdown(badges, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Cleaned Dataset</div>', unsafe_allow_html=True)
    st.dataframe(cleaned_df, use_container_width=True)

    # Download cleaned file
    buf = io.BytesIO()
    cleaned_df.to_excel(buf, index=False)
    st.download_button(
        "⬇ Download Cleaned Excel",
        data=buf.getvalue(),
        file_name="cleaned_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.markdown('<div class="section-header">Statistical Summary</div>', unsafe_allow_html=True)
    st.dataframe(cleaned_df.describe(), use_container_width=True)


# ── Tab 2: Charts ──────────────────────────────────────────────────────────────
with tab_charts:
    if not charts:
        st.warning("Not enough data to generate charts.")
    else:
        for i in range(0, len(charts), 2):
            row = st.columns(2)
            for j, col in enumerate(row):
                if i + j < len(charts):
                    c = charts[i + j]
                    with col:
                        st.plotly_chart(c["fig"], use_container_width=True)


# ── Tab 3: AI Insights ─────────────────────────────────────────────────────────
with tab_ai:
    st.markdown('<div class="section-header">AI-Generated Business Insights</div>', unsafe_allow_html=True)
    openai_key = st.text_input(
        "OpenAI API Key (optional — leave blank for free local AI or rule-based analysis)",
        type="password",
        placeholder="sk-…",
        help="If you have an OpenAI key, paste it here for GPT-4o-mini analysis."
    )
    if st.button("Generate Insights"):
        import os
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
        with st.spinner("Analysing your data…"):
            result = generate_insights(cleaned_df, stats)
        st.markdown(f'<div class="insight-box">{result}</div>', unsafe_allow_html=True)
        st.download_button(
            "⬇ Download Insights as Text",
            data=result,
            file_name="ai_insights.txt",
            mime="text/plain"
        )
    else:
        st.info("Click **Generate Insights** above to get an AI analysis of your dataset.")

    st.markdown("---")
    if st.button("Generate PDF Report"):
        with st.spinner("Building PDF report..."):
            from insights import generate_insights as gi
            insights_text = gi(cleaned_df, stats)
            pdf_path = generate_pdf(cleaned_df, stats, insights_text, "report.pdf")
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "⬇ Download PDF Report",
                    data=f.read(),
                    file_name="analysis_report.pdf",
                    mime="application/pdf"
                )

with tab_raw:
    st.markdown('<div class="section-header">Original Uploaded Data</div>', unsafe_allow_html=True)
    try:
        uploaded.seek(0)
        if uploaded.name.lower().endswith(".csv"):
            raw_df = pd.read_csv(uploaded)
        else:
            raw_df = pd.read_excel(uploaded)
        st.dataframe(raw_df, use_container_width=True)
    except Exception:
        st.warning("Could not re-read raw file (already processed).")
