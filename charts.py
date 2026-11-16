"""
charts.py - the charts, built with Altair (it comes with Streamlit).

Colors follow the GroupGrade theme: ink blue and red pen (a colorblind-checked
pair), with pencil gray for "before" values.
"""

import altair as alt
import pandas as pd

INK = "#1F2A3A"
MUTED = "#5B6577"
GRID = "#ECE6D6"
INK_BLUE = "#2A55B8"
RED_PEN = "#C2402A"
PENCIL_GRAY = "#A8A29E"
FONT = "Inter, system-ui, sans-serif"


def _style(chart):
    """Quiet axes and hairline grid so the data stands out."""
    return (chart
            .configure(font=FONT)
            .configure_view(stroke=None)
            .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor=GRID,
                            domain=False, tickColor=GRID, labelFontSize=12,
                            titleFontSize=12, titleFontWeight=600)
            .configure_legend(labelColor=INK, titleColor=MUTED, orient="top",
                              labelFontSize=12, titleFontSize=12, symbolType="circle"))


def grades_chart(grades):
    """
    One bar per student, grouped by team. Ink blue = at or above the team's project
    grade, red pen = below it. The dark tick is the team's project grade.
    """
    data = grades.copy()
    # keep each team together, best grade first
    data = data.sort_values(["team", "adjusted_grade"], ascending=[True, False])
    order = list(data["student"] + " · " + data["team"])
    data["label"] = order
    data["Compared with project grade"] = [
        "At or above" if a >= p else "Below"
        for a, p in zip(data["adjusted_grade"], data["project_grade"])]

    base = alt.Chart(data).encode(
        y=alt.Y("label:N", sort=order, title=None, axis=alt.Axis(labelPadding=6)))
    tooltip = [alt.Tooltip("student:N", title="Student"), alt.Tooltip("team:N", title="Team"),
               alt.Tooltip("project_grade:Q", title="Project grade", format=".1f"),
               alt.Tooltip("avg_received:Q", title="Avg peer score", format=".2f"),
               alt.Tooltip("adjusted_grade:Q", title="Final grade", format=".1f")]

    bars = base.mark_bar(cornerRadiusEnd=4, size=14).encode(
        x=alt.X("adjusted_grade:Q", title="Final grade", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color("Compared with project grade:N",
                        scale=alt.Scale(domain=["At or above", "Below"],
                                        range=[INK_BLUE, RED_PEN])),
        tooltip=tooltip)
    ticks = base.mark_tick(color=INK, thickness=2, size=18, opacity=.85).encode(
        x="project_grade:Q", tooltip=tooltip)

    return _style((bars + ticks).properties(height=max(260, 22 * len(data))))


def before_after_chart(compare):
    """Dumbbell chart: each student's grade before and after leaving the outlier out."""
    long = compare.melt(id_vars="student", value_vars=["Before", "After"],
                        var_name="Version", value_name="Grade")
    scale = alt.Scale(domain=["Before", "After"], range=[PENCIL_GRAY, INK_BLUE])
    y = alt.Y("student:N", title=None, sort=list(compare["student"]))

    lines = alt.Chart(compare).mark_rule(color="#D6CFBF", strokeWidth=2).encode(
        y=y, x="Before:Q", x2="After:Q")
    dots = alt.Chart(long).mark_circle(size=140, opacity=1, stroke="white",
                                       strokeWidth=2).encode(
        y=y,
        x=alt.X("Grade:Q", title="Grade", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color("Version:N", title=None, scale=scale),
        tooltip=["student:N", "Version:N", alt.Tooltip("Grade:Q", format=".1f")])
    return _style((lines + dots).properties(height=max(160, 46 * len(compare))))


def flags_chart(flags, names):
    """How many flags of each kind. `names` maps flag type -> friendly name."""
    counts = pd.Series([names.get(f["type"], f["type"]) for f in flags]).value_counts()
    data = counts.rename_axis("Kind").reset_index(name="Flags")
    y = alt.Y("Kind:N", sort="-x", title=None)
    bars = alt.Chart(data).mark_bar(cornerRadiusEnd=4, size=16, color=RED_PEN).encode(
        y=y, x=alt.X("Flags:Q", title=None, axis=alt.Axis(tickMinStep=1, labels=False,
                                                           grid=False)),
        tooltip=["Kind:N", "Flags:Q"])
    labels = alt.Chart(data).mark_text(align="left", dx=6, color=INK, fontWeight=600).encode(
        y=y, x="Flags:Q", text="Flags:Q")
    return _style((bars + labels).properties(height=max(120, 34 * len(data))))
