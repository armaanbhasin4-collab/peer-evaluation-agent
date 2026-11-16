# Peer Evaluation Agent

A small Streamlit app that replaces a paid peer-evaluation tool. Upload your
students' peer evaluations, set each team's project grade, and click **Run Agent**. The
agent computes fair individual grades, flags problems, and drafts feedback. You
review everything before anything is final, and nothing is ever sent to students.

## Run it

You need Python 3.10 or newer.

```bash
git clone <this repo's URL>
cd peer-evaluation-agent
pip install -r requirements.txt
streamlit run app.py
```

Your browser opens at http://localhost:8501. The app starts in **mock mode**:
flags and feedback come from simple built-in rules, and it costs nothing.

### Turning on the real AI (optional)

1. Get an API key at https://openrouter.ai/keys.
2. Copy the example settings file and paste your key into it:
   ```bash
   cp .env.example .env
   ```
3. Restart the app and switch off **Mock mode** in the sidebar.

`.env` is listed in `.gitignore`, so your key is never committed. The default model
is `anthropic/claude-haiku-5.5`. You can change it with `OPENROUTER_MODEL` in `.env`.

## Project grades for each team

Different teams can earn different project grades. After you upload the
evaluations, the app shows a **Project grades** table with one row per team found
in the CSV. Each team's **Project grade (before peer adjustment)** starts at 85, and
you can click any grade to change it.

To fill the whole table at once, also upload a `team_grades.csv`:

```
team,grade
Alpha,92
Beta,78
```

- Team names must match the evaluations exactly, including capitals.
- Grades are numbers from 0 to 100.
- Teams missing from the file stay at 85.
- If a team is listed twice, the last grade is used.
- Bad rows and unknown teams are skipped, with a warning.

You can still edit the table after uploading the file.
`team_grades.csv` in this repo is a sample that matches `evaluations.csv`.

### Run the checks

```bash
python test_grading.py
```

## How it works

1. **Load and clean.** Rows with missing names, invalid scores (anything but
   1–5) or duplicates are dropped, and you're told how many. Self-ratings never
   count toward grades.
2. **Retaliation fix.** If an evaluator scores teammates **1.5+ points below**
   what the rest of the team gave the same people, their ratings are left out.
3. **Grades.** `team's project grade × (student avg ÷ team avg)`, capped at 100.
   No grade can drop below **50% of the team's own project grade** unless you
   confirm it. For example, a Beta student with project grade 78 has a floor of 39.
4. **Review comments.** Each team is checked for freeloaders, retaliation,
   manipulation attempts, collusion, score/comment mismatches and
   self-inflation. Feedback drafts are written at the same time.
5. **You review.** Approve or override every flag, and decide on any grade below
   the floor. `adjusted_grades.csv` can only be downloaded once everything is
   reviewed.

The page has five views:

| View | What it shows |
|---|---|
| 📊 Grades | Table, bar chart, and a plain-English explanation of every grade |
| 🛡️ Retaliation fix | Before/after grades for any team where an evaluator was left out |
| ✅ Review queue | Approve/override each flag; the grades CSV unlocks when done |
| ✉️ Feedback drafts | Editable drafts, each needing approval; download approved ones |
| 💰 Cost | This run's API cost vs. the paid tool ($9.50 × number of students) |

Click **🧪 Load stress-test data** to try `stress_test.csv` together with
`stress_team_grades.csv`. Together they contain every edge case:
- a freeloader, a spiteful evaluator, and two prompt injections
- a colluding team, a "did nothing" comment next to a 5, and a self-inflating student
- broken rows in the evaluations
- messy team grades: an out-of-range grade, a non-number, a blank team, a duplicate
  team, a wrongly capitalized team, an unknown team, and two teams with no grade
- a team graded 100, to test the cap, and a team graded 40, to test a low floor

## Safety

- **Comments can't change grades.** Grades are calculated in plain Python before
  any AI is involved. The AI only suggests flags and feedback, and you approve both.
- **Comments are treated as data.** They're sent inside `<evaluations>` tags, and
  the instructions tell the model never to follow anything written there.
- **Replies are checked.** Unknown flag types and names not on the team are
  dropped. If a reply can't be read, the app retries once, then says so and falls back
  to the rules.
- **Rules backstop.** In real mode the built-in rules run too, and anything the AI
  missed is added and labeled "rules backstop".
- **Nothing is sent.** The app has no way to email or message anyone.

### API limits (in `ai_review.py`)

| Limit | Value |
|---|---|
| AI calls per run | 20 (one per team) |
| Spending per run | stops at $0.50 |
| Reply length | 1500 tokens |
| Comment length | first 500 characters |
| File size | 5000 rows |

A real run on the 32-student stress-test file costs about half a cent.

## Files

| File | Purpose |
|---|---|
| `app.py` | The web page |
| `grading.py` | Grade math, retaliation fix, floor, explanations (no AI) |
| `ai_review.py` | Mock rules, OpenRouter calls, API limits |
| `evaluations.csv` | Sample data: 20 students, 5 teams |
| `team_grades.csv` | Sample project grades for those 5 teams (all different) |
| `stress_test.csv` | Every edge case: 32 students, 8 teams |
| `stress_team_grades.csv` | Messy team grades for the stress test |
| `test_grading.py` | Quick checks |
| `docs/screenshots/` | Screenshots of the app |

## Screenshots

Screenshots marked *(mock)* are from mock mode; the rest are from a real AI run.

| | |
|---|---|
| Project grades table *(mock)* | ![](docs/screenshots/0_project_grades.png) |
| Grades with per-team project grades *(mock)* | ![](docs/screenshots/3_grades_table_chart.png) |
| Retaliation fix *(mock)* | ![](docs/screenshots/1_retaliation_fix.png) |
| Flags and review queue | ![](docs/screenshots/2_4a_flags_review_locked.png) |
| Grade explanations *(mock)* | ![](docs/screenshots/3_explanations.png) |
| Grades file unlocked *(mock)* | ![](docs/screenshots/4b_review_unlocked.png) |
| Feedback drafts | ![](docs/screenshots/5_feedback.png) |
| Cost | ![](docs/screenshots/6_cost.png) |
| Stress-test data and team grade warnings *(mock)* | ![](docs/screenshots/7_stress_button.png) |
