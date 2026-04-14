import streamlit as st
import json
import os
import re
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── Colour palette (same as main app) ─────────────────────────────────────────
NAVY   = "#1F2E4B"
BEIGE  = "#EFE7E0"
TEAL   = "#3B756A"
BROWN  = "#5C3317"
ORANGE = "#C8532A"
WHITE  = "#FFFFFF"
LIGHT  = "#F7F2EE"
BLUE   = "#2E6B8A"

# ── Sample data shown when no real screenings exist ───────────────────────────
DEMO_DATA = [
    {"fund_name": "Pale Blue Dot Fund II",  "date": "10 Apr 2025, 09:14",
     "result": "## 4. FIT WITH FERD MANDATE\nScore: [88]\n## 7. RECOMMENDATION\n**Proceed to deeper evaluation**\n## 2. CLIMATE EXPOSURE\n- Estimated 80–90% of climate-related investments\n"},
    {"fund_name": "Breakthrough Energy Ventures III", "date": "09 Apr 2025, 14:30",
     "result": "## 4. FIT WITH FERD MANDATE\nScore: [92]\n## 7. RECOMMENDATION\n**Proceed to deeper evaluation**\n## 2. CLIMATE EXPOSURE\n- Estimated 95–100% climate-related\n"},
    {"fund_name": "2150 Urban Tech Fund",    "date": "08 Apr 2025, 11:05",
     "result": "## 4. FIT WITH FERD MANDATE\nScore: [62]\n## 7. RECOMMENDATION\n**Borderline – needs clarification**\n## 2. CLIMATE EXPOSURE\n- Estimated 55–65% climate-related\n"},
    {"fund_name": "Deep Science Ventures",  "date": "07 Apr 2025, 16:22",
     "result": "## 4. FIT WITH FERD MANDATE\nScore: [45]\n## 7. RECOMMENDATION\n**Decline**\n## 2. CLIMATE EXPOSURE\n- Estimated 30–40% climate-related\n"},
    {"fund_name": "Lowercarbon Capital III", "date": "06 Apr 2025, 10:00",
     "result": "## 4. FIT WITH FERD MANDATE\nScore: [95]\n## 7. RECOMMENDATION\n**Proceed to deeper evaluation**\n## 2. CLIMATE EXPOSURE\n- Estimated 100% climate-related\n"},
]

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Analytics – Ferd Impact",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;500;600&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">',
    unsafe_allow_html=True,
)
st.markdown(f'<style>body, .stApp {{ background-color: {BEIGE}; }}</style>', unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="background:{NAVY}; padding:28px 40px 20px 40px; margin:-1rem -1rem 0 -1rem; border-bottom:3px solid {TEAL};">
      <div style="display:flex; align-items:center; gap:16px;">
        <span style="font-size:28px;">📊</span>
        <div>
          <div style="font-family:'EB Garamond',serif; font-size:28px; font-weight:600;
               color:{WHITE}; letter-spacing:0.02em;">Analytics Dashboard</div>
          <div style="font-family:'Inter',sans-serif; font-size:13px; color:{BEIGE}; opacity:0.8;
               margin-top:2px; letter-spacing:0.05em; text-transform:uppercase;">
            Ferd Impact Investing · Screening Overview
          </div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Data helpers ──────────────────────────────────────────────────────────────
DATA_FILE = "screenings.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                records = json.load(f)
            if records:
                return records, False   # real data
        except (json.JSONDecodeError, OSError):
            pass
    return DEMO_DATA, True              # demo data


def extract_score(text: str):
    m = re.search(r"Score:\s*\[?(\d+)", text)
    return int(m.group(1)) if m else None


def extract_climate_exposure(text: str):
    section = re.search(r"CLIMATE EXPOSURE.*?(?=##|\Z)", text, re.DOTALL | re.IGNORECASE)
    if section:
        chunk = section.group(0)
        m = re.search(r"(\d{2,3})\s*[–\-–]\s*(\d{2,3})\s*%", chunk)
        if m:
            return (int(m.group(1)) + int(m.group(2))) / 2
        m = re.search(r"(\d{2,3})\s*%", chunk)
        if m:
            return int(m.group(1))
    return None


def get_recommendation(text: str) -> str:
    low = text.lower()
    if "proceed to deeper evaluation" in low:
        return "Proceed"
    elif "borderline" in low:
        return "Borderline"
    return "Decline"


# ── Load & build DataFrame ────────────────────────────────────────────────────
raw_data, is_demo = load_data()

if is_demo:
    st.info(
        "**Demo mode** – no real screenings found. "
        "Head to the **Fund Screener** page to screen your first fund. "
        "The charts below use sample data.",
        icon="ℹ️",
    )

rows = []
for item in raw_data:
    result_text = item.get("result", "")
    rows.append({
        "Fund":            item.get("fund_name", "Unnamed"),
        "Date":            item.get("date", ""),
        "Score":           extract_score(result_text),
        "ClimateExposure": extract_climate_exposure(result_text),
        "Recommendation":  get_recommendation(result_text),
        "Result":          result_text,
    })

df = pd.DataFrame(rows)

# ── KPI Metrics ───────────────────────────────────────────────────────────────
total            = len(df)
proceed_count    = int((df["Recommendation"] == "Proceed").sum())
borderline_count = int((df["Recommendation"] == "Borderline").sum())
decline_count    = int((df["Recommendation"] == "Decline").sum())
avg_score        = df["Score"].dropna().mean()


def kpi_card(label: str, value: str, color: str, sublabel: str = "") -> str:
    sub_html = (
        f"<div style='font-family:Inter,sans-serif; font-size:12px; color:#aaa; margin-top:2px;'>{sublabel}</div>"
        if sublabel else ""
    )
    return (
        f"<div style='background:{WHITE}; border-radius:10px; padding:20px 24px; "
        f"border-left:4px solid {color}; box-shadow:0 1px 4px rgba(0,0,0,0.07);'>"
        f"<div style='font-family:Inter,sans-serif; font-size:11px; color:#888; "
        f"text-transform:uppercase; letter-spacing:0.07em; margin-bottom:6px;'>{label}</div>"
        f"<div style='font-family:\"EB Garamond\",serif; font-size:38px; font-weight:600; "
        f"color:{color}; line-height:1;'>{value}</div>"
        f"{sub_html}</div>"
    )


c1, c2, c3, c4, c5 = st.columns(5)
pct = lambda n: f"{n/total*100:.0f}%" if total else "—"

with c1: st.markdown(kpi_card("Total Screened",  str(total),          NAVY),   unsafe_allow_html=True)
with c2: st.markdown(kpi_card("Proceeding",      str(proceed_count),  TEAL,    pct(proceed_count)),    unsafe_allow_html=True)
with c3: st.markdown(kpi_card("Borderline",      str(borderline_count), ORANGE, pct(borderline_count)), unsafe_allow_html=True)
with c4: st.markdown(kpi_card("Declined",        str(decline_count),  BROWN,   pct(decline_count)),    unsafe_allow_html=True)
with c5: st.markdown(kpi_card("Avg Score",       f"{avg_score:.0f}" if not pd.isna(avg_score) else "—", BLUE), unsafe_allow_html=True)

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

# ── Charts Row ────────────────────────────────────────────────────────────────
chart_l, chart_r = st.columns([1, 1.6])

with chart_l:
    fig_donut = go.Figure(go.Pie(
        labels=["Proceed", "Borderline", "Decline"],
        values=[proceed_count, borderline_count, decline_count],
        hole=0.65,
        marker=dict(colors=[TEAL, ORANGE, BROWN], line=dict(color=BEIGE, width=3)),
        textinfo="percent+label",
        textfont=dict(family="Inter", size=12, color=NAVY),
        insidetextorientation="radial",
    ))
    fig_donut.add_annotation(
        text=f"<b>{total}</b><br>funds",
        x=0.5, y=0.5,
        font=dict(size=18, family="EB Garamond", color=NAVY),
        showarrow=False,
    )
    fig_donut.update_layout(
        title=dict(
            text="Recommendation Breakdown",
            font=dict(family="EB Garamond", size=18, color=NAVY),
            x=0,
        ),
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        showlegend=False,
        margin=dict(t=55, b=20, l=20, r=20),
        height=320,
    )
    st.plotly_chart(fig_donut, use_container_width=True)

with chart_r:
    df_scores = df.dropna(subset=["Score"]).sort_values("Score")
    if not df_scores.empty:
        color_map = {"Proceed": TEAL, "Borderline": ORANGE, "Decline": BROWN}
        bar_colors = [color_map.get(r, NAVY) for r in df_scores["Recommendation"]]

        fig_bar = go.Figure(go.Bar(
            x=df_scores["Score"],
            y=df_scores["Fund"],
            orientation="h",
            marker_color=bar_colors,
            text=df_scores["Score"].dropna().astype(int).astype(str),
            textposition="outside",
            textfont=dict(family="Inter", size=12, color=NAVY),
        ))
        fig_bar.update_layout(
            title=dict(
                text="Fund Scores (0–100)",
                font=dict(family="EB Garamond", size=18, color=NAVY),
                x=0,
            ),
            paper_bgcolor=WHITE,
            plot_bgcolor=LIGHT,
            xaxis=dict(
                range=[0, 115],
                showgrid=True,
                gridcolor="#E5E0DB",
                tickfont=dict(family="Inter"),
            ),
            yaxis=dict(showgrid=False, tickfont=dict(family="Inter", size=12)),
            margin=dict(t=55, b=20, l=10, r=60),
            height=320,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# ── Scatter: Climate Exposure vs Score ────────────────────────────────────────
df_scatter = df.dropna(subset=["Score", "ClimateExposure"])
if len(df_scatter) >= 2:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    color_map = {"Proceed": TEAL, "Borderline": ORANGE, "Decline": BROWN}
    scatter_colors = [color_map.get(r, NAVY) for r in df_scatter["Recommendation"]]

    fig_scatter = go.Figure(go.Scatter(
        x=df_scatter["ClimateExposure"],
        y=df_scatter["Score"],
        mode="markers+text",
        marker=dict(
            color=scatter_colors,
            size=16,
            opacity=0.85,
            line=dict(color=WHITE, width=2),
        ),
        text=df_scatter["Fund"],
        textposition="top center",
        textfont=dict(family="Inter", size=11, color=NAVY),
    ))
    fig_scatter.add_vline(
        x=50,
        line_dash="dash",
        line_color="#C8BEB4",
        annotation_text="50 % climate threshold",
        annotation_font=dict(family="Inter", size=11, color=BROWN),
        annotation_position="top right",
    )
    fig_scatter.add_hrect(y0=70, y1=100, fillcolor=TEAL, opacity=0.04, line_width=0)
    fig_scatter.update_layout(
        title=dict(
            text="Climate Exposure vs Fund Score",
            font=dict(family="EB Garamond", size=18, color=NAVY),
            x=0,
        ),
        paper_bgcolor=WHITE,
        plot_bgcolor=LIGHT,
        xaxis=dict(
            title="Est. Climate Exposure (%)",
            range=[0, 108],
            gridcolor="#E5E0DB",
            tickfont=dict(family="Inter"),
        ),
        yaxis=dict(
            title="Mandate Fit Score",
            range=[0, 108],
            gridcolor="#E5E0DB",
            tickfont=dict(family="Inter"),
        ),
        margin=dict(t=55, b=50, l=60, r=20),
        height=400,
        showlegend=False,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# ── Fund Table ────────────────────────────────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.markdown(
    f'<div style="font-family:\'EB Garamond\',serif; font-size:22px; font-weight:600; '
    f'color:{NAVY}; margin-bottom:16px;">All Screened Funds</div>',
    unsafe_allow_html=True,
)

color_map = {"Proceed": TEAL, "Borderline": ORANGE, "Decline": BROWN}
for _, row in df.iterrows():
    c = color_map.get(row["Recommendation"], NAVY)
    score_str = str(int(row["Score"])) if pd.notna(row["Score"]) else "—"
    climate_str = (f" · Climate ~{row['ClimateExposure']:.0f}%"
                   if pd.notna(row["ClimateExposure"]) else "")
    with st.expander(
        f"**{row['Fund']}**  ·  Score {score_str}{climate_str}  ·  {row['Recommendation']}",
        expanded=False,
    ):
        st.markdown(
            f'<span style="background:{c}; color:{WHITE}; font-size:12px; font-weight:600; '
            f'padding:3px 10px; border-radius:4px;">{row["Recommendation"]}</span>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown(row["Result"] if row["Result"].strip() else "_No details available._")
