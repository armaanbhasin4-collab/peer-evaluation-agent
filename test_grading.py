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
before = g.compute_grades(df, 85)
after = g.compute_grades(df, 85, exclude=outliers)
gamma_before = dict(before[before.team == "Gamma"][["student", "adjusted_grade"]].values)
gamma_after = dict(after[after.team == "Gamma"][["student", "adjusted_grade"]].values)
assert set(gamma_before.values()) == {85.0}
assert gamma_after == {"Isla": 91.1, "Jamal": 91.1, "Kenji": 66.8, "Lena": 91.1}

# Floor: Hank is held at 42.5 until the professor confirms 28.3
hank = after[after.student == "Hank"].iloc[0]
assert hank.below_floor and hank.calculated_grade == 28.3 and hank.adjusted_grade == 42.5
confirmed = g.apply_floor_decisions(after, {"Hank"})
assert confirmed[confirmed.student == "Hank"].iloc[0].adjusted_grade == 28.3

# Cap at 100
assert after.adjusted_grade.max() == 100

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

# The AI reply reader never crashes on junk
assert ai.read_json("not json") is None
assert ai.clean_flags([{"type": "hack", "student": "Hank"}, "junk"], {"Hank"}) == []

print("All checks passed.")
