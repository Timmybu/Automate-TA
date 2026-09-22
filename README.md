# Automate TA — Assignment Studio

A self-contained frontend prototype for the CS 1980 Automate TA capstone.

## Run locally

Double-click `index.html`. It opens the application directly from the repository; no server, account, installation, build step, or cloud service is required.

## Project structure

```text
index.html            Application markup and entry point
assets/
  styles.css          Layout, visual design, and responsive rules
  app.js              Sample data, rendering, and interactions
  favicon.svg         Local application icon
data/
  Test_Info.xlsx      TA preference survey input
scripts/
  PeopleSoft Scraper/ Course collection and staffing estimates
  ta_preferences/     Survey extraction and preference scoring
```

## Included flows

- Review assignment coverage, preference fit, hours, and unresolved conflicts.
- Search the sample course and teaching-assistant data.
- Inspect the full proposed assignment.
- Adjust staffing constraints and optimization weights.
- Simulate a late TA withdrawal while preserving stable placements.
- Export the current assignment as CSV.

## Python preference scoring

See [TA Preference Scoring and Testing UI](docs/ta-preference-scoring.md) for the
complete topic map, formulas, preference values, PeopleSoft test integration, UI
workflow, and current limitations.

The workbook is treated only as source data. Two independent scripts outside the
PeopleSoft scraper handle survey processing:

1. `extract_ta_preferences.py` reads the raw `Form Responses 1` worksheet and writes
   normalized JSON. It does not calculate scores.
2. `score_ta_preferences.py` reads that JSON, applies course-topic weights, and writes
   explainable TA-course rankings. It does not read Excel.

Course-topic weights live in JSON rather than the workbook. Start with
`scripts/ta_preferences/course_topic_weights.example.json` and use
topic names that exactly match the survey headers. A weight of `0` is ignored; larger
positive values make a topic more important to that course.

```powershell
python "scripts/ta_preferences/extract_ta_preferences.py" `
  "data/Test_Info.xlsx" `
  --output "outputs/ta-preferences.json"

python "scripts/ta_preferences/score_ta_preferences.py" `
  "outputs/ta-preferences.json" `
  --course-map "scripts/ta_preferences/course_topic_weights.example.json" `
  --output "outputs/ta-course-rankings.json"
```

Use `--format csv` for a flat export. The default overall score is 60% topic fit and
40% stated course preference; `--topic-weight` and `--preference-weight` can change
that balance and must add to `1.0`. A `Cannot TA` response is a hard disqualifier.
Free-text scheduling and course constraints are retained in the output for later
constraint processing; the scorer does not guess their meaning.

### Local scoring test UI

Start the local dashboard server with:

```powershell
& C:\Python313\python.exe "scripts\ta_preferences\testing_ui.py"
```

Then open `http://127.0.0.1:8765/#scoring-test`. The **Scoring test** tab runs the
real extraction and scoring pipeline whenever **Run scoring test** is pressed. It
allows the topic/preference balance to be adjusted, shows rankings by course, and
rewrites `outputs/ta-preferences.json` and `outputs/ta-course-rankings.json` after
each successful run. Generated `.xlsx` files in
`scripts/PeopleSoft Scraper/reports` appear as read-only test inputs. When selected,
their sections, enrollment, estimated TA need, and highest-ranked candidate are shown
in the same JavaScript view. Excel lock files beginning with `~$` are ignored. The
server and API remain separate from the PeopleSoft scraper and never modify its reports.
