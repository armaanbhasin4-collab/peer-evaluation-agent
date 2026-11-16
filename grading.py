"""
grading.py - all the grade math. No AI here, so results are exact and repeatable.

The steps:
  1. load_evaluations()       clean up the CSV
  2. find_outlier_evaluators() spot evaluators who score far below their team (retaliation)
  3. compute_grades()          team's project grade x (student avg / team avg), capped
                               at 100, with a floor of 50% of the team's project grade
  4. explain()                 a plain-English sentence for each student

Each team can have its own project grade (see load_team_grades()).
"""

import pandas as pd

REQUIRED_COLUMNS = ["team", "evaluator", "evaluatee", "score", "comment"]

# An evaluator is left out if, on average, they score teammates this many
# points LOWER than everyone else on the team scored the same people.
OUTLIER_GAP = 1.5

# No grade can drop below this share of the team's project grade unless the professor
# confirms it.
FLOOR_SHARE = 0.5

DEFAULT_PROJECT_GRADE = 85.0  # used for any team without a grade

MAX_ROWS = 5000  # refuse giant files


def load_evaluations(file):
    """Read and clean the CSV. Returns (clean_df, list_of_problems_found)."""
    if hasattr(file, "seek"):  # an uploaded file can be read more than once
        file.seek(0)
    df = pd.read_csv(file, dtype=str, keep_default_na=False)
    df.columns = [c.strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing these columns: {', '.join(missing)}")
    if len(df) > MAX_ROWS:
        raise ValueError(f"CSV has {len(df)} rows; the limit is {MAX_ROWS}.")

    problems = []
    for col in ["team", "evaluator", "evaluatee", "comment"]:
        df[col] = df[col].astype(str).str.strip()

    # Rows with no names
    blank = (df["team"] == "") | (df["evaluator"] == "") | (df["evaluatee"] == "")
    if blank.any():
        problems.append(f"Dropped {blank.sum()} row(s) with a missing team or name.")
    df = df[~blank]

    # Scores must be whole numbers 1-5
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    bad = df["score"].isna() | (df["score"] < 1) | (df["score"] > 5) | (df["score"] % 1 != 0)
    if bad.any():
        problems.append(f"Dropped {bad.sum()} row(s) with a missing or invalid score "
                        "(scores must be 1-5).")
    df = df[~bad]

    # Same evaluator rating the same person twice: keep the last one
    dupes = df.duplicated(subset=["team", "evaluator", "evaluatee"], keep="last")
    if dupes.any():
        problems.append(f"Dropped {dupes.sum()} duplicate rating(s) (kept the latest).")
    df = df[~dupes]

    df["score"] = df["score"].astype(int)
    self_count = (df["evaluator"] == df["evaluatee"]).sum()
    if self_count:
        problems.append(f"Found {self_count} self-rating(s). They are shown to the AI "
                        "but never count toward grades.")
    return df.reset_index(drop=True), problems


def load_team_grades(file, teams):
    """
    Read a team_grades.csv (columns: team, grade) for the given list of teams.
    Returns ({team: grade}, list_of_problems_found). Teams missing from the
    file get DEFAULT_PROJECT_GRADE.
    """
    if hasattr(file, "seek"):
        file.seek(0)
    tg = pd.read_csv(file, dtype=str, keep_default_na=False)
    tg.columns = [c.strip().lower() for c in tg.columns]
    if "team" not in tg.columns or "grade" not in tg.columns:
        raise ValueError("team_grades.csv needs the columns: team, grade")

    problems = []
    tg["team"] = tg["team"].astype(str).str.strip()
    tg["typed"] = tg["grade"].astype(str).str.strip()
    tg["grade"] = pd.to_numeric(tg["typed"], errors="coerce")

    bad = (tg["team"] == "") | tg["grade"].isna() | (tg["grade"] < 0) | (tg["grade"] > 100)
    for _, row in tg[bad].iterrows():
        problems.append(f"Ignored row '{row['team'] or '(blank team)'}, {row['typed']}': "
                        "needs a team name and a grade from 0 to 100.")
    tg = tg[~bad]

    dupes = tg[tg.duplicated(subset="team", keep="last")]["team"].unique()
    for team in dupes:
        problems.append(f"Team {team} is listed more than once; used the last grade.")
    tg = tg.drop_duplicates(subset="team", keep="last")

    unknown = sorted(set(tg["team"]) - set(teams))
    if unknown:
        problems.append(f"Ignored team(s) not in the evaluations: {', '.join(unknown)}. "
                        "Team names must match exactly, including capitals.")

    found = dict(zip(tg["team"], tg["grade"].astype(float)))
    missing = [t for t in teams if t not in found]
    if missing:
        problems.append(f"No grade for {', '.join(missing)}; using "
                        f"{DEFAULT_PROJECT_GRADE:g}.")
    return {t: found.get(t, DEFAULT_PROJECT_GRADE) for t in teams}, problems


def peer_ratings(df):
    """Only ratings of OTHER people (self-ratings never count)."""
    return df[df["evaluator"] != df["evaluatee"]]


def find_outlier_evaluators(df):
    """
    For each evaluator, compare every score they gave with the average score the
    REST of the team gave that same person. If they are OUTLIER_GAP or more points
    lower on average, they are treated as retaliating and left out.
    Returns a dict: {(team, evaluator): average_gap}
    """
    peers = peer_ratings(df)
    outliers = {}
    for (team, evaluator), rows in peers.groupby(["team", "evaluator"]):
        gaps = []
        for _, row in rows.iterrows():
            others = peers[(peers["team"] == team)
                           & (peers["evaluatee"] == row["evaluatee"])
                           & (peers["evaluator"] != evaluator)]
            if len(others) > 0:
                gaps.append(row["score"] - others["score"].mean())
        if gaps:
            avg_gap = sum(gaps) / len(gaps)
            if avg_gap <= -OUTLIER_GAP:
                outliers[(team, evaluator)] = round(avg_gap, 2)
    return outliers


def compute_grades(df, team_grades, exclude=None):
    """
    Compute adjusted grades. `team_grades` is {team: project grade}; any team not in it
    gets DEFAULT_PROJECT_GRADE. `exclude` is a dict like find_outlier_evaluators()
    returns; those evaluators' scores are left out. Returns one row per student.
    """
    exclude = exclude or {}
    peers = peer_ratings(df)
    keep = [(t, e) not in exclude for t, e in zip(peers["team"], peers["evaluator"])]
    used = peers[keep]

    grades = (used.groupby(["team", "evaluatee"])["score"]
              .agg(["mean", "count"]).reset_index()
              .rename(columns={"evaluatee": "student", "mean": "avg_received",
                               "count": "ratings_used"}))

    grades["team_avg"] = grades.groupby("team")["avg_received"].transform("mean")
    grades["ratio"] = grades["avg_received"] / grades["team_avg"]
    grades["project_grade"] = [float(team_grades.get(t, DEFAULT_PROJECT_GRADE))
                               for t in grades["team"]]
    grades["calculated_grade"] = (grades["project_grade"] * grades["ratio"]).clip(upper=100)

    grades["floor"] = FLOOR_SHARE * grades["project_grade"]
    grades["below_floor"] = grades["calculated_grade"] < grades["floor"]
    # Until the professor confirms, a grade below the floor is held AT the floor
    grades["adjusted_grade"] = grades[["calculated_grade", "floor"]].max(axis=1)

    for col in ["avg_received", "team_avg"]:
        grades[col] = grades[col].round(2)
    grades["ratio"] = grades["ratio"].round(4)
    for col in ["calculated_grade", "adjusted_grade"]:
        grades[col] = grades[col].round(1)
    return grades.sort_values(["team", "student"]).reset_index(drop=True)


def apply_floor_decisions(grades, confirmed):
    """`confirmed` is a set of (team, student) pairs whose below-floor grade the
    professor accepted."""
    grades = grades.copy()
    for i, row in grades.iterrows():
        if row["below_floor"] and (row["team"], row["student"]) in confirmed:
            grades.at[i, "adjusted_grade"] = row["calculated_grade"]
    return grades


def explain(row, excluded_for_team, confirmed):
    """One plain-English explanation of how a student's grade was reached."""
    name = row["student"]
    project = row["project_grade"]
    raw = project * row["ratio"]  # before the 100 cap
    text = (f"Team {row['team']}'s project grade is {project:g}. "
            f"{name}'s teammates gave an average score of {row['avg_received']:.2f} "
            f"(from {row['ratings_used']} rating(s)). The team average was "
            f"{row['team_avg']:.2f}, so {name} scored {row['ratio']:.2f}× the team. "
            f"{project:g} × {row['ratio']:.2f} = {raw:.1f}")
    if raw > 100:
        text += ", capped at 100"
    text += "."

    others = [e for e in excluded_for_team if e != name]
    if others:
        text += (f" Ratings from {', '.join(others)} were left out because they were far "
                 "below what the rest of the team gave.")
    if name in excluded_for_team:
        text += (f" {name}'s own ratings of teammates were left out because they were far "
                 "below what everyone else gave.")

    if row["below_floor"]:
        floor = row["floor"]
        if (row["team"], name) in confirmed:
            text += (f" This is below the 50% floor ({floor:g}); the professor confirmed "
                     f"the lower grade of {row['calculated_grade']}.")
        else:
            text += (f" This is below the 50% floor, so the grade is held at {floor:g} "
                     "until the professor confirms it.")
    return text
