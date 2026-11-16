# Peer Evaluation Agent

A small Streamlit app that replaces a paid peer-evaluation tool. Upload your
students' peer evaluations, enter the group grade, and click **Run Agent**. The
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
3. **Grades.** `group grade × (student avg ÷ team avg)`, capped at 100. No grade
   can drop below **50% of the group grade** unless you confirm it.
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

Click **🧪 Load stress-test data** to try `stress_test.csv`, which contains every
edge case: a freeloader, a spiteful evaluator, two prompt injections, a colluding
team, a "did nothing" comment next to a 5, a self-inflating student, and broken rows.

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
| `stress_test.csv` | Every edge case: 32 students, 8 teams |
| `test_grading.py` | Quick checks |
| `docs/screenshots/` | Screenshots from a real run |

## Screenshots

| | |
|---|---|
| Retaliation fix | ![](docs/screenshots/1_retaliation_fix.png) |
| Flags and review queue | ![](docs/screenshots/2_4a_flags_review_locked.png) |
| Grade explanations | ![](docs/screenshots/3_explanations.png) |
| Grades file unlocked | ![](docs/screenshots/4b_review_unlocked.png) |
| Feedback drafts | ![](docs/screenshots/5_feedback.png) |
| Cost | ![](docs/screenshots/6_cost.png) |
| Stress-test button | ![](docs/screenshots/7_stress_button.png) |
