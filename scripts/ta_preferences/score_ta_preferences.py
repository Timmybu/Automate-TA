"""Score normalized TA preference data against course-topic mappings.

Input comes from extract_ta_preferences.py. This script does not read Excel and has no
dependency on the PeopleSoft scraper.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, TextIO


TOPIC_VALUES = {
    "Unsatisfactory": 0,
    "Satisfactory": 1,
    "Strong": 2,
    "Excellent": 3,
}

PREFERENCE_VALUES = {
    "Third Choice Group": 40.0,
    "Second Choice": 70.0,
    "First Choice Group": 100.0,
}

CANNOT_TA = "Cannot TA Group (explain below)"


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def load_extracted_preferences(path: str | Path) -> dict[str, Any]:
    """Load and validate the normalized output from the extraction script."""

    input_path = Path(path)
    with input_path.open(encoding="utf-8") as source:
        payload = json.load(source)

    if not isinstance(payload, dict):
        raise ValueError("Extracted preference data must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported or missing extracted-data schema_version")

    courses = payload.get("courses")
    topics = payload.get("topics")
    profiles = payload.get("profiles")
    if not isinstance(courses, list) or not courses:
        raise ValueError("Extracted preference data has no courses")
    if not isinstance(topics, list) or not topics:
        raise ValueError("Extracted preference data has no topics")
    if not isinstance(profiles, list) or not profiles:
        raise ValueError("Extracted preference data has no profiles")

    expected_courses = set(courses)
    expected_topics = set(topics)
    valid_preferences = set(PREFERENCE_VALUES) | {CANNOT_TA, ""}

    for index, profile in enumerate(profiles, start=1):
        if not isinstance(profile, dict):
            raise ValueError(f"Profile {index} must be a JSON object")
        course_preferences = profile.get("course_preferences")
        topic_ratings = profile.get("topic_ratings")
        if not isinstance(course_preferences, dict):
            raise ValueError(f"Profile {index} has no course_preferences object")
        if not isinstance(topic_ratings, dict):
            raise ValueError(f"Profile {index} has no topic_ratings object")
        if set(course_preferences) != expected_courses:
            raise ValueError(f"Profile {index} course headers do not match the schema")
        if set(topic_ratings) != expected_topics:
            raise ValueError(f"Profile {index} topic headers do not match the schema")

        invalid_preferences = {
            course: preference
            for course, preference in course_preferences.items()
            if preference not in valid_preferences
        }
        if invalid_preferences:
            raise ValueError(
                f"Profile {index} contains unknown course preferences: "
                f"{invalid_preferences}"
            )

        invalid_ratings = {
            topic: rating
            for topic, rating in topic_ratings.items()
            if rating and rating not in TOPIC_VALUES
        }
        if invalid_ratings:
            raise ValueError(
                f"Profile {index} contains unknown topic ratings: {invalid_ratings}"
            )

    return payload


def load_course_topic_weights(path: str | Path) -> dict[str, dict[str, float]]:
    """Load and validate course-to-topic weights from JSON."""

    mapping_path = Path(path)
    with mapping_path.open(encoding="utf-8") as source:
        raw_mapping = json.load(source)

    if not isinstance(raw_mapping, dict) or not raw_mapping:
        raise ValueError("Course-topic mapping must be a non-empty JSON object")

    mapping: dict[str, dict[str, float]] = {}
    for raw_course, raw_weights in raw_mapping.items():
        course = _text(raw_course)
        if not course:
            raise ValueError("Course-topic mapping contains a blank course name")
        if not isinstance(raw_weights, dict) or not raw_weights:
            raise ValueError(f"Course {course!r} must define at least one topic weight")

        weights: dict[str, float] = {}
        for raw_topic, raw_weight in raw_weights.items():
            topic = _text(raw_topic)
            if isinstance(raw_weight, bool) or not isinstance(raw_weight, (int, float)):
                raise ValueError(
                    f"Weight for {course!r} / {topic!r} must be numeric"
                )
            weight = float(raw_weight)
            if not math.isfinite(weight) or weight < 0:
                raise ValueError(
                    f"Weight for {course!r} / {topic!r} must be finite and non-negative"
                )
            if weight > 0:
                weights[topic] = weight

        if not weights:
            raise ValueError(f"Course {course!r} has no positive topic weights")
        mapping[course] = weights

    return mapping


def calculate_topic_fit(
    topic_ratings: Mapping[str, str],
    course_weights: Mapping[str, float],
) -> dict[str, Any]:
    """Calculate an explainable, normalized 0-100 topic-fit score."""

    if not course_weights:
        raise ValueError("At least one course topic weight is required")

    earned = 0.0
    maximum = 0.0
    contributions: dict[str, dict[str, float | int | str | None]] = {}
    missing_topics: list[str] = []

    for topic, raw_weight in course_weights.items():
        weight = float(raw_weight)
        if not math.isfinite(weight) or weight < 0:
            raise ValueError(f"Topic weight must be finite and non-negative: {topic!r}")
        if weight == 0:
            continue

        maximum += max(TOPIC_VALUES.values()) * weight
        rating_label = _text(topic_ratings.get(topic))
        rating_value = TOPIC_VALUES.get(rating_label) if rating_label else None
        weighted_points = None if rating_value is None else rating_value * weight
        contributions[topic] = {
            "rating_label": rating_label or None,
            "rating_value": rating_value,
            "weight": weight,
            "weighted_points": weighted_points,
        }
        if rating_value is None:
            missing_topics.append(topic)
        else:
            earned += weighted_points

    if maximum == 0:
        raise ValueError("At least one positive course topic weight is required")

    score = None if missing_topics else round(100.0 * earned / maximum, 1)
    return {
        "score": score,
        "earned_points": round(earned, 3),
        "maximum_points": round(maximum, 3),
        "contributions": contributions,
        "missing_topics": missing_topics,
    }


def score_candidate(
    profile: Mapping[str, Any],
    course: str,
    course_weights: Mapping[str, float],
    *,
    topic_weight: float = 0.6,
    preference_weight: float = 0.4,
) -> dict[str, Any]:
    """Score one candidate for one course."""

    if not math.isclose(topic_weight + preference_weight, 1.0, abs_tol=1e-9):
        raise ValueError("Topic and preference weights must add up to 1.0")
    if topic_weight < 0 or preference_weight < 0:
        raise ValueError("Topic and preference weights cannot be negative")

    preference = profile["course_preferences"].get(course, "")
    topic_fit = calculate_topic_fit(profile["topic_ratings"], course_weights)
    disqualifiers: list[str] = []

    if preference == CANNOT_TA:
        disqualifiers.append("candidate marked course as Cannot TA")
    elif not preference:
        disqualifiers.append("course preference is missing")
    if topic_fit["missing_topics"]:
        disqualifiers.append("one or more required topic ratings are missing")

    preference_score = PREFERENCE_VALUES.get(preference)
    eligible = not disqualifiers
    overall_score = None
    if eligible and topic_fit["score"] is not None and preference_score is not None:
        overall_score = round(
            topic_fit["score"] * topic_weight
            + preference_score * preference_weight,
            1,
        )

    return {
        "candidate_id": profile.get("candidate_id", ""),
        "name": profile.get("name", ""),
        "email": profile.get("email", ""),
        "course": course,
        "eligible": eligible,
        "disqualifiers": disqualifiers,
        "topic_fit": topic_fit["score"],
        "preference": preference,
        "preference_score": preference_score,
        "overall_score": overall_score,
        "topic_contributions": topic_fit["contributions"],
        "missing_topics": topic_fit["missing_topics"],
        "scheduling_constraints": profile.get("scheduling_constraints", ""),
        "course_constraints": profile.get("course_constraints", ""),
        "notes": profile.get("notes", ""),
    }


def build_rankings(
    extracted_data: Mapping[str, Any],
    course_topic_weights: Mapping[str, Mapping[str, float]],
    *,
    topic_weight: float = 0.6,
    preference_weight: float = 0.4,
) -> list[dict[str, Any]]:
    """Score all configured courses and sort eligible candidates first."""

    profiles = extracted_data["profiles"]
    known_courses = set(extracted_data["courses"])
    known_topics = set(extracted_data["topics"])

    unknown_courses = sorted(set(course_topic_weights) - known_courses)
    if unknown_courses:
        raise ValueError(
            "Course mappings do not match extracted Top choices headers: "
            + ", ".join(unknown_courses)
        )

    unknown_topics = {
        course: sorted(set(weights) - known_topics)
        for course, weights in course_topic_weights.items()
        if set(weights) - known_topics
    }
    if unknown_topics:
        details = "; ".join(
            f"{course}: {', '.join(topics)}"
            for course, topics in sorted(unknown_topics.items())
        )
        raise ValueError(
            "Course mappings contain topics that do not match extracted Topic Areas "
            f"headers: {details}"
        )

    results = [
        score_candidate(
            profile,
            course,
            weights,
            topic_weight=topic_weight,
            preference_weight=preference_weight,
        )
        for course, weights in course_topic_weights.items()
        for profile in profiles
    ]
    results.sort(
        key=lambda result: (
            result["course"],
            not result["eligible"],
            -(result["overall_score"] if result["overall_score"] is not None else -1),
            result["name"].casefold(),
        )
    )
    return results


def write_json(
    destination: TextIO,
    extracted_data: Mapping[str, Any],
    results: list[dict[str, Any]],
    course_topic_weights: Mapping[str, Mapping[str, float]],
    topic_weight: float,
    preference_weight: float,
) -> None:
    payload = {
        "schema_version": 1,
        "source": extracted_data.get("source", {}),
        "model": {
            "topic_values": TOPIC_VALUES,
            "preference_values": PREFERENCE_VALUES,
            "cannot_ta_value": CANNOT_TA,
            "topic_weight": topic_weight,
            "preference_weight": preference_weight,
            "course_topic_weights": course_topic_weights,
        },
        "profile_count": len(extracted_data["profiles"]),
        "ranking_count": len(results),
        "rankings": results,
    }
    json.dump(payload, destination, indent=2, ensure_ascii=False)
    destination.write("\n")


def write_csv(destination: TextIO, results: Iterable[dict[str, Any]]) -> None:
    fieldnames = [
        "course",
        "candidate_id",
        "name",
        "email",
        "eligible",
        "overall_score",
        "topic_fit",
        "preference",
        "preference_score",
        "disqualifiers",
        "scheduling_constraints",
        "course_constraints",
        "notes",
        "topic_contributions",
    ]
    writer = csv.DictWriter(destination, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for result in results:
        row = dict(result)
        row["disqualifiers"] = "; ".join(result["disqualifiers"])
        row["topic_contributions"] = json.dumps(
            result["topic_contributions"], ensure_ascii=False, sort_keys=True
        )
        writer.writerow(row)


def _positive_fraction(value: str) -> float:
    parsed = float(value)
    if not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("value must be between 0 and 1")
    return parsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rank normalized TA preferences using course-topic weights."
    )
    parser.add_argument("preferences", type=Path, help="Extracted preference JSON")
    parser.add_argument(
        "--course-map",
        required=True,
        type=Path,
        help="JSON file mapping course names to topic weights",
    )
    parser.add_argument("--output", type=Path, help="Output path; defaults to stdout")
    parser.add_argument("--format", choices=("json", "csv"), default="json")
    parser.add_argument("--topic-weight", type=_positive_fraction, default=0.6)
    parser.add_argument("--preference-weight", type=_positive_fraction, default=0.4)
    args = parser.parse_args(argv)
    if not math.isclose(
        args.topic_weight + args.preference_weight, 1.0, abs_tol=1e-9
    ):
        parser.error("--topic-weight and --preference-weight must add up to 1.0")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    extracted_data = load_extracted_preferences(args.preferences)
    course_topic_weights = load_course_topic_weights(args.course_map)
    rankings = build_rankings(
        extracted_data,
        course_topic_weights,
        topic_weight=args.topic_weight,
        preference_weight=args.preference_weight,
    )

    destination: TextIO
    close_destination = False
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        destination = args.output.open("w", encoding="utf-8", newline="")
        close_destination = True
    else:
        destination = sys.stdout

    try:
        if args.format == "json":
            write_json(
                destination,
                extracted_data,
                rankings,
                course_topic_weights,
                args.topic_weight,
                args.preference_weight,
            )
        else:
            write_csv(destination, rankings)
    finally:
        if close_destination:
            destination.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
