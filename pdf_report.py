from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
from datetime import datetime

BLUE = colors.HexColor("#2563EB")
LIGHT_BLUE = colors.HexColor("#EFF6FF")
GREEN = colors.HexColor("#10B981")
GRAY = colors.HexColor("#64748B")
LIGHT_GRAY = colors.HexColor("#F8FAFC")
WHITE = colors.white
BLACK = colors.HexColor("#1E293B")
PALETTE = ["#2563EB","#10B981","#F59E0B","#EF4444","#8B5CF6","#EC4899"]

def _best_val(df):
    num_cols = df.select_dtypes(include="number").columns.tolist()
    num_cols = [c for c in num_cols if not any(k in c for k in ["id","index","row"])]
    preferred = ["total_sales","total_revenue","revenue","sales","amount","total"]
    return next((c for c in preferred if c in num_cols), num_cols[0] if num_cols else None)

def _best_cat(df):
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    skip = ["date","time","id","code","currency","order","created","updated","name"]
    cat_cols = [c for c in cat_cols if not any(k in c.lower() for k in skip)]
    preferred = ["product_name","category","region","product","type","segment"]
    return next((c for c in preferred if c in cat_cols), cat_cols[0] if cat_cols else None)

def _make_chart(df, chart_type="bar"):
    val = _best_val(df)
    cat = _best_cat(df)
    if not val or not cat:
        return None
    grouped = df.groupby(cat)[val].sum().nlargest(8)
    fig, ax = plt.subplots(figsize=(7, 3.5), facecolor="white")
    ax.set_facecolor("white")
    if chart_type == "bar":
        bars = ax.barh(grouped.index, grouped.values,
                       color=PALETTE[:len(grouped)], edgecolor="none")
        ax.set_xlabel(val.replace("_"," ").title(), fontsize=9)
        ax.tick_params(labelsize=8)
        for bar, v in zip(bars, grouped.values):
            ax.text(bar.get_width() + max(grouped.values)*0.01,
                    bar.get_y() + bar.get_height()/2,
                    f"{v:,.0f}", va="center", fontsize=7)
    elif chart_type == "pie":
        ax.pie(grouped.values, labels=grouped.index,
               autopct="%1.1f%%", colors=PALETTE[:len(grouped)],
               startangle=140, pctdistance=0.82,
               textprops={"fontsize": 7})
    ax.set_title(f"{val.replace('_',' ').title()} by {cat.replace('_',' ').title()}",
                 fontsize=10, fontweight="bold", pad=10)
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf

def _kpi_cell(label, value):
    label_style = ParagraphStyle("kl", fontSize=7, fontName="Helvetica",
                                  textColor=GRAY, alignment=TA_CENTER, spaceAfter=2)
    value_style = ParagraphStyle("kv", fontSize=13, fontName="Helvetica-Bold",
                                  textColor=BLACK, alignment=TA_CENTER)
    return [Paragraph(label.upper(), label_style), Paragraph(value, value_style)]

def generate_pdf(df, stats, insights_text, filename="analysis_report.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4,
                             rightMargin=1.5*cm, leftMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []

    header_style = ParagraphStyle("hdr", fontSize=18, fontName="Helvetica-Bold",
                                   textColor=WHITE, alignment=TA_CENTER, spaceAfter=4)
    header_data = [[Paragraph("DataLens Business Intelligence Report", header_style)]]
    header_table = Table(header_data, colWidths=[17*cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), BLUE),
        ("TOPPADDING", (0,0), (-1,-1), 16),
        ("BOTTOMPADDING", (0,0), (-1,-1), 16),
        ("LEFTPADDING", (0,0), (-1,-1), 20),
        ("RIGHTPADDING", (0,0), (-1,-1), 20),
    ]))
    story.append(header_table)

    date_style = ParagraphStyle("dt", fontSize=9, fontName="Helvetica",
                                 textColor=GRAY, alignment=TA_CENTER,
                                 spaceBefore=6, spaceAfter=16)
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %B %Y at %H:%M')}",
        date_style))

    section_style = ParagraphStyle("sec", fontSize=12, fontName="Helvetica-Bold",
                                    textColor=BLACK, spaceBefore=12, spaceAfter=8)
    story.append(Paragraph("Key Performance Indicators", section_style))

    metric = stats.get("metric_name", "Value")
    kpi_data = [[
        _kpi_cell("Total " + metric, f"{stats.get('total',0):,.0f}"),
        _kpi_cell("Average " + metric, f"{stats.get('average',0):,.2f}"),
        _kpi_cell("Total Records", str(stats.get("rows",0))),
        _kpi_cell("Columns", str(stats.get("columns",0))),
    ]]
    kpi_table = Table(kpi_data, colWidths=[4.1*cm]*4)
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT_BLUE),
        ("TOPPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("LINEAFTER", (0,0), (2,0), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("Dataset Summary", section_style))
    summary_df = df.describe().round(2).reset_index()
    table_data = [list(summary_df.columns)]
    for _, row in summary_df.iterrows():
        table_data.append([str(v) for v in row])
    col_w = 17*cm / len(table_data[0])
    data_table = Table(table_data, colWidths=[col_w]*len(table_data[0]))
    data_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BLUE),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 7.5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT_GRAY]),
        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
    ]))
    story.append(data_table)
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("Visual Analysis", section_style))
    bar_buf = _make_chart(df, "bar")
    pie_buf = _make_chart(df, "pie")
    if bar_buf and pie_buf:
        chart_data = [[
            Image(bar_buf, width=8.3*cm, height=4.5*cm),
            Image(pie_buf, width=8.3*cm, height=4.5*cm),
        ]]
        chart_table = Table(chart_data, colWidths=[8.5*cm, 8.5*cm])
        chart_table.setStyle(TableStyle([
            ("TOPPADDING", (0,0), (-1,-1), 0),
            ("BOTTOMPADDING", (0,0), (-1,-1), 0),
            ("LEFTPADDING", (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(chart_table)

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("AI Business Insights", section_style))
    insight_style = ParagraphStyle("ins", fontSize=9, fontName="Helvetica",
                                    textColor=BLACK, leading=16,
                                    leftIndent=10, rightIndent=10)
    insight_box_data = [[Paragraph(insights_text.replace("\n\n", "<br/><br/>"), insight_style)]]
    insight_box = Table(insight_box_data, colWidths=[17*cm])
    insight_box.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT_GRAY),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
    ]))
    story.append(insight_box)
    story.append(Spacer(1, 0.6*cm))

    footer_style = ParagraphStyle("ft", fontSize=8, fontName="Helvetica",
                                   textColor=GRAY, alignment=TA_CENTER)
    story.append(Paragraph(
        "Generated by DataLens | Confidential Business Report",
        footer_style))
    doc.build(story)
    return filename
