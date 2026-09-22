# Pitt PeopleSoft IScript endpoints

Reverse-engineered endpoints under `https://pitcsprd.csps.pitt.edu/psc/pitcsprd/EMPLOYEE/SA/s/`, discovered via browser network inspection (not officially documented by Pitt/PeopleSoft/Oracle). All return JSON. None are wrapped by any `institution` value other than `UPITT`.

All were tested anonymously (no session cookie). **None of them expose a room/building field to anonymous requests** — see [Room data](#room-data) below.

| IScript function | Used by | Query params | Returns |
|---|---|---|---|
| `WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch` | [class_search.py](class_search.py) | `institution`, `campus`, `term`, `subject`, `catalog_nbr` (optional), `page` | Paginated list of class sections for a subject/term (optionally filtered to one catalog number): enrollment, capacity, meeting days/times, instructors, cross-listing flag. |
| `WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassDetails` | [class_details.py](class_details.py) | `institution`, `term`, `class_nbr` | Full detail for one class section: meetings, enrollment, textbook/materials info, cross-listed sections (`combined_sections`), enrollment requirements. |
| `WEBLIB_HCX_CM.H_COURSE_CATALOG.FieldFormula.IScript_SubjectCourses` | not used | `institution`, `subject` | Catalog listing of every course number in a subject (title, `crse_id`, whether it has open terms). No schedule info. |
| `WEBLIB_HCX_CM.H_COURSE_CATALOG.FieldFormula.IScript_CatalogCourseDetails` | not used | `institution`, `course_id`, `use_catalog_print`, `effdt`, `crse_offer_nbr`, `subject`, `catalog_nbr`, `typ_offr` | Static catalog description for one course: long description, units, components (Lecture/Recitation/...), attributes, prerequisites, terms it's offered. No schedule/room. |
| `WEBLIB_HCX_CM.H_BROWSE_CLASSES.FieldFormula.IScript_CourseCampuses` | not used | `institution`, `term`, `x_acad_career`, `course_id` | List of campuses (e.g. `PIT` / "Pittsburgh Campus") the course is offered at that term. Campus-level only. |
| `WEBLIB_HCX_CM.H_BROWSE_CLASSES.FieldFormula.IScript_CourseLocations` | not used | `institution`, `term`, `x_acad_career`, `course_id`, `campus` | List of locations (e.g. `PGH` / "Pittsburgh Campus"). Despite the name, this is campus-level, not building/room. |
| `WEBLIB_HCX_CM.H_BROWSE_CLASSES.FieldFormula.IScript_BrowseSections` | not used | `institution`, `term`, `x_acad_career`, `subject`, `catalog_nbr`, `course_id`, `campus`, `location` | Section list for a course, similar shape to `IScript_ClassSearch` (enrollment, meetings, instructors). Same reduced meeting fields anonymously. |
| `WEBLIB_HCX_GN.H_MAP.FieldFormula.IScript_GetBuilding` | not used | `bldg_cd` (e.g. `SENSQ`) | `{"building":{"descr":"Sennott Square","latitude":40.441494,"longitude":-79.95633},"use_google_maps":false,"google_maps_api_key":""}`, followed by map tile/pin PNGs. Building name + coordinates for the map widget — no room number, so it doesn't help resolve a specific class's room. Requires auth (see note below). |

## Room data on the PeopleSoft endpoints

`class_search`/`class_details` meeting objects normally only contain `days`, `start_time`, `end_time`, `start_dt`, `end_dt`, `instructor`. A browser session that's logged into Pitt's PeopleSoft portal gets a richer meeting object with `bldg_cd`, `bldg_has_coordinates`, `facility_descr` (e.g. `"5502 Sennott Square"`), `room` (e.g. `"05502"`), and `facility_id` (e.g. `"SENSQ05502"`).

This is a genuine server-side authorization difference, not a Cloudflare/bot-detection artifact — an anonymous request to the exact same class returns 200 with valid JSON, just missing those five fields. Every endpoint in the table above was checked anonymously and all omit room data the same way, so this isn't specific to one endpoint.

Reproducing it requires a live, currently-valid PeopleSoft session cookie (`PS_TOKEN` + related cookies) from a logged-in browser session — these expire/rotate frequently (observed rotating within the same day), so there's no way to make this work from cached/hardcoded credentials. We deliberately did not build any tooling that stores or reads a session cookie for this reason.

`IScript_GetBuilding` sits behind a stricter gate than the rest: it redirects unauthenticated requests straight to Pitt's central Shibboleth SSO (`passport.pitt.edu`), even with browser-matching headers, rather than returning a reduced-but-valid JSON body the way every `WEBLIB_HCX_CM` endpoint above does. Its authenticated response is now confirmed (see table) — it's a building-level lookup (name + lat/long for the map widget), not a room lookup, so even with auth it wouldn't help populate `Room`.

## Room data — solved via courses.sci.pitt.edu

Room actually ended up available anonymously, just from an entirely different, unrelated system: `https://courses.sci.pitt.edu/{term}.json` — the School of Computing & Information's own public course-schedule mirror, not PeopleSoft, no auth required. See [../sci_courses.py](../sci_courses.py).

Its `sections` object is keyed by an arbitrary numeric string, and each value has a `Section.class_number` field that matches PeopleSoft's `class_nbr` exactly, plus a `Room` object (`{"bldg": "SENSQ", "room": "5502"}`) — cross-checked against CS 0447 class 22066, whose authenticated PeopleSoft `facility_descr` was `"5502 Sennott Square"`. Match confirmed.

Caveat: this feed only covers CS/CMPINF (SCI's own courses), which happens to be exactly what `config.data` cares about. Some `sections` entries have a `null` `Section` (cancelled/placeholder rows) and must be skipped.

`gen_class_csv.py` now sources `Room` from `sci_courses.section_info(term)` instead of leaving it blank.

## Other avenues checked

- **25Live** (Pitt's room-booking system, CollegeNET): has a public, no-login "STUDENT STUDY SPACES" search, but it only shows room *availability* (busy/free grid), not which course occupies a room. No course-to-room lookup without Pitt login.
- **Official Pitt API**: none exists. The only related public project is the community-maintained [PittAPI](https://github.com/pittcsc/PittAPI) (Pitt CS Club); not evaluated in depth here.
