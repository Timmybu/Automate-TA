import csv
import os
from collections import defaultdict, namedtuple
from datetime import datetime

import config
from pitt_data.peoplesoft_api.class_search import class_search
from pitt_data.peoplesoft_api.class_search_result import ClassSearchResult
from pitt_data.peoplesoft_api.class_details import class_details
from pitt_data.peoplesoft_api.class_details_result import ClassDetailsResult
from pitt_data.sci_courses import section_info

PRIMARY_COMPONENTS = ("LEC", "PRA", "INT")
# Planning/reports -- one level up from this file's own generators/ folder.
PLANNING_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(PLANNING_DIR, "reports")

HEADERS = [
	"Subject", "Course Number", "Name", "Class Number", "Associated Class Number",
	"Days", "Start Time", "End Time", "Room", "Instructor", "Type",
	"Enrollment Capacity", "Term Enrollment", "Crosslisted", "Crosslisted Enrollment",
]

# What _crosslist_info() reports for one row: label lists the partner sections, capacity/
# term_enrollment are either this row's own numbers or the group's combined totals, and
# breakdown is the per-partner enrollment string (or "CROSSLISTED" -- see _crosslist_info).
CrosslistInfo = namedtuple("CrosslistInfo", ["label", "capacity", "term_enrollment", "breakdown"])


def _subjects_for_term(term):
	return [subject for t, subject in config.data if str(t) == str(term)]


def _passes_filter(result: ClassSearchResult):
	# config.courses_filter() expects an object with .subject()/.catalog_number()/.type().
	class _Adapter:
		def subject(self): return result.subject()
		def catalog_number(self): return result.catalog_number()
		def type(self): return result.component()
	return config.courses_filter(_Adapter())


def _format_time(raw):
	return datetime.strptime(raw, "%H.%M.%S.%f").strftime("%I:%M %p").lstrip("0")


def _fetch_filtered_results(term, subjects):
	results = []
	for subject in subjects:
		for entry in class_search(term, subject) or []:
			result = ClassSearchResult(entry)
			if _passes_filter(result):
				results.append(result)
	return results


def _count_primary_offerings(results):
	# How many times each (subject, catalog_number) is offered as a LEC/PRA/INT this term
	# -- the denominator for _compare_enrollment_stats()'s per-offering average.
	counts = {}
	for result in results:
		if result.component() in PRIMARY_COMPONENTS:
			key = (result.subject(), result.catalog_number())
			counts[key] = counts.get(key, 0) + 1
	return counts


def _compare_enrollment_stats(compare, subjects, offering_counts):
	# For each compare term, sum enrollment across primary (LEC/PRA/INT) sections per
	# (subject, catalog_number), then divide by how many times that course is offered
	# (primary sections only) in the term of interest. REC/LAB are excluded from the sum
	# since those students are already counted in the primary section they attend.
	stats = {key: {} for key in offering_counts}
	for compare_term in compare:
		totals = {}
		for subject in subjects:
			for entry in class_search(compare_term, subject) or []:
				result = ClassSearchResult(entry)
				if result.component() not in PRIMARY_COMPONENTS or not _passes_filter(result):
					continue
				key = (result.subject(), result.catalog_number())
				totals[key] = totals.get(key, 0) + result.enrollment_total()
		for key, offerings in offering_counts.items():
			stats[key][compare_term] = round(totals[key] / offerings, 1) if key in totals else ""
	return stats


def _crosslist_info(term, result: ClassSearchResult) -> CrosslistInfo:
	# A cross-listed course shows up as a separate class_search row per subject/section,
	# each only reporting its own slice of enrollment. class_details' combined_sections()
	# lists every partner sharing this class, always at the same component level (a LEC
	# row's partners are other LECs, a REC row's partners are other RECs -- never mixed),
	# each with its own capacity/enrollment. We fold those into one combined total, and
	# park it on whichever partner sorts first ("the base"); every other partner's row
	# just points back with CROSSLISTED, so summing a column down the sheet doesn't
	# double-count the same students.
	if not result.cross_listed():
		return CrosslistInfo("", result.class_capacity(), result.enrollment_total(), "")

	group = ClassDetailsResult(class_details(term, result.class_number())).combined_sections()
	partners = [s for s in group if str(s["class_nbr"]) != str(result.class_number())]
	label = "; ".join(f"{s['subject']}{s['catalog_nbr']}-{s['class_nbr']}" for s in partners)

	group_by_course = sorted(group, key=lambda s: (s["subject"], s["catalog_nbr"], int(s["class_nbr"])))
	is_base = str(group_by_course[0]["class_nbr"]) == str(result.class_number())
	if not is_base:
		return CrosslistInfo(label, "CROSSLISTED", "CROSSLISTED", "CROSSLISTED")

	capacity = sum(int(s["enrl_cap"]) for s in group)
	term_enrollment = sum(int(s["enrl_tot"]) for s in group)
	breakdown = " + ".join(f"{int(s['enrl_tot'])} ({s['subject']}{s['catalog_nbr']})" for s in group_by_course)
	return CrosslistInfo(label, capacity, term_enrollment, breakdown)


def _section_sort_key(result: ClassSearchResult):
	try:
		return (0, int(result.class_section()))
	except ValueError:
		return (1, result.class_section())


def _ordered_rows(results, sci_info):
	# Orders rows as lecture-then-its-recitations (matching courses.sci.pitt.edu's own
	# display), using the sci feed's section_group as the association key -- PeopleSoft's
	# own class_search feed order and class_section numbering are NOT reliable indicators
	# of which REC/LAB belongs to which lecture. Returns (result, associated_class_section)
	# pairs. Rows with no resolvable group (missing from the sci feed, or a section_group
	# with no lecture in it) fall back to standalone, in their original relative order.
	by_course = defaultdict(list)
	for result in results:
		by_course[(result.subject(), result.catalog_number())].append(result)

	ordered = []
	for entries in by_course.values():
		subgroups = defaultdict(list)
		standalone = []
		for result in entries:
			group = sci_info.get(str(result.class_number()), {}).get("section_group")
			if group is not None:
				subgroups[group].append(result)
			else:
				standalone.append(result)

		def group_key(group_entries):
			primary = next((r for r in group_entries if r.component() in PRIMARY_COMPONENTS), group_entries[0])
			return _section_sort_key(primary)

		for group_entries in sorted(subgroups.values(), key=group_key):
			primary = next((r for r in group_entries if r.component() in PRIMARY_COMPONENTS), None)
			others = sorted((r for r in group_entries if r is not primary), key=_section_sort_key)
			if primary is not None:
				ordered.append((primary, primary.class_section()))
				ordered.extend((r, primary.class_section()) for r in others)
			else:
				# No lecture in this group (e.g. unstaffed, zero-enrollment placeholder
				# sections) -- nothing to associate them with.
				ordered.extend((r, "") for r in others)

		ordered.extend((r, "") for r in standalone)

	return ordered


def _build_row(term, result: ClassSearchResult, associated_class_section, sci_info, compare_stats, compare):
	has_meeting = len(result.data.get("meetings", [])) > 0
	days = result.meeting_days() if has_meeting else ""
	start_time = _format_time(result.start_time()) if has_meeting else ""
	end_time = _format_time(result.end_time()) if has_meeting else ""
	room = sci_info.get(str(result.class_number()), {}).get("room", "")
	instructor = "; ".join(name for name, _ in result.instructors())
	crosslist = _crosslist_info(term, result)
	course_key = (result.subject(), result.catalog_number())
	compare_values = [compare_stats.get(course_key, {}).get(compare_term, "") for compare_term in compare]

	return [
		result.subject(),
		result.catalog_number(),
		result.class_name(),
		result.class_number(),
		associated_class_section,
		days,
		start_time,
		end_time,
		room,
		instructor,
		result.component(),
		crosslist.capacity,
		crosslist.term_enrollment,
		crosslist.label,
		crosslist.breakdown,
	] + compare_values


def gen_csv(term: str, compare: list, output_path: str = None):
	subjects = _subjects_for_term(term)
	if not subjects:
		raise ValueError(f"No subjects configured for term {term} in config.data")

	results = _fetch_filtered_results(term, subjects)
	offering_counts = _count_primary_offerings(results)
	compare_stats = _compare_enrollment_stats(compare, subjects, offering_counts)
	sci_info = section_info(term)

	if output_path is None:
		os.makedirs(REPORTS_DIR, exist_ok=True)
		output_path = os.path.join(REPORTS_DIR, f"class_report_{term}.csv")

	with open(output_path, "w", newline="") as f:
		writer = csv.writer(f)
		writer.writerow(HEADERS + [f"Enrollment {compare_term}" for compare_term in compare])
		for result, associated_class_section in _ordered_rows(results, sci_info):
			writer.writerow(_build_row(term, result, associated_class_section, sci_info, compare_stats, compare))

	return output_path
