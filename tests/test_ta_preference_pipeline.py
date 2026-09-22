import json
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

MODULE_DIR = Path(__file__).resolve().parents[1] / "scripts" / "ta_preferences"
sys.path.insert(0, str(MODULE_DIR))

from extract_ta_preferences import extract_workbook, write_json as write_extracted_json  # noqa: E402
from score_ta_preferences import (  # noqa: E402
    CANNOT_TA,
    build_rankings,
    calculate_topic_fit,
    load_extracted_preferences,
    score_candidate,
)
from testing_ui import load_peoplesoft_report  # noqa: E402


INTRO = "Introductory programming (could be Python or Java)"
JAVA = "Core programming in Java"


def extracted_data(preference="First Choice Group"):
    return {
        "schema_version": 1,
        "source": {"workbook": "test.xlsx", "sheet": "Form Responses 1"},
        "courses": ["CS 0445"],
        "topics": [INTRO, JAVA],
        "profile_count": 1,
        "profiles": [
            {
                "candidate_id": "test@pitt.edu",
                "timestamp": "2026-08-12T12:00:00",
                "first_name": "Test",
                "last_name": "Candidate",
                "name": "Test Candidate",
                "email": "test@pitt.edu",
                "course_preferences": {"CS 0445": preference},
                "topic_ratings": {INTRO: "Excellent", JAVA: "Strong"},
                "scheduling_constraints": "Friday afternoon",
                "course_constraints": "",
                "goals": "Teaching experience",
                "notes": "",
            }
        ],
    }


class PreferencePipelineTests(unittest.TestCase):
    def test_extractor_reads_raw_response_headers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workbook_path = Path(temp_dir) / "responses.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Form Responses 1"
            sheet.append(
                [
                    "Timestamp",
                    "First name",
                    "Last name",
                    "Pitt email address",
                    "Top choices [CS 0445]",
                    f"Topic Areas [{INTRO}]",
                    f"Topic Areas [{JAVA}]",
                    "Scheduling constraints",
                    "Courses constraints",
                    "Goals",
                    "Anything else we should know?",
                ]
            )
            sheet.append(
                [
                    "2026-08-12 12:00:00",
                    "Test",
                    "Candidate",
                    "test@pitt.edu",
                    "First Choice Group",
                    "Excellent",
                    "Strong",
                    "Friday afternoon",
                    "",
                    "Teaching experience",
                    "No additional notes",
                ]
            )
            workbook.save(workbook_path)

            payload = extract_workbook(workbook_path)

        self.assertEqual(payload["profile_count"], 1)
        self.assertEqual(payload["topics"], [INTRO, JAVA])
        self.assertEqual(
            payload["profiles"][0]["course_preferences"]["CS 0445"],
            "First Choice Group",
        )

    def test_extracted_json_loads_in_scorer(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "preferences.json"
            with path.open("w", encoding="utf-8") as destination:
                write_extracted_json(extracted_data(), destination)

            loaded = load_extracted_preferences(path)

        self.assertEqual(loaded["profiles"][0]["email"], "test@pitt.edu")

    def test_weighted_topic_fit_is_normalized(self):
        fit = calculate_topic_fit(
            {INTRO: "Excellent", JAVA: "Strong"},
            {INTRO: 1, JAVA: 2},
        )

        self.assertEqual(fit["earned_points"], 7)
        self.assertEqual(fit["maximum_points"], 9)
        self.assertEqual(fit["score"], 77.8)

    def test_cannot_ta_is_a_hard_disqualifier(self):
        profile = extracted_data(CANNOT_TA)["profiles"][0]
        result = score_candidate(profile, "CS 0445", {INTRO: 1, JAVA: 2})

        self.assertFalse(result["eligible"])
        self.assertIsNone(result["overall_score"])

    def test_rankings_reject_unknown_mapping_topic(self):
        with self.assertRaisesRegex(ValueError, "do not match extracted Topic Areas"):
            build_rankings(
                extracted_data(),
                {"CS 0445": {"Misspelled topic": 1}},
            )

    def test_testing_ui_reads_peoplesoft_sections_without_modifying_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "class_report_2271.xlsx"
            workbook = Workbook()
            sheet = workbook.active
            sheet.append(
                [
                    "Subject",
                    "Course Number",
                    "Name",
                    "Class Number",
                    "Type",
                    "Term Enrollment",
                    "# Recitation TAs (PhD)",
                    "# Graders (PhD)",
                ]
            )
            sheet.append(["CS", "0011", "Computing for Scientists", 12345, "LEC", 42, "", 0.5])
            sheet.append(["CS", "0445", "Algorithms and Data Structures 1", 23456, "REC", 25, 0.25, ""])
            workbook.save(report_path)
            original_size = report_path.stat().st_size

            report = load_peoplesoft_report(
                report_path,
                ["CS 0011/0012", "CS 0445"],
            )

            self.assertEqual(report["section_count"], 2)
            self.assertEqual(report["mapped_section_count"], 2)
            self.assertEqual(report["sections"][0]["mapped_course"], "CS 0011/0012")
            self.assertEqual(report["sections"][1]["recitation_ta_need"], 0.25)
            self.assertEqual(report_path.stat().st_size, original_size)


if __name__ == "__main__":
    unittest.main()
