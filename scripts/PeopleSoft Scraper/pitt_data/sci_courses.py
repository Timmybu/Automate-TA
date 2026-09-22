import requests

from request_cache_decorator import cache_request
import config


@cache_request(ttl=86400, force=not config.use_cache, cache_dir=config.cache_dir)
def sci_course_data(term):
	# Public School of Computing & Information course mirror (CS/CMPINF only, no auth needed).
	url = f"https://courses.sci.pitt.edu/{term}.json"
	return requests.get(url, timeout=20).json()


def section_info(term):
	# Maps class_number (matches PeopleSoft's class_nbr) -> {"room": "BLDG room" or "",
	# "section_group": str or None}. section_group is the lecture/recitation grouping key
	# (e.g. "1010") shown on courses.sci.pitt.edu itself as "21904 (1010)" -- it does NOT
	# line up with PeopleSoft's own class_section values or feed order, so it's the only
	# reliable way to associate a REC/LAB back to its lecture. Not every class_nbr is
	# present here (this feed only covers CS/CMPINF, and even within those a handful of
	# classes are missing), and a few section_groups have no lecture at all -- seen for
	# unstaffed, zero-enrollment placeholder recitations (e.g. CS 0441 group "1150" for
	# term 2271) that SCI's own scheduling data never linked to a lecture. Callers should
	# fall back gracefully in both cases.
	data = sci_course_data(term)
	info = {}
	for entry in data.get("sections", {}).values():
		if not entry:
			continue
		section = entry.get("Section")
		if not section:
			continue
		room = entry.get("Room") or {}
		room_str = f"{room['bldg']} {room['room']}" if room.get("bldg") and room.get("room") else ""
		info[str(section["class_number"])] = {
			"room": room_str,
			"section_group": section.get("section_group"),
		}
	return info
