import streamlit as st
import anthropic
import json
import os
import PyPDF2
import io
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ferd Impact – Fund Screener",
    page_icon="🌿",
    layout="wide",
)

# ── Google Fonts ──────────────────────────────────────────────────────────────
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;500;600&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">',
    unsafe_allow_html=True,
)

# ── Colours ───────────────────────────────────────────────────────────────────
NAVY   = "#1F2E4B"
BEIGE  = "#EFE7E0"
TEAL   = "#3B756A"
BROWN  = "#5C3317"
ORANGE = "#C8532A"
WHITE  = "#FFFFFF"
LIGHT  = "#F7F2EE"

# ── Global page background ────────────────────────────────────────────────────
st.markdown(
    f'<style>body, .stApp {{ background-color: {BEIGE}; }}</style>',
    unsafe_allow_html=True,
)

# ── Data file ─────────────────────────────────────────────────────────────────
DATA_FILE = "screenings.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def reset_data():
    save_data([])

# ── PDF extraction ────────────────────────────────────────────────────────────
def extract_pdf_text(uploaded_file) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)

# ── Claude prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an investment analyst working for Ferd Impact Investing.

Your task is to evaluate whether a VC fund fits our mandate:
- Focus: Climate technology
- Requirement: At least 50% of the portfolio must be climate-related
- Preference: Strong potential for meaningful climate impact and venture-scale returns

OUTPUT FORMAT (use exactly these section headers):

## 1. FUND SUMMARY
(max 150 words)
Strategy, sector, theme | Stage | Geography | Ticket Size | Fund number | Founders, GPs, and their background

## 2. CLIMATE EXPOSURE
- Estimated % of climate-related investments (range is fine)
- Breakdown of climate vs non-climate (if possible)
- Level of confidence: High / Medium / Low

## 3. CLIMATE QUALITY
- Type of climate focus (e.g. energy, mobility, carbon removal, etc.)
- Depth: Core climate vs "climate-adjacent"
- Risk of greenwashing: Low / Medium / High

## 4. FIT WITH FERD MANDATE
Score: [0–100]
Key reasons (3–5 bullets)

## 5. KEY RISKS
- Strategy risks
- Team risks
- Market risks

## 6. RED FLAGS
Check and comment on:
- Infrastructure fund (not VC)
- Solo GP
- PE not VC exposure

## 7. RECOMMENDATION
Choose exactly one:
**Proceed to deeper evaluation**
**Borderline – needs clarification**
**Decline**

## 8. IF BORDERLINE: WHAT WOULD YOU NEED TO KNOW?
(Only if Borderline – list 3–5 specific questions. Omit this section otherwise.)

Be concise, analytical, and opinionated. Avoid generic statements."""

def run_screening(fund_text: str) -> str:
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Please screen this VC fund:\n\n{fund_text}"}],
    )
    return message.content[0].text

# ── Recommendation badge ──────────────────────────────────────────────────────
def recommendation_badge(result_text: str):
    low = result_text.lower()
    if "proceed to deeper evaluation" in low:
        color, label = TEAL,   "✅ Proceed to deeper evaluation"
    elif "borderline" in low:
        color, label = ORANGE, "⚠️ Borderline – needs clarification"
    else:
        color, label = BROWN,  "❌ Decline"
    return color, label

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="background:{NAVY}; padding:28px 40px 20px 40px; margin:-1rem -1rem 0 -1rem; border-bottom:3px solid {TEAL};">
      <div style="display:flex; align-items:center; gap:16px;">
        <span style="font-size:28px;">🌿</span>
        <div>
          <div style="font-family:'EB Garamond',serif; font-size:28px; font-weight:600; color:{WHITE}; letter-spacing:0.02em;">
            Ferd Impact Investing
          </div>
          <div style="font-family:'Inter',sans-serif; font-size:13px; color:{BEIGE}; opacity:0.8; margin-top:2px; letter-spacing:0.05em; text-transform:uppercase;">
            VC Fund Screener
          </div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Layout: two columns ───────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1.1], gap="large")

# ══════════════════════════════════════════════════════════════════════════════
# LEFT COLUMN – Input
# ══════════════════════════════════════════════════════════════════════════════
with col_left:
    st.markdown(
        f'<div style="font-family:\'EB Garamond\',serif; font-size:22px; font-weight:600; color:{NAVY}; margin-bottom:16px;">Submit Fund for Screening</div>',
        unsafe_allow_html=True,
    )

    fund_name = st.text_input(
        "Fund name",
        placeholder="e.g. Pale Blue Dot Fund II",
        help="Used to label this screening in the history",
    )

    tab_pdf, tab_text = st.tabs(["📄 Upload PDF", "✏️ Paste text"])

    fund_text = ""

    with tab_pdf:
        uploaded = st.file_uploader(
            "Upload fund deck (PDF)",
            type=["pdf"],
            label_visibility="collapsed",
        )
        if uploaded:
            with st.spinner("Extracting text from PDF…"):
                fund_text = extract_pdf_text(uploaded)
            st.success(f"Extracted {len(fund_text):,} characters from PDF.")

    with tab_text:
        pasted = st.text_area(
            "Paste fund description or deck content",
            height=260,
            placeholder="Paste the full fund deck text, description, or any relevant information here…",
            label_visibility="collapsed",
        )
        if pasted.strip():
            fund_text = pasted

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    run_btn = st.button(
        "🔍  Run Screening",
        type="primary",
        use_container_width=True,
        disabled=not fund_text.strip(),
    )

    # Custom button style
    st.markdown(
        f"""<style>
        div.stButton > button[kind="primary"] {{
            background-color: {TEAL} !important;
            color: {WHITE} !important;
            border: none !important;
            font-family: 'Inter', sans-serif !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            padding: 12px !important;
            border-radius: 6px !important;
        }}
        div.stButton > button[kind="primary"]:hover {{
            background-color: {NAVY} !important;
        }}
        </style>""",
        unsafe_allow_html=True,
    )

    # ── History sidebar ───────────────────────────────────────────────────────
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-family:\'EB Garamond\',serif; font-size:20px; font-weight:600; color:{NAVY}; margin-bottom:12px;">Screening History</div>',
        unsafe_allow_html=True,
    )

    data = load_data()

    if not data:
        st.markdown(
            f'<div style="font-family:\'Inter\',sans-serif; font-size:14px; color:{BROWN}; opacity:0.7;">No screenings yet.</div>',
            unsafe_allow_html=True,
        )
    else:
        for i, item in enumerate(reversed(data)):
            badge_color, badge_label = recommendation_badge(item.get("result", ""))
            idx = len(data) - 1 - i
            with st.expander(f"**{item.get('fund_name','Unnamed')}** — {item.get('date','')}", expanded=False):
                st.markdown(
                    f'<span style="background:{badge_color}; color:{WHITE}; font-family:Inter,sans-serif; font-size:12px; font-weight:600; padding:3px 10px; border-radius:4px;">{badge_label}</span>',
                    unsafe_allow_html=True,
                )
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                st.markdown(item.get("result", ""), unsafe_allow_html=False)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if data:
        if st.button("🔄 Reset all screenings", use_container_width=True):
            reset_data()
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RIGHT COLUMN – Result
# ══════════════════════════════════════════════════════════════════════════════
with col_right:
    st.markdown(
        f'<div style="font-family:\'EB Garamond\',serif; font-size:22px; font-weight:600; color:{NAVY}; margin-bottom:16px;">Screening Result</div>',
        unsafe_allow_html=True,
    )

    result_placeholder = st.empty()

    if run_btn and fund_text.strip():
        with st.spinner("Analysing fund…"):
            result = run_screening(fund_text)

        badge_color, badge_label = recommendation_badge(result)

        # Save to history
        entry = {
            "fund_name": fund_name.strip() if fund_name.strip() else "Unnamed Fund",
            "date": datetime.now().strftime("%d %b %Y, %H:%M"),
            "result": result,
        }
        records = load_data()
        records.append(entry)
        save_data(records)

        with result_placeholder.container():
            # Recommendation badge
            st.markdown(
                f"""
                <div style="background:{badge_color}; color:{WHITE}; font-family:'Inter',sans-serif;
                     font-size:15px; font-weight:600; padding:12px 20px; border-radius:6px; margin-bottom:20px;">
                    {badge_label}
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Result card
            st.markdown(
                f"""
                <div style="background:{WHITE}; border:1px solid #D9D0C7; border-radius:8px;
                     padding:28px 32px; font-family:'Inter',sans-serif; font-size:14px; line-height:1.7;
                     color:#2A2A2A;">
                """,
                unsafe_allow_html=True,
            )
            st.markdown(result)
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        result_placeholder.markdown(
            f"""
            <div style="background:{LIGHT}; border:1px dashed #C8BEB4; border-radius:8px;
                 padding:48px 32px; text-align:center; color:{NAVY}; opacity:0.5;">
                <div style="font-family:'EB Garamond',serif; font-size:20px; margin-bottom:8px;">
                    No screening run yet
                </div>
                <div style="font-family:'Inter',sans-serif; font-size:13px;">
                    Upload a PDF or paste fund text, then click Run Screening.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
