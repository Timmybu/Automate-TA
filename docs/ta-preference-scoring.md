# TA Preference Scoring and Testing UI

This document describes the TA preference-scoring work on the `feature-ML` branch.
The implementation is a local testing environment. It does not submit data to
PeopleSoft, change PeopleSoft reports, or make final TA assignments.

## Architecture

The preference pipeline is intentionally separate from the PeopleSoft scraper:

1. `extract_ta_preferences.py` reads the TA survey workbook and writes normalized JSON.
2. `score_ta_preferences.py` ranks candidates using the course-topic map.
3. `testing_ui.py` serves the existing JavaScript dashboard and exposes a local test API.
4. `assets/app.js` calls that API when **Run scoring test** is pressed.
5. A generated PeopleSoft workbook can be selected as a read-only section source.

The pipeline writes these inspectable test outputs after every successful run:

- `outputs/ta-preferences.json`
- `outputs/ta-course-rankings.json`

## Survey topics

The survey contains eight topic areas.

| Code | Topic |
| --- | --- |
| IP | Introductory programming (could be Python or Java) |
| JV | Core programming in Java |
| SA | Computer systems/architecture |
| TH | Theory and mathematical foundations |
| SE | Programming practice and software engineering |
| AI | Artificial intelligence and machine learning |
| SN | Security and networks |
| DM | Data management and organization |

Candidate responses are converted to numeric values:

| Response | Value |
| --- | ---: |
| Unsatisfactory | 0 |
| Satisfactory | 1 |
| Strong | 2 |
| Excellent | 3 |

## Course-topic weights

Each course assigns a separate importance weight to each topic:

| Weight | Meaning |
| ---: | --- |
| 0 | Not relevant; excluded from the calculation |
| 1 | Supporting knowledge |
| 2 | Important knowledge |
| 3 | Core course knowledge |

The current map is stored in
`scripts/ta_preferences/course_topic_weights.json`.

| Course | IP | JV | SA | TH | SE | AI | SN | DM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CS 0007 | 3 | 2 | 0 | 0 | 1 | 0 | 0 | 0 |
| CS 0011/0012 | 3 | 2 | 0 | 0 | 1 | 0 | 0 | 0 |
| CMPINF 0401 | 3 | 3 | 0 | 0 | 1 | 0 | 0 | 0 |
| CS 0441 | 0 | 0 | 1 | 3 | 0 | 0 | 0 | 0 |
| CS 0445 | 1 | 3 | 1 | 2 | 2 | 0 | 0 | 2 |
| CS 0447 | 0 | 0 | 3 | 1 | 0 | 0 | 0 | 0 |
| CS 0449 | 0 | 0 | 3 | 0 | 3 | 0 | 0 | 0 |
| CS 0590 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 |
| CS 1501 | 0 | 1 | 0 | 3 | 3 | 0 | 1 | 2 |
| CS 1502 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| CS 1503 | 0 | 0 | 0 | 2 | 0 | 3 | 0 | 0 |
| CS 1510/2012 | 0 | 0 | 0 | 3 | 1 | 0 | 0 | 0 |

Weights are relative within a course. Multiplying every weight in a course by the
same value does not change its normalized topic-fit score.

The map was informed by the University of Pittsburgh 2026–2027 course catalog:

- [Undergraduate catalog course listings, page 15](https://catalog.upp.pitt.edu/content.php?catoid=241&navoid=27442&filter%5Bitem_type%5D=3&filter%5Bonly_active%5D=1&filter%5B3%5D=1&filter%5Bcpage%5D=15#acalog_template_course_filter)
- [Undergraduate catalog course listings, page 16](https://catalog.upp.pitt.edu/content.php?catoid=241&navoid=27442&filter%5Bitem_type%5D=3&filter%5Bonly_active%5D=1&filter%5B3%5D=1&filter%5Bcpage%5D=16#acalog_template_course_filter)
- [Graduate catalog listing containing CS 2012](https://catalog.upp.pitt.edu/content.php?catoid=242&filter%5B3%5D=1&filter%5Bcpage%5D=13&filter%5Bitem_type%5D=3&filter%5Bonly_active%5D=1&navoid=27740)

## Topic-fit calculation

For each topic with a positive course weight:

```text
weighted points = candidate topic value × course topic weight
```

The topic-fit score is normalized to 0–100:

```text
topic fit = earned weighted points ÷ maximum weighted points × 100
maximum weighted points = 3 × sum of positive course weights
```

For example, CS 0445 has positive weights totaling 11, so its maximum is 33
points. A candidate earning 26 weighted points receives a topic fit of 78.8%.

## Course preferences

Course preferences are converted as follows:

| Survey response | Preference score |
| --- | ---: |
| First Choice Group | 100 |
| Second Choice | 70 |
| Third Choice Group | 40 |
| Cannot TA Group | Hard exclusion |
| Missing response | Exclusion |

Third choice receives a positive score because it still indicates willingness to
teach the course. `Cannot TA` is never averaged into the score.

## Overall score and adjustable split

The default overall score is:

```text
overall score = topic fit × 0.60 + preference score × 0.40
```

The testing UI retains adjustable topic-fit and course-preference controls. The two
percentages always total 100%. The Python command line exposes the same controls as
`--topic-weight` and `--preference-weight`.

Example using a 78.8% topic fit:

| Preference | Calculation | Overall score |
| --- | --- | ---: |
| First choice | `78.8 × 0.60 + 100 × 0.40` | 87.3 |
| Second choice | `78.8 × 0.60 + 70 × 0.40` | 75.3 |
| Third choice | `78.8 × 0.60 + 40 × 0.40` | 63.3 |

## Eligibility and ranking

A candidate is excluded from a course when:

- the candidate selected `Cannot TA Group (explain below)`;
- the course preference is missing; or
- one or more topic ratings required by that course are missing.

For each course, eligible candidates are sorted by overall score from highest to
lowest. Excluded candidates are retained in the output with their reasons and appear
after eligible candidates. Names provide stable ordering when scores tie.

Courses are ranked independently. A candidate can currently rank first for more than
one course because assignment conflict resolution is not implemented yet.

## Prerequisites

Prerequisites influenced the selected course-topic weights, but the application does
not currently verify a candidate's transcript or completed coursework. Prerequisite
knowledge is represented indirectly through the candidate's topic ratings and the
course map.

## PeopleSoft workbook integration

Generated `.xlsx` reports in `scripts/PeopleSoft Scraper/reports` appear in the
testing UI as read-only inputs. The integration reads these columns when present:

- Subject
- Course Number
- Name
- Class Number
- Type
- Term Enrollment
- `# Recitation TAs (PhD)`
- `# Graders (PhD)`

The UI displays each section's enrollment, type, estimated TA need, top-ranked
candidate, and score. Combined mapping keys such as `CS 0011/0012` and
`CS 1510/2012` are expanded when matching PeopleSoft course codes.

PeopleSoft data does not currently change the candidate score. It supplies the
sections and staffing context to which rankings are connected.

Excel lock files beginning with `~$` are ignored. At the time this document was
written, the report directory contained lock files but no readable generated report.

## Testing UI

Start the local server:

```powershell
& C:\Python313\python.exe "scripts\ta_preferences\testing_ui.py"
```

Open:

```text
http://127.0.0.1:8765/#scoring-test
```

The **Scoring test** tab is part of the existing JavaScript single-page dashboard.
Pressing **Run scoring test** calls the local Python API, reruns extraction and
scoring, refreshes the course rankings, and rewrites the output JSON files. The button
can be used repeatedly.

Stop the server with `Ctrl+C` in its terminal. The server is not intended to remain
running continuously.

## Command-line workflow

Extraction:

```powershell
& C:\Python313\python.exe "scripts\ta_preferences\extract_ta_preferences.py" `
  "data\Test_Info.xlsx" `
  --output "outputs\ta-preferences.json"
```

Scoring:

```powershell
& C:\Python313\python.exe "scripts\ta_preferences\score_ta_preferences.py" `
  "outputs\ta-preferences.json" `
  --course-map "scripts\ta_preferences\course_topic_weights.json" `
  --topic-weight 0.60 `
  --preference-weight 0.40 `
  --output "outputs\ta-course-rankings.json"
```

Use `--format csv` to produce a flat CSV result.

## Current limitations

The current output is a candidate ranking, not a finished TA assignment. These items
are retained or displayed but are not yet enforced by the scoring model:

- free-text scheduling constraints;
- completed prerequisites or transcripts;
- previous teaching experience;
- maximum working hours;
- conflicts between course sections;
- duplicate assignments across courses;
- instructor preferences; and
- final coverage and optimization across all sections.

Only courses present in `course_topic_weights.json` are scored.

## Verification

The test suite is located at `tests/test_ta_preference_pipeline.py` and currently
covers survey extraction, normalized JSON validation, weighted topic-fit calculation,
hard `Cannot TA` exclusions, invalid topic mappings, and read-only PeopleSoft workbook
parsing.

Run it with:

```powershell
& C:\Python313\python.exe "tests\test_ta_preference_pipeline.py"
```

