"""
ui.py - the look of the app: colors, fonts, and small pieces of HTML.

Everything visual lives here so app.py can stay focused on what the app does.
All text that comes from a CSV or the AI goes through html.escape() first.
"""

import html

import streamlit as st

# Colors used across the page (charts use the team colors in charts.py)
INK = "#1E1B4B"        # main text
MUTED = "#64748B"      # secondary text
BRAND = "#4F46E5"      # buttons, highlights
BRAND_DARK = "#3730A3"

# Each kind of flag gets an icon, a friendly name, and a soft tint for its badge
FLAG_STYLES = {
    "freeloader":     ("💤", "Freeloader",     "#FEF3C7", "#92400E"),
    "retaliation":    ("😠", "Retaliation",    "#FEE2E2", "#991B1B"),
    "manipulation":   ("🕵️", "Manipulation",   "#EDE9FE", "#5B21B6"),
    "collusion":      ("🤝", "Collusion",      "#DBEAFE", "#1E40AF"),
    "mismatch":       ("🔀", "Score mismatch", "#FCE7F3", "#9D174D"),
    "self_inflation": ("🎈", "Self-inflation", "#DCFCE7", "#166534"),
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* The font is set on text elements only, so Streamlit's icon font still works */
html, body, .stApp, p, li, label, h1, h2, h3, h4, button, input, textarea,
.stMarkdown, [data-testid="stCaptionContainer"],
.hero, .steps, .stats, .stat, .callout, .savings, .flag-head, .evidence, .student-line {{
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
}}
.stApp {{
    background:
      radial-gradient(1200px 500px at 10% -10%, #E0E7FF 0%, transparent 60%),
      radial-gradient(900px 400px at 100% 0%, #FCE7F3 0%, transparent 55%),
      #F8FAFC;
}}
.block-container {{ padding-top: 1.5rem; max-width: 1200px; }}
#MainMenu, footer, [data-testid="stToolbar"] {{ visibility: hidden; }}
h1, h2, h3 {{ color: {INK}; letter-spacing: -0.02em; }}

/* Bordered containers become white cards */
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"][data-test-scroll-behavior] {{
    background: #FFFFFF;
    border: 1px solid #E2E8F0 !important;
    border-radius: 18px !important;
    box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 8px 24px rgba(15,23,42,.06);
}}

/* Buttons */
.stButton > button, .stDownloadButton > button {{
    border-radius: 12px; font-weight: 600; padding: 0.55rem 1.1rem;
    border: 1px solid #E2E8F0; transition: all .15s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
    border-color: {BRAND}; color: {BRAND}; transform: translateY(-1px);
}}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {BRAND} 0%, #7C3AED 100%);
    color: white; border: none; box-shadow: 0 6px 16px rgba(79,70,229,.35);
}}
.stButton > button[kind="primary"]:hover {{ color: white; filter: brightness(1.05); }}
.stButton > button:disabled {{ opacity: .55; transform: none; box-shadow: none; }}

/* File uploader */
[data-testid="stFileUploaderDropzone"] {{
    background: #F8FAFF; border: 1.5px dashed #C7D2FE; border-radius: 14px;
}}

/* Sidebar */
[data-testid="stSidebar"] {{ background: #FFFFFF; border-right: 1px solid #E2E8F0; }}

/* View switcher */
[data-testid="stButtonGroup"] button {{ border-radius: 999px !important; font-weight: 600; }}

/* ---- Custom pieces ---- */
.hero {{
    background: linear-gradient(135deg, #4338CA 0%, #6D28D9 55%, #DB2777 120%);
    border-radius: 24px; padding: 2rem 2.2rem; color: white; margin-bottom: 1.2rem;
    box-shadow: 0 18px 40px rgba(67,56,202,.28); position: relative; overflow: hidden;
}}
.hero::after {{
    content: ""; position: absolute; right: -60px; top: -60px; width: 260px; height: 260px;
    background: rgba(255,255,255,.08); border-radius: 50%;
}}
.hero h1 {{ color: white; font-size: 2.1rem; font-weight: 800; margin: 0 0 .35rem 0; }}
.hero p {{ color: rgba(255,255,255,.88); font-size: 1.02rem; margin: 0; max-width: 720px; }}
.badges {{ margin-top: 1rem; display: flex; gap: .5rem; flex-wrap: wrap; }}
.badge {{
    background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.25);
    padding: .3rem .75rem; border-radius: 999px; font-size: .82rem; font-weight: 600;
}}

.steps {{ display: flex; gap: .6rem; margin: .2rem 0 1.2rem 0; flex-wrap: wrap; }}
.step {{
    flex: 1; min-width: 150px; background: #FFFFFF; border: 1px solid #E2E8F0;
    border-radius: 14px; padding: .65rem .9rem; display: flex; align-items: center; gap: .6rem;
    color: {MUTED}; font-weight: 600; font-size: .9rem;
}}
.step .num {{
    width: 28px; height: 28px; border-radius: 50%; display: grid; place-items: center;
    background: #F1F5F9; color: {MUTED}; font-weight: 700; flex-shrink: 0;
}}
.step.done .num {{ background: #DCFCE7; color: #166534; }}
.step.active {{ border-color: {BRAND}; color: {INK}; box-shadow: 0 0 0 3px rgba(79,70,229,.12); }}
.step.active .num {{ background: {BRAND}; color: white; }}

.section-title {{ display: flex; align-items: center; gap: .6rem; margin: .1rem 0 .2rem 0; }}
.section-title .num {{
    width: 30px; height: 30px; border-radius: 10px; display: grid; place-items: center;
    background: #EEF2FF; color: {BRAND}; font-weight: 800;
}}
.section-title h3 {{ margin: 0; font-size: 1.15rem; }}
.section-sub {{ color: {MUTED}; font-size: .9rem; margin: 0 0 .6rem 2.6rem; }}

.stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: .9rem; margin: .4rem 0 1rem 0; }}
@media (max-width: 800px) {{ .stats {{ grid-template-columns: repeat(2, 1fr); }} }}
.stat {{
    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 18px; padding: 1.1rem 1.2rem;
    box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 8px 24px rgba(15,23,42,.05);
}}
.stat .icon {{
    width: 38px; height: 38px; border-radius: 12px; display: grid; place-items: center;
    font-size: 1.15rem; margin-bottom: .6rem;
}}
.stat .label {{ color: {MUTED}; font-size: .82rem; font-weight: 600; }}
.stat .value {{ color: {INK}; font-size: 1.75rem; font-weight: 800; letter-spacing: -0.02em; }}
.stat .hint {{ color: {MUTED}; font-size: .78rem; margin-top: .1rem; }}

.callout {{
    background: #EEF2FF; border: 1px solid #E0E7FF; border-radius: 14px;
    padding: .8rem 1rem; color: {INK}; font-size: .92rem; margin-bottom: .8rem;
}}
.callout.green {{ background: #F0FDF4; border-color: #DCFCE7; }}
.callout.amber {{ background: #FFFBEB; border-color: #FEF3C7; }}

.flag-head {{ display: flex; align-items: center; gap: .55rem; flex-wrap: wrap; }}
.pill {{
    display: inline-flex; align-items: center; gap: .3rem; padding: .22rem .65rem;
    border-radius: 999px; font-size: .78rem; font-weight: 700;
}}
.meta {{ color: {MUTED}; font-size: .85rem; }}
.who {{ color: {INK}; font-weight: 700; }}
.evidence {{ color: #334155; margin: .45rem 0 .1rem 0; font-size: .95rem; }}

.savings {{
    background: linear-gradient(135deg, #059669 0%, #10B981 100%); color: white;
    border-radius: 22px; padding: 1.6rem 1.8rem; box-shadow: 0 14px 32px rgba(5,150,105,.25);
    margin-bottom: 1rem;
}}
.savings .label {{ opacity: .9; font-weight: 600; }}
.savings .value {{ font-size: 2.8rem; font-weight: 800; letter-spacing: -0.03em; }}
.savings .hint {{ opacity: .9; font-size: .92rem; }}

.student-line {{ padding: .55rem 0; border-bottom: 1px solid #F1F5F9; }}
.student-line:last-child {{ border-bottom: none; }}
.grade-chip {{
    float: right; background: #EEF2FF; color: {BRAND_DARK}; font-weight: 800;
    border-radius: 10px; padding: .1rem .6rem;
}}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(mock_mode, model):
    mode = "🧪 Mock mode · free" if mock_mode else f"🤖 AI: {html.escape(model)}"
    st.markdown(f"""
    <div class="hero">
      <h1>📝 Peer Evaluation Agent</h1>
      <p>Fair individual grades from team peer reviews. Flags freeloaders, spite and
         gaming attempts, drafts feedback, and leaves every final decision to you.</p>
      <div class="badges">
        <span class="badge">{mode}</span>
        <span class="badge">🔒 Nothing is sent to students</span>
        <span class="badge">💸 Replaces a $9.50/student tool</span>
      </div>
    </div>""", unsafe_allow_html=True)


def steps(current):
    """Progress bar of the four steps. `current` is 1-4."""
    names = ["Load data", "Set project grades", "Run the agent", "Review & export"]
    parts = []
    for i, name in enumerate(names, start=1):
        state = "done" if i < current else "active" if i == current else ""
        mark = "✓" if i < current else str(i)
        parts.append(f'<div class="step {state}"><span class="num">{mark}</span>{name}</div>')
    st.markdown(f'<div class="steps">{"".join(parts)}</div>', unsafe_allow_html=True)


def section(number, title, subtitle=""):
    st.markdown(f'<div class="section-title"><span class="num">{number}</span>'
                f'<h3>{html.escape(title)}</h3></div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p class="section-sub">{subtitle}</p>', unsafe_allow_html=True)


def stat_cards(cards):
    """cards: list of (icon, tint, label, value, hint)."""
    html_cards = "".join(
        f'<div class="stat"><div class="icon" style="background:{tint}">{icon}</div>'
        f'<div class="label">{label}</div><div class="value">{value}</div>'
        f'<div class="hint">{hint}</div></div>'
        for icon, tint, label, value, hint in cards)
    st.markdown(f'<div class="stats">{html_cards}</div>', unsafe_allow_html=True)


def callout(text, kind=""):
    st.markdown(f'<div class="callout {kind}">{text}</div>', unsafe_allow_html=True)


def flag_header(flag):
    icon, name, bg, fg = FLAG_STYLES.get(flag["type"], ("🚩", flag["type"], "#F1F5F9", INK))
    st.markdown(
        f'<div class="flag-head">'
        f'<span class="pill" style="background:{bg};color:{fg}">{icon} {name}</span>'
        f'<span class="who">{html.escape(flag["student"])}</span>'
        f'<span class="meta">· Team {html.escape(flag["team"])} · found by '
        f'{html.escape(flag["source"])}</span></div>'
        f'<div class="evidence">{html.escape(flag["evidence"])}</div>',
        unsafe_allow_html=True)


def savings_card(saved, paid, cost, students):
    st.markdown(f"""
    <div class="savings">
      <div class="label">You save on this class</div>
      <div class="value">${saved:,.2f}</div>
      <div class="hint">The paid tool would cost ${paid:,.2f} ($9.50 × {students} students).
        This run cost ${cost:.4f}.</div>
    </div>""", unsafe_allow_html=True)


def student_line(name, grade, explanation):
    st.markdown(f'<div class="student-line"><span class="grade-chip">{grade:g}</span>'
                f'<b>{html.escape(name)}</b><br><span class="meta">'
                f'{html.escape(explanation)}</span></div>', unsafe_allow_html=True)
