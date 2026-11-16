"""
Peer Evaluation Agent
---------------------
Upload peer evaluations, set each team's project grade, click "Run Agent".

Files:
  app.py        - this file: the web page
  grading.py    - grade math (no AI)
  ai_review.py  - flags + feedback drafts (mock rules or a real AI model)
  ui.py         - colors, fonts and small pieces of HTML
  charts.py     - the charts

Run it with:   streamlit run app.py
"""

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

import ai_review as ai
import charts
import grading as g
import ui

load_dotenv()  # reads OPENROUTER_API_KEY and OPENROUTER_MODEL from .env
API_KEY, MODEL = ai.get_settings()

SAMPLE_FILE = "evaluations.csv"
SAMPLE_TEAM_GRADES = "team_grades.csv"
STRESS_FILE = "stress_test.csv"
STRESS_TEAM_GRADES = "stress_team_grades.csv"
GRADE_LABEL = "Project grade (before peer adjustment)"
GRADES_FILE = "adjusted_grades.csv"
REPORT_FILE = "flags_report.txt"
PAID_TOOL_PRICE = 9.50  # dollars per student for the paid peer-evaluation tool

st.set_page_config(page_title="Peer Evaluation Agent", page_icon="📝", layout="wide")
ui.inject_css()


# ---------------------------------------------------------------------------
# Sidebar: mode, API key and limits
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    if API_KEY:
        mock_mode = st.toggle("Mock mode (free, no API calls)", value=True)
        st.success("OpenRouter key found", icon="🔑")
    else:
        # Without a key the AI can't run, so mock mode stays on
        mock_mode = st.toggle("Mock mode (free, no API calls)", value=True, disabled=True,
                              help="Add an OpenRouter key to turn on the real AI.")
        st.info("No OpenRouter key yet, so the app runs in free mock mode.", icon="🔑")
        with st.expander("How to add your key"):
            st.markdown(
                "Get a key at [openrouter.ai/keys](https://openrouter.ai/keys), then:\n\n"
                "**On Streamlit Cloud:** open your app → **⋮ → Settings → Secrets** and "
                "paste:\n```toml\nOPENROUTER_API_KEY = \"sk-or-...\"\n```\n"
                "**On your computer:** copy `.env.example` to `.env` and put your key "
                "after `OPENROUTER_API_KEY=`.\n\n"
                "Then reload the app. Never put the key in the code or on GitHub.")
    st.caption("Mock mode uses simple built-in rules. Real mode sends each team's comments "
               f"to **{MODEL}** via OpenRouter." if not mock_mode or API_KEY else
               "Mock mode uses simple built-in rules. Nothing leaves your computer.")
    st.markdown("#### API limits")
    st.caption(f"• Max {ai.MAX_API_CALLS_PER_RUN} AI calls per run  \n"
               f"• Stops at ${ai.MAX_COST_PER_RUN:.2f} per run  \n"
               f"• Max {ai.MAX_OUTPUT_TOKENS} tokens per reply  \n"
               f"• Comments cut to {ai.MAX_COMMENT_CHARS} characters  \n"
               f"• Max {g.MAX_ROWS} rows per file")


# ---------------------------------------------------------------------------
# Step 1: choose the data
# ---------------------------------------------------------------------------

ui.hero(mock_mode, MODEL)
steps_slot = st.empty()  # filled in once we know how far along the professor is

# Built-in data you can load with one click (no upload needed)
DEMOS = {
    "sample": {"evaluations": SAMPLE_FILE, "team_grades": SAMPLE_TEAM_GRADES,
               "note": "the clean sample: 20 students in 5 teams with different "
                       "project grades."},
    "stress": {"evaluations": STRESS_FILE, "team_grades": STRESS_TEAM_GRADES,
               "note": "every edge case. After you run the agent, the Review queue shows "
                       "the teammate problems: freeloaders, spite, prompt injections, "
                       "collusion, score/comment mismatch and self-inflation."},
}

with st.container(border=True):
    ui.section(1, "Load your data",
               "Upload your peer evaluations, or try the app with built-in data.")
    col1, col2 = st.columns(2)
    with col1:
        uploaded = st.file_uploader("Peer evaluations CSV", type="csv")
    with col2:
        grades_upload = st.file_uploader("Optional: team_grades.csv (columns: team, grade)",
                                         type="csv")
    b1, b2, _ = st.columns([1, 1, 2])
    if b1.button("📄 Load sample data", width="stretch"):
        st.session_state["demo"] = "sample"
    if b2.button("🧪 Load stress-test data", width="stretch"):
        st.session_state["demo"] = "stress"

demo = DEMOS.get(st.session_state.get("demo"))

# Which evaluations file to use (an upload always wins)
source = None
if uploaded is not None:
    source, source_name, source_id = uploaded, uploaded.name, uploaded.file_id
elif demo:
    source = source_name = source_id = demo["evaluations"]

# Which team grades file to use (built-in data comes with its own)
grades_source, grades_id = None, "defaults"
if grades_upload is not None:
    grades_source, grades_id = grades_upload, grades_upload.file_id
elif demo and uploaded is None:
    grades_source = grades_id = demo["team_grades"]


# ---------------------------------------------------------------------------
# Step 2: project grade for each team
# ---------------------------------------------------------------------------

team_grades = None
run = False
if source is not None:
    with st.container(border=True):
        ui.section(2, "Set each team's project grade",
                   "One row per team found in the CSV. Click a grade to change it. Teams "
                   f"start at {g.DEFAULT_PROJECT_GRADE:g} unless team_grades.csv sets them.")
        if demo and uploaded is None and grades_upload is None:
            ui.callout(f"📂 Using <b>{source_name}</b> and <b>{grades_source}</b>: "
                       f"{demo['note']}")
        else:
            ui.callout(f"📂 Using <b>{source_name}</b>"
                       + (f" and <b>{grades_upload.name}</b>"
                          if grades_upload is not None else ""))
        try:
            preview_df, _ = g.load_evaluations(source)
            teams = sorted(preview_df["team"].unique())
            if grades_source is not None:
                filled, grade_problems = g.load_team_grades(grades_source, teams)
                if grade_problems and grades_source == STRESS_TEAM_GRADES:
                    # The stress-test file is broken on purpose, so these are expected
                    with st.expander(f"✅ The checks caught {len(grade_problems)} typing "
                                     f"mistakes in {STRESS_TEAM_GRADES}, as expected (this "
                                     "file is broken on purpose)"):
                        for p in grade_problems:
                            st.warning(p, icon="⚠️")
                else:
                    for p in grade_problems:
                        st.warning(p, icon="⚠️")
            else:
                filled = {t: g.DEFAULT_PROJECT_GRADE for t in teams}

            table = pd.DataFrame({"team": teams, GRADE_LABEL: [filled[t] for t in teams]})
            edited = st.data_editor(
                table, hide_index=True, num_rows="fixed", disabled=["team"], width="stretch",
                # a new evaluations or team grades file starts a fresh table
                key=f"grades_editor_{source_id}_{grades_id}",
                column_config={
                    "team": st.column_config.TextColumn("Team"),
                    GRADE_LABEL: st.column_config.NumberColumn(
                        GRADE_LABEL, min_value=0.0, max_value=100.0, step=0.5,
                        format="%.1f", required=True),
                })
            if edited[GRADE_LABEL].isna().any():
                st.error("Every team needs a project grade from 0 to 100.")
            else:
                team_grades = dict(zip(edited["team"], edited[GRADE_LABEL].astype(float)))
        except Exception as e:
            st.error(f"Could not read the file: {e}")

        run = st.button("🤖 Run Agent", type="primary", disabled=team_grades is None,
                        width="stretch")


# ---------------------------------------------------------------------------
# The agent
# ---------------------------------------------------------------------------

def run_agent(source, source_id, team_grades, mock_mode):
    with st.status("Agent is working...", expanded=True) as status:
        st.write("**Step 1:** Loading and cleaning the CSV...")
        df, problems = g.load_evaluations(source)
        for p in problems:
            st.write(f"⚠️ {p}")
        st.write(f"✅ {len(df)} usable ratings for "
                 f"{g.peer_ratings(df)['evaluatee'].nunique()} students.")

        st.write("**Step 2:** Checking for retaliation and computing grades...")
        outliers = g.find_outlier_evaluators(df)
        grades_before = g.compute_grades(df, team_grades)
        grades = g.compute_grades(df, team_grades, exclude=outliers)
        for (team, evaluator), gap in outliers.items():
            st.write(f"⚠️ Left out {evaluator}'s ratings (team {team}): "
                     f"{abs(gap)} points below teammates.")
        st.write(f"✅ Grades computed. {int(grades['below_floor'].sum())} grade(s) "
                 "below the 50% floor need your confirmation.")

        label = "rules (mock mode)" if mock_mode else MODEL
        st.write(f"**Step 3:** Reviewing comments with {label}...")
        flags, feedback, total_cost, calls = [], {}, 0.0, 0
        for team, rows in df.groupby("team"):
            team_outliers = {e: gap for (t, e), gap in outliers.items() if t == team}
            rule_flags, rule_fb, cost = ai.review_team_mock(rows, team_outliers)
            for f in rule_flags:
                f["source"] = "rules"
            if mock_mode:
                team_flags, team_fb = rule_flags, rule_fb
            elif calls >= ai.MAX_API_CALLS_PER_RUN or total_cost >= ai.MAX_COST_PER_RUN:
                st.write(f"⛔ Team {team}: API limit reached, using rules only.")
                team_flags, team_fb = rule_flags, rule_fb
            else:
                ai_flags, team_fb, cost = ai.review_team_ai(team, rows, team_outliers,
                                                            API_KEY, MODEL)
                calls += 1
                if ai_flags is None:
                    st.write(f"⚠️ Team {team}: the AI reply couldn't be read, using rules only.")
                    ai_flags, team_fb = [], rule_fb
                for f in ai_flags:
                    f["source"] = "AI"
                # Backstop: add anything the rules caught that the AI missed
                found = {(f["type"], f["student"]) for f in ai_flags}
                missed = [dict(f, source="rules backstop") for f in rule_flags
                          if (f["type"], f["student"]) not in found]
                team_flags = ai_flags + missed
            total_cost += cost
            for f in team_flags:
                f["team"] = team
                f["id"] = f"{team}|{f['type']}|{f['student']}"
            flags += team_flags
            feedback.update({(team, name): text for name, text in team_fb.items()})
            extra = sum(f["source"] == "rules backstop" for f in team_flags)
            st.write(f"✅ Team {team}: {len(team_flags)} flag(s)"
                     + (f" ({extra} added by the rules backstop)" if extra else ""))

        st.write("**Step 4:** Saving the flags report...")
        status.update(label="Agent finished! Review the results below.",
                      state="complete", expanded=False)

    st.session_state["run_id"] = st.session_state.get("run_id", 0) + 1
    st.session_state["results"] = {
        "df": df, "grades": grades, "grades_before": grades_before,
        "outliers": outliers, "flags": flags, "feedback": feedback,
        "cost": total_cost, "calls": calls, "mock": mock_mode,
        "team_grades": team_grades, "problems": problems, "source_id": source_id,
    }
    with open(REPORT_FILE, "w") as f:
        f.write(build_report(st.session_state["results"], {}))


def build_report(results, decisions):
    lines = ["PEER EVALUATION FLAGS REPORT", "=" * 40,
             "Project grades (before peer adjustment): " + ", ".join(f"{t} {v:g}" for t, v in
                                             sorted(results["team_grades"].items())),
             f"Mode: {'mock (rules)' if results['mock'] else MODEL}",
             f"Total API cost: ${results['cost']:.6f}", ""]
    if results["outliers"]:
        lines.append("Ratings left out (retaliation check):")
        for (team, evaluator), gap in results["outliers"].items():
            lines.append(f"  Team {team}: {evaluator} ({abs(gap)} points below teammates)")
        lines.append("")
    for team in sorted(results["grades"]["team"].unique()):
        lines.append(f"Team {team}")
        team_flags = [f for f in results["flags"] if f["team"] == team]
        if not team_flags:
            lines.append("  No flags.")
        for f in team_flags:
            d = decisions.get(f["id"], "Pending")
            lines.append(f"  [{f['type'].upper()}] {f['student']}: {f['evidence']}  "
                         f"(found by {f['source']}) -> {d.upper()}")
        lines.append("")
    return "\n".join(lines)


if run:
    try:
        run_agent(source, source_id, team_grades, mock_mode)
    except requests.HTTPError as e:
        st.error(f"OpenRouter request failed: {e.response.status_code} "
                 f"{e.response.text[:300]}")
    except Exception as e:
        st.error(f"Something went wrong: {e}")


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

results = st.session_state.get("results")
# Results from a different evaluations file are out of date: hide them
if results and (source is None or results.get("source_id") != source_id):
    st.session_state.pop("results")
    results = None
if not results:
    with steps_slot:
        ui.steps(1 if source is None else 2)
    st.stop()

rid = st.session_state["run_id"]  # makes widget keys fresh for every run

# Streamlit forgets a widget's value when it isn't on screen. Re-saving these keys
# keeps review decisions and feedback approvals when you switch views.
for key in list(st.session_state.keys()):
    if key.startswith(("flag_", "floor_", "fbtext_", "fbok_")):
        st.session_state[key] = st.session_state[key]
flags = results["flags"]
base_grades = results["grades"]

# Professor decisions (read from the review widgets below)
decisions = {f["id"]: st.session_state.get(f"flag_{rid}_{f['id']}", "Pending") for f in flags}
# Grades below the floor, as (team, student) pairs
floor_students = list(base_grades[base_grades["below_floor"]][["team", "student"]]
                      .itertuples(index=False, name=None))
floor_choice = {(t, s): st.session_state.get(f"floor_{rid}_{t}_{s}", "Pending")
                for t, s in floor_students}
confirmed = {key for key, c in floor_choice.items() if c.startswith("Confirm")}

grades = g.apply_floor_decisions(base_grades, confirmed)
excluded_by_team = {}
for (team, evaluator) in results["outliers"]:
    excluded_by_team.setdefault(team, []).append(evaluator)
grades["explanation"] = [g.explain(row, excluded_by_team.get(row["team"], []), confirmed)
                         for _, row in grades.iterrows()]

pending = (sum(d == "Pending" for d in decisions.values())
           + sum(c == "Pending" for c in floor_choice.values()))
total_items = len(decisions) + len(floor_choice)
paid = PAID_TOOL_PRICE * len(grades)

with steps_slot:
    ui.steps(4 if pending else 5)

st.markdown("## Results")
ui.stat_cards([
    ("👥", "#EEF2FF", "Students graded", len(grades),
     f"{grades['team'].nunique()} teams"),
    ("🎓", "#F0FDF4", "Average final grade", f"{grades['adjusted_grade'].mean():.1f}",
     f"lowest {grades['adjusted_grade'].min():g} · highest {grades['adjusted_grade'].max():g}"),
    ("📝", "#FEF3C7", "Left to review", pending,
     "all done, grades unlocked ✓" if pending == 0 else f"of {total_items} items"),
    ("💸", "#DCFCE7", "You save", f"${paid - results['cost']:,.0f}",
     f"vs. ${PAID_TOOL_PRICE:.2f}/student tool"),
])

# A view switcher (it remembers its choice when you click things, unlike st.tabs)
VIEWS = ["📊 Grades", "🛡️ Retaliation fix", "✅ Review queue", "✉️ Feedback drafts", "💰 Cost"]
view = st.segmented_control("View", VIEWS, default=VIEWS[0], key="view", required=True,
                            label_visibility="collapsed") or VIEWS[0]
flag_names = {k: v[1] for k, v in ui.FLAG_STYLES.items()}

# ---- Grades ---------------------------------------------------------------
if view == VIEWS[0]:
    left, right = st.columns([3, 2])
    with left:
        with st.container(border=True):
            st.markdown("### Final grades")
            st.caption("Bars show each student's final grade. The dark tick is the team's "
                       "project grade, so you can see who landed above or below it. "
                       "Hover a bar for details.")
            st.altair_chart(charts.grades_chart(grades), width="stretch", theme=None)
    with right:
        with st.container(border=True):
            st.markdown("### Teams")
            overview = (grades.groupby("team")
                        .agg(project=("project_grade", "first"),
                             average=("adjusted_grade", "mean"),
                             lowest=("adjusted_grade", "min"))
                        .reset_index())
            overview["flags"] = [sum(f["team"] == t for f in flags) for t in overview["team"]]
            st.dataframe(overview, hide_index=True, width="stretch",
                         column_config={
                             "team": "Team", "project": st.column_config.NumberColumn(
                                 "Project", format="%.0f"),
                             "average": st.column_config.NumberColumn("Avg final",
                                                                      format="%.1f"),
                             "lowest": st.column_config.NumberColumn("Lowest",
                                                                     format="%.1f"),
                             "flags": "Flags"})
        if flags:
            with st.container(border=True):
                st.markdown("### Flags by kind")
                st.altair_chart(charts.flags_chart(flags, flag_names), width="stretch",
                                theme=None)

    with st.container(border=True):
        st.markdown("### 💬 Why each student got their grade")
        for team, rows in grades.groupby("team"):
            with st.expander(f"Team {team}  ·  project grade {rows['project_grade'].iloc[0]:g}"):
                for _, row in rows.iterrows():
                    ui.student_line(row["student"], row["adjusted_grade"], row["explanation"])

    with st.expander("📋 All grades as a table"):
        st.dataframe(grades[["team", "student", "project_grade", "avg_received", "team_avg",
                             "calculated_grade", "adjusted_grade"]],
                     hide_index=True, width="stretch",
                     column_config={
                         "team": "Team", "student": "Student",
                         "project_grade": "Project grade", "avg_received": "Avg received",
                         "team_avg": "Team avg", "calculated_grade": "Calculated",
                         "adjusted_grade": "Final grade"})

# ---- Retaliation fix ------------------------------------------------------
if view == VIEWS[1]:
    ui.callout(f"🛡️ Evaluators who score teammates <b>{g.OUTLIER_GAP}+ points below</b> what "
               "the rest of the team gave the same people are left out. No grade can fall "
               "below <b>50% of its team's project grade</b> unless you confirm it in the "
               "Review queue.")
    if not results["outliers"]:
        ui.callout("✅ No evaluators were left out in this class.", "green")
    for team in sorted(excluded_by_team):
        with st.container(border=True):
            st.markdown(f"### Team {team}: before and after")
            st.caption(f"Left out: {', '.join(excluded_by_team[team])}. Gray dot = before, "
                       "blue dot = after.")
            before = results["grades_before"]
            before = before[before["team"] == team][["student", "adjusted_grade"]]
            after = grades[grades["team"] == team][["student", "adjusted_grade"]]
            compare = before.merge(after, on="student", suffixes=("_before", "_after"))
            compare = compare.rename(columns={"adjusted_grade_before": "Before",
                                              "adjusted_grade_after": "After"})
            compare["Change"] = (compare["After"] - compare["Before"]).round(1)
            c1, c2 = st.columns([3, 2])
            with c1:
                st.altair_chart(charts.before_after_chart(compare), width="stretch",
                                theme=None)
            with c2:
                st.dataframe(compare, hide_index=True, width="stretch",
                             column_config={"student": "Student"})

# ---- Review queue ---------------------------------------------------------
if view == VIEWS[2]:
    with st.container(border=True):
        done = total_items - pending
        st.markdown(f"### {done} of {total_items} reviewed")
        st.progress(done / total_items if total_items else 1.0)
        st.caption("The grades file unlocks when every item below has a decision.")

    if floor_students:
        with st.container(border=True):
            st.markdown("### ⚖️ Grades below the 50% floor")
            for t, s in floor_students:
                row = grades[(grades["team"] == t) & (grades["student"] == s)].iloc[0]
                st.radio(f"**{s}** (Team {t}, project grade {row['project_grade']:g}): "
                         f"calculated {row['calculated_grade']}, floor {row['floor']:g}",
                         ["Pending", f"Keep at floor ({row['floor']:g})",
                          f"Confirm lower grade ({row['calculated_grade']})"],
                         key=f"floor_{rid}_{t}_{s}", horizontal=True)

    st.markdown("### 🚩 Flags")
    if not flags:
        ui.callout("✅ No flags to review.", "green")
    for f in flags:
        with st.container(border=True):
            ui.flag_header(f)
            st.radio("Decision", ["Pending", "Approve", "Override"],
                     key=f"flag_{rid}_{f['id']}", horizontal=True,
                     label_visibility="collapsed")

    report = build_report(results, decisions)
    out = grades.copy()
    out["floor_status"] = ["" if not r["below_floor"] else
                           ("confirmed lower grade" if (r["team"], r["student"]) in confirmed
                            else "kept at floor")
                           for _, r in out.iterrows()]
    out["approved_flags"] = ["; ".join(f["type"] for f in flags
                                       if decisions[f["id"]] == "Approve"
                                       and f["student"] in (r["student"], ai.WHOLE_TEAM)
                                       and f["team"] == r["team"])
                             for _, r in out.iterrows()]
    out = out[["team", "student", "project_grade", "avg_received", "ratings_used",
               "team_avg", "ratio", "calculated_grade", "floor", "adjusted_grade",
               "floor_status", "approved_flags", "explanation"]]

    with st.container(border=True):
        st.markdown("### ⬇️ Export")
        d1, d2 = st.columns(2)
        if pending == 0:
            out.to_csv(GRADES_FILE, index=False)
            with open(REPORT_FILE, "w") as fh:
                fh.write(report)
            d1.download_button("⬇️ Download adjusted_grades.csv", out.to_csv(index=False),
                               GRADES_FILE, "text/csv", width="stretch", type="primary")
        else:
            d1.button(f"🔒 adjusted_grades.csv — review {pending} more item(s)",
                      disabled=True, width="stretch")
        d2.download_button("⬇️ Download flags_report.txt", report, REPORT_FILE, "text/plain",
                           width="stretch")

# ---- Feedback drafts ------------------------------------------------------
if view == VIEWS[3]:
    ui.callout("📭 <b>Nothing is ever sent.</b> This app cannot email or message anyone. "
               "Edit and approve the drafts, then download the approved ones to share "
               "yourself.")
    approved = []
    for team, rows in grades.groupby("team"):
        st.markdown(f"### Team {team}")
        cols = st.columns(2)
        for i, (_, row) in enumerate(rows.iterrows()):
            name = row["student"]
            key = f"fbtext_{rid}_{team}_{name}"
            if key not in st.session_state:  # first time: start from the draft
                st.session_state[key] = results["feedback"].get((team, name), "") or "(no draft)"
            with cols[i % 2]:
                with st.container(border=True):
                    text = st.text_area(f"✉️ {name}", key=key, height=130)
                    if st.checkbox("Approve", key=f"fbok_{rid}_{team}_{name}"):
                        approved.append(f"To: {name} (Team {team})\n{text}\n")
    with st.container(border=True):
        st.markdown(f"**{len(approved)} of {len(grades)} drafts approved.**")
        st.download_button("⬇️ Download approved feedback",
                           "\n".join(approved) or "None approved.",
                           "approved_feedback.txt", "text/plain", disabled=not approved)

# ---- Cost -----------------------------------------------------------------
if view == VIEWS[4]:
    ui.savings_card(paid - results["cost"], paid, results["cost"], len(grades))
    mode = ("mock mode (no API calls)" if results["mock"]
            else f"{results['calls']} call(s) to {MODEL}")
    ui.stat_cards([
        ("🧾", "#EEF2FF", "This run", f"${results['cost']:.4f}", mode),
        ("🏷️", "#FEE2E2", "Paid tool", f"${paid:,.2f}",
         f"${PAID_TOOL_PRICE:.2f} × {len(grades)} students"),
        ("📞", "#F1F5F9", "AI calls", results["calls"],
         f"limit {ai.MAX_API_CALLS_PER_RUN} per run"),
        ("🛑", "#FEF3C7", "Spending cap", f"${ai.MAX_COST_PER_RUN:.2f}", "per run"),
    ])
