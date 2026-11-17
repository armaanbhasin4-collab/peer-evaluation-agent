"""
Quick checks that the grade math and the mock rules work.
Run with:   python test_grading.py
"""
import ai_review as ai
import grading as g

df, problems = g.load_evaluations("stress_test.csv")
outliers = g.find_outlier_evaluators(df)

# Messy rows are cleaned up
assert len(problems) == 4, problems

# Retaliation: only Kenji is left out
assert list(outliers) == [("Gamma", "Kenji")], outliers

# Team Gamma before and after leaving Kenji out
# With no team grades, every team uses the default of 85
before = g.compute_grades(df, {})
after = g.compute_grades(df, {}, exclude=outliers)
gamma_before = dict(before[before.team == "Gamma"][["student", "adjusted_grade"]].values)
gamma_after = dict(after[after.team == "Gamma"][["student", "adjusted_grade"]].values)
assert set(gamma_before.values()) == {85.0}
assert gamma_after == {"Isla": 91.1, "Jamal": 91.1, "Kenji": 66.8, "Lena": 91.1}

# Floor: Hank is held at 42.5 until the professor confirms 28.3
hank = after[after.student == "Hank"].iloc[0]
assert hank.below_floor and hank.calculated_grade == 28.3 and hank.adjusted_grade == 42.5
confirmed = g.apply_floor_decisions(after, {("Beta", "Hank")})
assert confirmed[confirmed.student == "Hank"].iloc[0].adjusted_grade == 28.3

# Cap at 100
assert after.adjusted_grade.max() == 100

# Per-team project grades from the messy stress-test grades file
teams = sorted(df.team.unique())
team_grades, grade_problems = g.load_team_grades("stress_team_grades.csv", teams)
assert team_grades == {"Alpha": 90, "Beta": 78, "Delta": 88, "Epsilon": 100, "Eta": 40,
                       "Gamma": 70, "Theta": 85, "Zeta": 85}, team_grades
assert len(grade_problems) == 6, grade_problems  # bad rows, duplicate, unknown, missing

graded = g.compute_grades(df, team_grades, exclude=outliers)
row = lambda name: graded[graded.student == name].iloc[0]
assert row("Hank").project_grade == 78 and row("Hank").calculated_grade == 26.0
assert row("Hank").floor == 39 and row("Hank").adjusted_grade == 39  # 50% of 78
assert row("Kenji").adjusted_grade == 55.0                           # 70 x 0.79
assert row("Sam").adjusted_grade == 100                              # 100 x 1.11, capped
assert row("Aiden").floor == 20 and not row("Aiden").below_floor     # 29.4 is above 20
text = g.explain(row("Hank"), [], set())
assert "project grade is 78" in text and "held at 39" in text, text

# The sample team_grades.csv matches the sample evaluations exactly
sample, _ = g.load_evaluations("evaluations.csv")
sample_grades, sample_problems = g.load_team_grades("team_grades.csv",
                                                    sorted(sample.team.unique()))
assert sample_problems == [] and len(set(sample_grades.values())) == 5

# Mock rules catch every planted case
found = set()
for team, rows in df.groupby("team"):
    team_out = {e: gap for (t, e), gap in outliers.items() if t == team}
    flags, feedback, cost = ai.review_team_mock(rows, team_out)
    assert cost == 0 and len(feedback) == rows.evaluatee.nunique()
    found |= {(f["type"], f["student"]) for f in flags}
expected = {("freeloader", "Hank"), ("retaliation", "Kenji"), ("manipulation", "Noah"),
            ("manipulation", "Sam"), ("collusion", ai.WHOLE_TEAM), ("mismatch", "Zane"),
            ("self_inflation", "Eli")}
assert expected <= found, expected - found

# Each flag explains its effect on grades with the real numbers
import impact
before_tg = g.compute_grades(df, team_grades)
def effect(kind, student, team):
    return impact.flag_impact({"type": kind, "student": student, "team": team},
                              df, graded, before_tg, team_grades, outliers)
assert "held at 39" in effect("freeloader", "Hank", "Beta")["text"]
assert "Isla 70 → 75 (+5.0)" in effect("retaliation", "Kenji", "Gamma")["text"]
assert effect("manipulation", "Noah", "Delta")["short"].startswith("no effect")
assert effect("self_inflation", "Eli", "Theta")["short"].startswith("no effect")
assert "all 4 got the project grade (85)" in effect("collusion", ai.WHOLE_TEAM, "Zeta")["short"]
assert "would be 20.9 instead of 29.4" in effect("mismatch", "Zane", "Eta")["text"]

# The AI reply reader never crashes on junk
assert ai.read_json("not json") is None
assert ai.clean_flags([{"type": "hack", "student": "Hank"}, "junk"], {"Hank"}) == []

print("All checks passed.")
