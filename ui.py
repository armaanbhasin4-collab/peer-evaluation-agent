"""
ui.py - the look of GroupGrade: notebook paper, red pen, ink blue, pencil yellow.

Colors and fonts that Streamlit can set itself are in .streamlit/config.toml.
This file adds the rest: ruled paper, the chalkboard header, index cards and
the gradebook table. All text from a CSV or the AI goes through html.escape().
"""

import html

import streamlit as st

# The palette from the pitch deck
CREAM = "#FBF8F1"
SIDEBAR = "#F3EFE3"
INK_TEXT = "#1F2A3A"
RED_PEN = "#C2402A"
INK_BLUE = "#2A55B8"
PENCIL = "#F5C242"
CHALKBOARD = "#1F3B34"
MUTED = "#5B6577"

# Each kind of flag gets an icon, a friendly name, and badge colors
FLAG_STYLES = {
    "freeloader":     ("💤", "Freeloader",     "#FDF1D2", "#8A5A00"),
    "retaliation":    ("😠", "Retaliation",    "#F9E1DC", "#9A2F1D"),
    "manipulation":   ("🕵️", "Manipulation",   "#E7ECF8", "#1F3F8A"),
    "collusion":      ("🤝", "Collusion",      "#E3EEF0", "#1F4D57"),
    "mismatch":       ("🔀", "Score mismatch", "#F6E4EC", "#7D2350"),
    "self_inflation": ("🎈", "Self-inflation", "#E6F0E4", "#2D5A27"),
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Caveat:wght@500;700&family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&display=swap');

/* ---- Notebook paper: faint blue ruled lines and a red margin line ---- */
.stApp {{ background: {CREAM}; }}
[data-testid="stMain"] {{
    background-color: {CREAM};
    background-image:
      linear-gradient(90deg, transparent 46px, rgba(194,64,42,.45) 46px,
                      rgba(194,64,42,.45) 48px, transparent 48px),
      repeating-linear-gradient(180deg, transparent 0, transparent 31px,
                                rgba(42,85,184,.09) 31px, rgba(42,85,184,.09) 32px);
    background-attachment: local;
}}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.6rem; max-width: 1200px; }}
[data-testid="stSidebar"] {{ background: {SIDEBAR}; border-right: 1px solid #E4DCC8; }}
h1, h2, h3, h4 {{ font-family: 'Fraunces', Georgia, serif; color: {INK_TEXT};
                  letter-spacing: -0.01em; }}

/* Bordered containers: plain white cards */
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"][data-test-scroll-behavior] {{
    background: #FFFFFF; border: 1px solid #E9E2D0 !important; border-radius: 14px !important;
    box-shadow: 0 1px 2px rgba(31,42,58,.04), 0 6px 18px rgba(31,42,58,.06);
}}
/* ...and index cards: a 6px red (flags) or blue (feedback) top border.
   (Same element as the white card above, so the selector repeats it to win.) */
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"][data-test-scroll-behavior][class*="st-key-flagcard"],
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"][data-test-scroll-behavior][class*="st-key-fbcard"] {{
    border: none !important; border-radius: 6px !important;
    box-shadow: 0 2px 4px rgba(31,42,58,.06), 0 10px 24px rgba(31,42,58,.08) !important;
}}
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"][data-test-scroll-behavior][class*="st-key-flagcard"] {{
    border-top: 6px solid {RED_PEN} !important;
}}
[data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"][data-test-scroll-behavior][class*="st-key-fbcard"] {{
    border-top: 6px solid {INK_BLUE} !important;
}}

/* Buttons: red pen primary, ink blue secondary */
.stButton > button, .stDownloadButton > button {{
    border-radius: 10px; font-weight: 600; border: 1.5px solid #D9CFB8;
    background: #FFFFFF; color: {INK_BLUE}; transition: all .15s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
    border-color: {INK_BLUE}; color: {INK_BLUE}; transform: translateY(-1px);
}}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
    background: {RED_PEN}; color: #FFFFFF; border: none;
    box-shadow: 0 6px 14px rgba(194,64,42,.28);
}}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {{
    background: #A93522; color: #FFFFFF;
}}
.stButton > button:disabled {{ opacity: .55; transform: none; box-shadow: none; }}
[data-testid="stFileUploaderDropzone"] {{
    background: #FFFDF7; border: 1.5px dashed #D9CFB8; border-radius: 12px;
}}
[data-testid="stButtonGroup"] button {{ border-radius: 999px !important; font-weight: 600; }}

/* ---- Chalkboard header ---- */
.hero {{
    background:
      radial-gradient(600px 200px at 20% 0%, rgba(255,255,255,.07), transparent 70%),
      radial-gradient(400px 160px at 90% 100%, rgba(255,255,255,.05), transparent 70%),
      {CHALKBOARD};
    border-radius: 16px; padding: 1.8rem 2.1rem 1.6rem; color: #F4F1E8;
    margin-bottom: 1.1rem; box-shadow: 0 14px 30px rgba(31,59,52,.28);
    border-bottom: 6px solid #2C4F46;
}}
.hero h1 {{ font-family: 'Fraunces', Georgia, serif; color: #FBF8F1; font-size: 2.4rem;
            font-weight: 700; margin: 0 0 .3rem 0; letter-spacing: -0.02em; }}
.hero p {{ font-family: 'Inter', sans-serif; color: rgba(244,241,232,.86);
           font-size: 1rem; margin: 0; max-width: 700px; }}
.hero .note {{ font-family: 'Caveat', cursive; color: {PENCIL}; font-size: 1.55rem;
               margin-top: .5rem; transform: rotate(-1.5deg); display: inline-block; }}
.badges {{ margin-top: .9rem; display: flex; gap: .5rem; flex-wrap: wrap; }}
.badge {{ font-family: 'Inter', sans-serif; border: 1.5px dashed rgba(244,241,232,.45);
          color: #F4F1E8; padding: .25rem .7rem; border-radius: 999px;
          font-size: .8rem; font-weight: 600; }}

/* ---- Steps ---- */
.steps {{ display: flex; gap: .6rem; margin: .2rem 0 1.1rem 0; flex-wrap: wrap;
          font-family: 'Inter', sans-serif; }}
.step {{ flex: 1; min-width: 150px; background: #FFFFFF; border: 1px solid #E9E2D0;
         border-radius: 12px; padding: .6rem .85rem; display: flex; align-items: center;
         gap: .6rem; color: {MUTED}; font-weight: 600; font-size: .9rem; }}
.step .num {{ width: 28px; height: 28px; border-radius: 50%; display: grid; place-items: center;
              background: {SIDEBAR}; color: {MUTED}; font-weight: 700; flex-shrink: 0; }}
.step.done .num {{ background: #E7ECF8; color: {INK_BLUE}; }}
.step.active {{ border-color: {RED_PEN}; color: {INK_TEXT};
                box-shadow: 0 0 0 3px rgba(194,64,42,.12); }}
.step.active .num {{ background: {RED_PEN}; color: #FFFFFF; }}

.section-title {{ display: flex; align-items: center; gap: .6rem; margin: .1rem 0 .2rem 0; }}
.section-title .num {{ width: 30px; height: 30px; border-radius: 50%; display: grid;
    place-items: center; border: 2px solid {RED_PEN}; color: {RED_PEN};
    font-family: 'Fraunces', serif; font-weight: 700; }}
.section-title h3 {{ margin: 0; font-size: 1.2rem; }}
.section-sub {{ font-family: 'Inter', sans-serif; color: {MUTED}; font-size: .9rem;
                margin: 0 0 .6rem 2.6rem; }}

/* ---- Stat tiles ---- */
.stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: .9rem; margin: .4rem 0 1rem 0;
          font-family: 'Inter', sans-serif; }}
@media (max-width: 800px) {{ .stats {{ grid-template-columns: repeat(2, 1fr); }} }}
.stat {{ background: #FFFFFF; border: 1px solid #E9E2D0; border-radius: 14px;
         padding: 1rem 1.15rem; box-shadow: 0 6px 18px rgba(31,42,58,.05); }}
.stat .icon {{ width: 36px; height: 36px; border-radius: 10px; display: grid; place-items: center;
               font-size: 1.1rem; margin-bottom: .55rem; }}
.stat .label {{ color: {MUTED}; font-size: .8rem; font-weight: 600; }}
.stat .value {{ font-family: 'Fraunces', serif; color: {INK_TEXT}; font-size: 1.8rem;
                font-weight: 700; }}
.stat .hint {{ color: {MUTED}; font-size: .78rem; }}

/* ---- Notes ---- */
.callout {{ font-family: 'Inter', sans-serif; background: #FFF6D9; border-left: 4px solid {PENCIL};
            border-radius: 8px; padding: .75rem 1rem; color: {INK_TEXT}; font-size: .92rem;
            margin-bottom: .8rem; }}
.callout.green {{ background: #E7ECF8; border-left-color: {INK_BLUE}; }}
.scribble {{ font-family: 'Caveat', cursive; color: {RED_PEN}; font-size: 1.45rem;
             transform: rotate(-1deg); display: inline-block; margin: .1rem 0 .4rem .2rem; }}

/* ---- Flag cards ---- */
.flag-head {{ display: flex; align-items: center; gap: .55rem; flex-wrap: wrap;
              font-family: 'Inter', sans-serif; }}
.pill {{ display: inline-flex; align-items: center; gap: .3rem; padding: .2rem .6rem;
         border-radius: 999px; font-size: .76rem; font-weight: 700; }}
.meta {{ color: {MUTED}; font-size: .84rem; font-family: 'Inter', sans-serif; }}
.who {{ font-family: 'Fraunces', serif; color: {INK_TEXT}; font-weight: 700; font-size: 1.05rem; }}
.evidence {{ font-family: 'Inter', sans-serif; color: #33404F; margin: .45rem 0 .1rem 0;
             font-size: .94rem; }}

/* ---- Index cards (explanations) ---- */
.cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: .9rem;
          margin-bottom: .4rem; }}
.index-card {{
    background-color: #FFFFFF;
    background-image: repeating-linear-gradient(180deg, transparent 0, transparent 25px,
                      rgba(42,85,184,.08) 25px, rgba(42,85,184,.08) 26px);
    background-position: 0 44px;
    border-top: 6px solid {INK_BLUE}; border-radius: 6px; padding: .8rem 1rem 1rem;
    box-shadow: 0 2px 4px rgba(31,42,58,.06), 0 10px 24px rgba(31,42,58,.08);
    font-family: 'Inter', sans-serif;
}}
.index-card .top {{ display: flex; justify-content: space-between; align-items: center;
                    border-bottom: 1.5px solid rgba(194,64,42,.45); padding-bottom: .35rem;
                    margin-bottom: .45rem; }}
.index-card .name {{ font-family: 'Fraunces', serif; font-weight: 700; font-size: 1.05rem;
                     color: {INK_TEXT}; }}
.index-card .body {{ color: #33404F; font-size: .88rem; line-height: 26px; }}
.circled {{ border: 2px solid {RED_PEN}; color: {RED_PEN}; border-radius: 999px;
            padding: .1rem .6rem; font-family: 'Fraunces', serif; font-size: 1rem;
            font-weight: 700; line-height: 1.3; }}

/* ---- Gradebook table ---- */
.gradebook-wrap {{ overflow-x: auto; }}
table.gradebook {{ width: 100%; border-collapse: collapse; background: #FFFFFF;
                   font-family: 'Inter', sans-serif; font-size: .88rem; color: {INK_TEXT}; }}
table.gradebook th {{ font-family: 'Fraunces', serif; font-weight: 600; text-align: right;
                      color: {INK_BLUE}; padding: .55rem .7rem; background: {SIDEBAR};
                      border-bottom: 2px solid {INK_BLUE}; white-space: nowrap; }}
table.gradebook td {{ padding: .42rem .7rem; text-align: right;
                      border-bottom: 1px solid rgba(42,85,184,.16); }}
table.gradebook th.left, table.gradebook td.left {{ text-align: left; }}
table.gradebook td.team {{ color: {MUTED}; font-weight: 600; }}
table.gradebook td.name, table.gradebook th.name {{ border-right: 2px solid rgba(194,64,42,.55); }}
table.gradebook tr.first td {{ border-top: 1.5px solid rgba(42,85,184,.35); }}
table.gradebook td.final {{ font-weight: 700; color: {RED_PEN}; }}
table.gradebook td.held {{ background: rgba(245,194,66,.30); }}
table.gradebook tbody tr:hover td {{ background: #FFFBEF; }}
.legend-note {{ font-family: 'Inter', sans-serif; color: {MUTED}; font-size: .8rem;
                margin-top: .45rem; }}

/* ---- Savings card (chalkboard) ---- */
.savings {{ background: {CHALKBOARD}; color: #F4F1E8; border-radius: 16px; padding: 1.5rem 1.8rem;
            box-shadow: 0 14px 30px rgba(31,59,52,.25); margin-bottom: 1rem;
            font-family: 'Inter', sans-serif; border-bottom: 6px solid #2C4F46; }}
.savings .label {{ opacity: .85; font-weight: 600; }}
.savings .value {{ font-family: 'Fraunces', serif; font-size: 2.8rem; font-weight: 700;
                   color: {PENCIL}; }}
.savings .hint {{ opacity: .85; font-size: .92rem; }}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(mock_mode, model):
    mode = "🧪 Mock mode · free" if mock_mode else f"🤖 AI: {html.escape(model)}"
    st.markdown(f"""
    <div class="hero">
      <h1>GroupGrade</h1>
      <p>Fair individual grades from team peer reviews. Flags freeloaders, spite and
         gaming attempts, drafts feedback, and leaves every final decision to you.</p>
      <div class="note">no more $9.50 per student ✓</div>
      <div class="badges">
        <span class="badge">{mode}</span>
        <span class="badge">🔒 Nothing is sent to students</span>
      </div>
    </div>""", unsafe_allow_html=True)


def steps(current):
    """Progress bar of the four steps. `current` is 1-4 (5 = everything done)."""
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


def scribble(text):
    """A short handwritten-style note (used sparingly)."""
    st.markdown(f'<div class="scribble">{html.escape(text)}</div>', unsafe_allow_html=True)


def flag_header(flag):
    icon, name, bg, fg = FLAG_STYLES.get(flag["type"], ("🚩", flag["type"], SIDEBAR, INK_TEXT))
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


def explanation_cards(rows):
    """White index cards, one per student: name, circled grade, and the explanation."""
    cards = "".join(
        f'<div class="index-card"><div class="top"><span class="name">'
        f'{html.escape(r["student"])}</span><span class="circled">{r["adjusted_grade"]:g}'
        f'</span></div><div class="body">{html.escape(r["explanation"])}</div></div>'
        for _, r in rows.iterrows())
    st.markdown(f'<div class="cards">{cards}</div>', unsafe_allow_html=True)


def gradebook(grades):
    """The grades as a paper gradebook: team groups, a red margin after the name."""
    head = ("<tr><th class='left'>Team</th><th class='left name'>Student</th>"
            "<th>Project</th><th>Avg received</th><th>Team avg</th>"
            "<th>Calculated</th><th>Final</th></tr>")
    body, last_team = [], None
    for _, r in grades.iterrows():
        first = r["team"] != last_team
        last_team = r["team"]
        held = (" held" if r["below_floor"] and r["adjusted_grade"] != r["calculated_grade"]
                else "")
        body.append(
            f"<tr class='{'first' if first else ''}'>"
            f"<td class='left team'>{html.escape(r['team']) if first else ''}</td>"
            f"<td class='left name'>{html.escape(r['student'])}</td>"
            f"<td>{r['project_grade']:g}</td><td>{r['avg_received']:.2f}</td>"
            f"<td>{r['team_avg']:.2f}</td><td>{r['calculated_grade']:.1f}</td>"
            f"<td class='final{held}'>{r['adjusted_grade']:.1f}</td></tr>")
    st.markdown(f"<div class='gradebook-wrap'><table class='gradebook'><thead>{head}</thead>"
                f"<tbody>{''.join(body)}</tbody></table></div>"
                "<div class='legend-note'>Final grades are in red pen. A yellow highlight "
                "means the grade is held at the 50% floor until you decide in the Review "
                "queue.</div>", unsafe_allow_html=True)


def team_gradebook(overview):
    """Small gradebook with one row per team."""
    rows = "".join(
        f"<tr><td class='left name'>{html.escape(r['team'])}</td><td>{r['project']:g}</td>"
        f"<td class='final'>{r['average']:.1f}</td><td>{r['lowest']:.1f}</td>"
        f"<td>{r['flags']}</td></tr>"
        for _, r in overview.iterrows())
    st.markdown("<div class='gradebook-wrap'><table class='gradebook'><thead><tr>"
                "<th class='left name'>Team</th><th>Project</th><th>Avg final</th>"
                f"<th>Lowest</th><th>Flags</th></tr></thead><tbody>{rows}</tbody></table>"
                "</div>", unsafe_allow_html=True)
