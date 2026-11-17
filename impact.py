"""
impact.py - explains how each flag affected grades, with real numbers.

The numbers come from the grade math in grading.py (never from the AI), so they are
exact. Some flags change grades and some don't; each explanation says which.

flag_impact() returns two strings:
  short - one line for summaries, e.g. "grade 39 (-39 vs project grade 78)"
  text  - a full sentence or two for the review cards and the report
"""

import ai_review as ai
import grading as g


def _row(table, team, student):
    rows = table[(table["team"] == team) & (table["student"] == student)]
    return rows.iloc[0] if len(rows) else None


def _changes(before, after, team):
    """[(student, grade before, grade after)] for one team, in name order."""
    merged = (before[before["team"] == team][["student", "adjusted_grade"]]
              .merge(after[after["team"] == team][["student", "adjusted_grade"]],
                     on="student", suffixes=("_before", "_after")))
    return [(r["student"], r["adjusted_grade_before"], r["adjusted_grade_after"])
            for _, r in merged.iterrows()]


def flag_impact(flag, df, grades, grades_before, team_grades, outliers):
    """How one flag affected grades. `grades` already leaves out the outliers."""
    team, who, kind = flag["team"], flag["student"], flag["type"]
    me = _row(grades, team, who)

    if kind == "freeloader":
        if me is None:
            return {"short": "no grade found", "text": f"{who} has no peer ratings."}
        drop = me["calculated_grade"] - me["project_grade"]
        text = (f"Teammates gave {who} an average of {me['avg_received']:.2f}, against the "
                f"team's {me['team_avg']:.2f}. So {who}'s grade is {me['project_grade']:g} × "
                f"{me['ratio']:.2f} = {me['calculated_grade']:.1f}, which is {drop:+.1f} "
                f"against the project grade of {me['project_grade']:g}.")
        if me["below_floor"]:
            text += (f" That is below the 50% floor, so it is held at {me['floor']:g} until "
                     "you decide in the Review queue.")
            short = (f"grade {me['floor']:g} (held at floor; calculated "
                     f"{me['calculated_grade']:.1f} vs project grade {me['project_grade']:g})")
        else:
            short = (f"grade {me['calculated_grade']:.1f} ({drop:+.1f} vs project grade "
                     f"{me['project_grade']:g})")
        return {"short": short, "text": text}

    if kind == "retaliation":
        if (team, who) in outliers:
            # Already left out: compare with the grades from before the fix
            changes = _changes(grades_before, grades, team)
            lead = f"{who}'s ratings were left out of the grade math."
            short_lead = "ratings left out"
        else:
            # Not far enough below to be left out automatically: show what leaving out would do
            alt = g.compute_grades(df, team_grades, exclude={**outliers, (team, who): 0})
            changes = _changes(grades, alt, team)
            lead = (f"{who}'s ratings still count: they weren't far enough below the team to "
                    "be left out automatically. If they were left out:")
            short_lead = "ratings still count; leaving them out would give"
        moved = [(n, b, a) for n, b, a in changes if round(a - b, 1) != 0]
        if not moved:
            return {"short": f"{short_lead}, no grade changes",
                    "text": f"{lead} No one's grade changes."}
        detail = ", ".join(f"{n} {b:g} → {a:g} ({a - b:+.1f})" for n, b, a in moved)
        why = (f" {who}'s own grade moves too, because the team average changes."
               if any(n == who for n, _, _ in moved) else "")
        return {"short": f"{short_lead}: " + ", ".join(f"{n} {a - b:+.1f}" for n, b, a in moved),
                "text": f"{lead} Grades changed: {detail}.{why}"}

    if kind == "manipulation":
        grade = f" {who}'s own grade is {me['adjusted_grade']:g}." if me is not None else ""
        return {"short": "no effect on grades (comments never change scores)",
                "text": "No effect on anyone's grade. Grades are calculated from the scores "
                        "alone, before any comment is read, so instructions hidden in a "
                        f"comment can't change them.{grade}"}

    if kind == "collusion":
        team_rows = grades[grades["team"] == team]
        project = team_rows["project_grade"].iloc[0] if len(team_rows) else 0
        return {"short": f"no peer adjustment: all {len(team_rows)} got the project grade "
                         f"({project:g})",
                "text": f"Every teammate gave everyone a 5, so the peer adjustment had nothing "
                        f"to go on: all {len(team_rows)} students got exactly the project grade "
                        f"of {project:g}. If you think contributions differed, adjust these "
                        "grades by hand."}

    if kind == "mismatch":
        # Find the score that contradicts its own comment (high score, negative words)
        rows = df[(df["team"] == team) & (df["evaluator"] == who) & (df["evaluatee"] != who)
                  & (df["score"] >= 4)]
        rows = rows[rows["comment"].str.lower().apply(
            lambda c: any(w in c for w in ai.NEGATIVE_WORDS))]
        if rows.empty:
            return {"short": "scores still count as given",
                    "text": f"{who}'s scores still count as given. Compare the comment with "
                            "the score before approving."}
        r = rows.iloc[0]
        target = r["evaluatee"]
        alt = g.compute_grades(df.drop(index=r.name), team_grades, exclude=outliers)
        now, without = _row(grades, team, target), _row(alt, team, target)
        if now is None or without is None:
            return {"short": "scores still count as given",
                    "text": f"{who}'s score of {r['score']} for {target} still counts."}
        diff = now["adjusted_grade"] - without["adjusted_grade"]
        direction = "higher" if diff >= 0 else "lower"
        return {"short": f"{target}'s grade is {abs(diff):.1f} points {direction} because of "
                         "that score",
                "text": f"{who}'s score of {r['score']} for {target} still counts, even though "
                        f"the comment says otherwise. Without that score, {target}'s grade "
                        f"would be {without['adjusted_grade']:g} instead of "
                        f"{now['adjusted_grade']:g} ({-diff:+.1f})."}

    if kind == "self_inflation":
        grade = (f" {who}'s grade ({me['adjusted_grade']:g}) comes only from teammates' "
                 f"ratings (average {me['avg_received']:.2f}).") if me is not None else ""
        return {"short": "no effect (self-ratings never count)",
                "text": f"No effect on the grade: self-ratings never count.{grade}"}

    return {"short": "no grade change", "text": "This flag doesn't change any grade."}
