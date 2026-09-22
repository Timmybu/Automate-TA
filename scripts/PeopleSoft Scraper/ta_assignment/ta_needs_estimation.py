import csv
import math

PRIMARY_COMPONENTS = ("LEC", "PRA", "INT")

# How many "positions" a lecture needs, and what each position is worth in PhD-grader
# effort. Ranges are inclusive catalog numbers. Matches the old TA notebook's cutoff
# (445), which split courses into "per 75 students" (lower-level) vs "per 50" (upper).
ASSISTANT_RULES = [
	{"from": 0, "to": 444, "effort": 0.5, "per": 75},
	{"from": 445, "to": 9999, "effort": 0.5, "per": 50},
]

# Every REC/LAB section always needs this many Recitation TAs, regardless of enrollment.
RECITATION_EFFORT = 0.25

# A lecture this small gets no grader at all, overriding the assistant rule's formula.
MIN_ENROLLMENT_FOR_GRADER = 20

RECITATION_TA_COLUMN = "# Recitation TAs (PhD)"
GRADER_COLUMN = "# Graders (PhD)"
NEW_COLUMNS = [RECITATION_TA_COLUMN, GRADER_COLUMN]


def _assistant_rule_for(catalog_number):
	number = int(catalog_number)
	for rule in ASSISTANT_RULES:
		if rule["from"] <= number <= rule["to"]:
			return rule
	return None


def _positions_needed(enrollment, rule):
	positions = math.ceil(enrollment / rule["per"])
	return positions * rule["effort"]


def _grader_effort(catalog_number, enrollment):
	if enrollment < MIN_ENROLLMENT_FOR_GRADER:
		return 0
	rule = _assistant_rule_for(catalog_number)
	return _positions_needed(enrollment, rule) if rule else ""


def calculate_needs(csv_path: str, output_path: str = None) -> str:
	# Adds/updates "# Recitation TAs (PhD)" and "# Graders (PhD)" on a class report CSV
	# (from generators/gen_class_csv.py), based on each row's own enrollment. CSV only --
	# XLSX conversion (and any totals row) happens later, in generators/gen_class_xlsx.py.
	# Safe to re-run: if the columns already exist, their values are just recomputed.
	with open(csv_path, newline="") as f:
		header, *rows = csv.reader(f)

	catalog_col = header.index("Course Number")
	type_col = header.index("Type")
	enrollment_col = header.index("Term Enrollment")

	missing_columns = [column for column in NEW_COLUMNS if column not in header]
	header = header + missing_columns
	rec_ta_col = header.index(RECITATION_TA_COLUMN)
	grader_col = header.index(GRADER_COLUMN)

	updated_rows = []
	for row in rows:
		row = row + [""] * (len(header) - len(row))
		component = row[type_col]

		try:
			enrollment = int(row[enrollment_col])
		except (TypeError, ValueError):
			enrollment = None

		if enrollment is None:
			# Non-base row of a cross-listed group -- its enrollment (and TA need) is
			# already accounted for on the group's base row, so it gets neither role.
			row[rec_ta_col] = "CROSSLISTED"
			row[grader_col] = "CROSSLISTED"
		elif component in PRIMARY_COMPONENTS:
			row[rec_ta_col] = ""
			row[grader_col] = _grader_effort(row[catalog_col], enrollment)
		else:
			row[rec_ta_col] = RECITATION_EFFORT
			row[grader_col] = ""

		updated_rows.append(row)

	output_path = output_path or csv_path
	with open(output_path, "w", newline="") as f:
		writer = csv.writer(f)
		writer.writerow(header)
		writer.writerows(updated_rows)

	return output_path
