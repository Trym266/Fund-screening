import streamlit as st
import json
import os
import re
import plotly.graph_objects as go
import pandas as pd

# ── Colour palette ─────────────────────────────────────────────────────────────
NAVY   = "#1F2E4B"
BEIGE  = "#EFE7E0"
TEAL   = "#3B756A"
BROWN  = "#5C3317"
ORANGE = "#C8532A"
WHITE  = "#FFFFFF"
LIGHT  = "#F7F2EE"

PALETTE = [TEAL, "#2E6B8A", ORANGE, BROWN, "#6B9E8F", "#8B6B3D", "#4A7B9D", "#9E6B4A"]

# ── Sample data (demo mode) ────────────────────────────────────────────────────
DEMO_DATA = [
    {"fund_name": "Pale Blue Dot Fund II",       "date": "10 Apr 2025",
     "result": "Score: [88]\n**Proceed to deeper evaluation**\n- Estimated 80–90% climate-related\n"},
    {"fund_name": "Breakthrough Energy Ventures", "date": "09 Apr 2025",
     "result": "Score: [92]\n**Proceed to deeper evaluation**\n- Estimated 95–100% climate-related\n"},
    {"fund_name": "2150 Urban Tech Fund",          "date": "08 Apr 2025",
     "result": "Score: [62]\n**Borderline – needs clarification**\n- Estimated 55–65% climate-related\n"},
    {"fund_name": "Lowercarbon Capital III",       "date": "06 Apr 2025",
     "result": "Score: [95]\n**Proceed to deeper evaluation**\n- Estimated 100% climate-related\n"},
]

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Portfolio Builder – Ferd Impact",
    page_icon="🏗️",
    layout="wide",
)

st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;500;600&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">',
    unsafe_allow_html=True,
)
st.markdown(f'<style>body, .stApp {{ background-color: {BEIGE}; }}</style>', unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="background:{NAVY}; padding:28px 40px 20px 40px; margin:-1rem -1rem 0 -1rem;
         border-bottom:3px solid {TEAL};">
      <div style="display:flex; align-items:center; gap:16px;">
        <span style="font-size:28px;">🏗️</span>
        <div>
          <div style="font-family:'EB Garamond',serif; font-size:28px; font-weight:600;
               color:{WHITE}; letter-spacing:0.02em;">Portfolio Builder</div>
          <div style="font-family:'Inter',sans-serif; font-size:13px; color:{BEIGE}; opacity:0.8;
               margin-top:2px; letter-spacing:0.05em; text-transform:uppercase;">
            Construct your climate-tech portfolio from screened funds
          </div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Data helpers ───────────────────────────────────────────────────────────────
DATA_FILE = "screenings.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                records = json.load(f)
            if records:
                return records, False
        except (json.JSONDecodeError, OSError):
            pass
    return DEMO_DATA, True


def extract_score(text: str) -> int:
    m = re.search(r"Score:\s*\[?(\d+)", text)
    return int(m.group(1)) if m else 50


def extract_climate_exposure(text: str):
    section = re.search(r"CLIMATE EXPOSURE.*?(?=##|\Z)", text, re.DOTALL | re.IGNORECASE)
    chunk = section.group(0) if section else text
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


# ── Load data ──────────────────────────────────────────────────────────────────
raw_data, is_demo = load_data()

if is_demo:
    st.info(
        "**Demo mode** – showing sample funds. "
        "Screen real funds on the **Fund Screener** page to build a live portfolio.",
        icon="ℹ️",
    )

all_funds = []
for item in raw_data:
    result = item.get("result", "")
    all_funds.append({
        "name":     item.get("fund_name", "Unnamed"),
        "date":     item.get("date", ""),
        "score":    extract_score(result),
        "climate":  extract_climate_exposure(result),
        "rec":      get_recommendation(result),
        "result":   result,
    })

proceed_funds   = [f for f in all_funds if f["rec"] == "Proceed"]
borderline_funds = [f for f in all_funds if f["rec"] == "Borderline"]

# ── Fund Selection ─────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="font-family:\'EB Garamond\',serif; font-size:22px; font-weight:600; '
    f'color:{NAVY}; margin-bottom:6px;">Select Funds & Set Allocations</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div style="font-family:\'Inter\',sans-serif; font-size:14px; color:#666; margin-bottom:20px;">'
    "Check a fund to include it. Use the slider to set its relative weight — "
    "allocations are normalised to 100 % automatically."
    "</div>",
    unsafe_allow_html=True,
)

selected_funds: list[dict] = []
allocations: dict[str, int] = {}


def fund_row(fund: dict, default_checked: bool, default_alloc: int, badge_color: str):
    col_cb, col_info, col_slider = st.columns([0.5, 3, 3])
    with col_cb:
        checked = st.checkbox("", key=f"sel_{fund['name']}", value=default_checked)
    with col_info:
        climate_str = f"  ·  Climate ~{fund['climate']:.0f}%" if fund["climate"] else ""
        st.markdown(
            f"<div style='font-family:Inter,sans-serif; font-size:14px; font-weight:500; "
            f"padding-top:6px;'>{fund['name']}</div>"
            f"<div style='font-size:11px; color:#888;'>Score {fund['score']}{climate_str}</div>",
            unsafe_allow_html=True,
        )
    with col_slider:
        alloc = st.slider(
            "Weight", 5, 100, default_alloc, 5,
            key=f"alloc_{fund['name']}",
            label_visibility="collapsed",
        )
    return checked, alloc


if proceed_funds:
    st.markdown(
        f'<div style="font-family:Inter,sans-serif; font-size:12px; font-weight:600; '
        f'color:{TEAL}; text-transform:uppercase; letter-spacing:0.07em; margin-bottom:10px;">'
        "✅ Approved Funds</div>",
        unsafe_allow_html=True,
    )
    for fund in proceed_funds:
        checked, alloc = fund_row(fund, default_checked=True, default_alloc=25, badge_color=TEAL)
        if checked:
            selected_funds.append(fund)
            allocations[fund["name"]] = alloc

if borderline_funds:
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-family:Inter,sans-serif; font-size:12px; font-weight:600; '
        f'color:{ORANGE}; text-transform:uppercase; letter-spacing:0.07em; margin-bottom:10px;">'
        "⚠️ Borderline Funds</div>",
        unsafe_allow_html=True,
    )
    for fund in borderline_funds:
        checked, alloc = fund_row(fund, default_checked=False, default_alloc=15, badge_color=ORANGE)
        if checked:
            selected_funds.append(fund)
            allocations[fund["name"]] = alloc

# ── Portfolio Visualisation ────────────────────────────────────────────────────
st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

if not selected_funds:
    st.warning("Select at least one fund above to build your portfolio.")
    st.stop()

# Normalise
total_raw = sum(allocations[f["name"]] for f in selected_funds)
norm: dict[str, float] = {
    f["name"]: allocations[f["name"]] / total_raw * 100
    for f in selected_funds
}

# Blended metrics
blended_score = sum(f["score"] * norm[f["name"]] / 100 for f in selected_funds)
climate_funds = [f for f in selected_funds if f["climate"] is not None]
blended_climate = (
    sum(f["climate"] * norm[f["name"]] / 100 for f in climate_funds)
    / (sum(norm[f["name"]] / 100 for f in climate_funds) or 1)
    if climate_funds else None
)

st.markdown(
    f'<div style="font-family:\'EB Garamond\',serif; font-size:22px; font-weight:600; '
    f'color:{NAVY}; margin-bottom:20px;">Portfolio Overview</div>',
    unsafe_allow_html=True,
)

vis_col, stats_col = st.columns([1.3, 1])

with vis_col:
    labels = [f["name"] for f in selected_funds]
    values = [norm[f["name"]] for f in selected_funds]
    colors = PALETTE[: len(labels)]

    fig_pie = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color=BEIGE, width=3)),
        textinfo="percent+label",
        textfont=dict(family="Inter", size=12),
    ))
    fig_pie.add_annotation(
        text=f"<b>{len(selected_funds)}</b><br>fund{'s' if len(selected_funds) != 1 else ''}",
        x=0.5, y=0.5,
        font=dict(size=18, family="EB Garamond", color=NAVY),
        showarrow=False,
    )
    fig_pie.update_layout(
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20),
        height=360,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with stats_col:
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    def stat_card(label: str, value: str, color: str, note: str = "") -> str:
        note_html = (
            f"<div style='font-family:Inter,sans-serif; font-size:12px; color:#aaa; margin-top:2px;'>{note}</div>"
            if note else ""
        )
        return (
            f"<div style='background:{WHITE}; border-radius:10px; padding:18px 22px; "
            f"margin-bottom:14px; border-left:4px solid {color}; "
            f"box-shadow:0 1px 3px rgba(0,0,0,0.06);'>"
            f"<div style='font-family:Inter,sans-serif; font-size:11px; color:#888; "
            f"text-transform:uppercase; letter-spacing:0.06em;'>{label}</div>"
            f"<div style='font-family:\"EB Garamond\",serif; font-size:32px; "
            f"font-weight:600; color:{color};'>{value}</div>"
            f"{note_html}</div>"
        )

    st.markdown(
        stat_card("Funds in Portfolio", str(len(selected_funds)), NAVY),
        unsafe_allow_html=True,
    )
    st.markdown(
        stat_card("Blended Climate Score", f"{blended_score:.1f} / 100", TEAL, "Weighted average"),
        unsafe_allow_html=True,
    )
    if blended_climate is not None:
        above = blended_climate >= 50
        note  = "✅ Above 50 % mandate threshold" if above else "⚠️ Below 50 % mandate threshold"
        color = TEAL if above else ORANGE
        st.markdown(
            stat_card("Avg Climate Exposure", f"{blended_climate:.0f} %", color, note),
            unsafe_allow_html=True,
        )

    # Score gauge
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=blended_score,
        number={"font": {"family": "EB Garamond", "size": 28, "color": NAVY}, "suffix": "/100"},
        gauge={
            "axis": {"range": [0, 100], "tickfont": {"family": "Inter", "size": 10}},
            "bar":  {"color": TEAL, "thickness": 0.25},
            "bgcolor": LIGHT,
            "steps": [
                {"range": [0,  50], "color": "#F5ECE8"},
                {"range": [50, 70], "color": "#F0EDE4"},
                {"range": [70, 100], "color": "#E8F0EE"},
            ],
            "threshold": {
                "line": {"color": ORANGE, "width": 2},
                "thickness": 0.75,
                "value": 70,
            },
        },
        title={"text": "Blended Score", "font": {"family": "EB Garamond", "size": 14, "color": NAVY}},
    ))
    fig_gauge.update_layout(
        paper_bgcolor=WHITE,
        margin=dict(t=30, b=10, l=20, r=20),
        height=180,
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

# ── Allocation Table ──────────────────────────────────────────────────────────
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
st.markdown(
    f'<div style="font-family:\'EB Garamond\',serif; font-size:20px; font-weight:600; '
    f'color:{NAVY}; margin-bottom:14px;">Allocation Breakdown</div>',
    unsafe_allow_html=True,
)

rows_html = ""
for i, fund in enumerate(selected_funds):
    dot_color   = PALETTE[i % len(PALETTE)]
    alloc_pct   = norm[fund["name"]]
    climate_str = f"{fund['climate']:.0f} %" if fund["climate"] else "—"
    rec_color   = {"Proceed": TEAL, "Borderline": ORANGE, "Decline": BROWN}.get(fund["rec"], NAVY)
    rows_html += (
        f"<tr style='border-bottom:1px solid {BEIGE};'>"
        f"<td style='padding:11px 14px; font-family:Inter,sans-serif; font-size:14px;'>"
        f"<span style='display:inline-block; width:11px; height:11px; border-radius:50%; "
        f"background:{dot_color}; margin-right:9px; vertical-align:middle;'></span>"
        f"{fund['name']}</td>"
        f"<td style='padding:11px 14px; text-align:center; font-family:Inter,sans-serif; font-size:14px; "
        f"font-weight:600;'>{alloc_pct:.1f} %</td>"
        f"<td style='padding:11px 14px; text-align:center; font-family:Inter,sans-serif; font-size:14px;'>{fund['score']}</td>"
        f"<td style='padding:11px 14px; text-align:center; font-family:Inter,sans-serif; font-size:14px;'>{climate_str}</td>"
        f"<td style='padding:11px 14px; text-align:center;'>"
        f"<span style='background:{rec_color}; color:{WHITE}; font-family:Inter,sans-serif; "
        f"font-size:11px; font-weight:600; padding:2px 8px; border-radius:4px;'>{fund['rec']}</span>"
        f"</td></tr>"
    )

header_style = (
    f"padding:10px 14px; text-align:left; font-family:Inter,sans-serif; "
    f"font-size:11px; font-weight:600; color:#777; text-transform:uppercase; letter-spacing:0.06em;"
)
st.markdown(
    f"""
    <div style="background:{WHITE}; border-radius:10px; overflow:hidden;
         box-shadow:0 1px 4px rgba(0,0,0,0.07);">
      <table style="width:100%; border-collapse:collapse;">
        <thead>
          <tr style="background:{LIGHT};">
            <th style="{header_style}">Fund</th>
            <th style="{header_style} text-align:center;">Allocation</th>
            <th style="{header_style} text-align:center;">Score</th>
            <th style="{header_style} text-align:center;">Climate %</th>
            <th style="{header_style} text-align:center;">Status</th>
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
st.caption("Allocations are normalised relative weights. Adjust sliders above to rebalance.")
