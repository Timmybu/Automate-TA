class ClassSearchResult:
	def __init__(self, data):
		self.data = data

	# "index": 1,
	# "institution": "UPITT",
	# "institution_descr": "University of Pittsburgh",
	# "crse_id": "105611",
	def course_id(self): return self.data["crse_id"]
	# "crse_offer_nbr": 1,
	# "strm": "2271",
	# "session_code": "AT",
	# "session_descr": "Academic Term",
	# "class_section": "1050",
	def class_section(self): return self.data["class_section"]
	# "location": "PGH",
	# "location_descr": "Pittsburgh Campus",
	# "start_dt": "08/24/2026",
	# "end_dt": "12/04/2026",
	# "class_stat": "A",
	# "campus": "PIT",
	# "campus_descr": "Pittsburgh Campus",
	# "class_nbr": 11033,
	def class_number(self): return self.data["class_nbr"]
	# "acad_career": "UGRD",
	# "acad_career_descr": "Undergraduate",
	# "component": "LEC",
	def component(self): return self.data["component"]
	# "subject": "CS",
	def subject(self): return self.data["subject"]
	# "subject_descr": "Computer Science",
	# "catalog_nbr": "0007",
	def catalog_number(self): return self.data["catalog_nbr"]
	# "class_type": "E",
	# "schedule_print": "Y",
	# "acad_group": "SCI",
	# "instruction_mode": "PS",
	# "instruction_mode_descr": "In Person - S25",
	# "acad_org": "CSCI",
	# "grading_basis": "LG/SNC Elective Basis",
	# "wait_tot": 0,
	# "wait_cap": 20,
	# "class_capacity": 50,
	def class_capacity(self): return self.data["class_capacity"]
	# "enrollment_total": 28,
	def enrollment_total(self): return self.data["enrollment_total"]
	# "enrollment_available": 22,
	# "descr": "INTRODUCTION TO COMPUTER PROGRAMMING",
	def class_name(self): return self.data["descr"]
	# "rqmnt_designtn": "",
	# "units": "3",
	# "combined_section": "N",
	def cross_listed(self): return self.data["combined_section"] == "Y"
	# "enrl_stat": "O",
	# "enrl_stat_descr": "Open",
	# "topic": "",
	# "instructors": [
	# {
	# 	"name": "Timothy Hoffman",
	# 	"email": ""
	# }
	# ],
	def instructors(self): return [ (instructor["name"], instructor["email"]) for instructor in self.data["instructors"]]
	# "section_type": "Lecture",
	def section_type(self): return self.data["section_type"]
	# "meetings": [
	# {
	# 	"days": "MoWe",
	# 	"start_time": "16.30.00.000000",
	# 	"end_time": "17.45.00.000000",
	# 	"start_dt": "08/24/2026",
	# 	"end_dt": "12/04/2026",
	# 	"instructor": "Timothy Hoffman",
	# 	# room fields below are only present when class_search was fetched with an
	# 	# authenticated session; the public/anonymous endpoint omits them entirely
	# 	"bldg_cd": "SENSQ",
	# 	"bldg_has_coordinates": true,
	# 	"facility_descr": "5502 Sennott Square",
	# 	"room": "05502",
	# 	"facility_id": "SENSQ05502"
	# }
	# ],
	def meeting_days(self): return self.data["meetings"][0]["days"]
	def start_time(self): return self.data["meetings"][0]["start_time"]
	def room(self): return self.data["meetings"][0].get("facility_descr", "")
	def end_time(self): return self.data["meetings"][0]["end_time"]
	# "crse_attr": "DSGE,FNL",
	# "crse_attr_value": "DSGE-ALG,DSGE-QFR,FNL-HOURLY",
	# "reserve_caps": [
	# {
	# 	"rsrv_cap_nbr": 1,
	# 	"start_dt": "03/01/2026",
	# 	"enrl_cap": 10,
	# 	"descr": "SCI 1st Year",
	# 	"end_dt": "09/04/2026",
	# 	"enrl_tot": 10
	# },
	# {
	# 	"rsrv_cap_nbr": 2,
	# 	"start_dt": "03/01/2026",
	# 	"enrl_cap": 22,
	# 	"descr": "SCI Launch A",
	# 	"enrl_tot": 0
	# }
	# ],
	# "reserved_combined_info": {
	# "class_enrl_cap": 7,
	# "combined_enrl_cap": ...,
	# "enrl_tot_other_combined": ...
	# },
	# "icons": []
	def __str__(self):
		return f"{self.subject()}{self.catalog_number()}-{self.class_section()} ({self.class_number()}) {self.section_type()} {self.meeting_days()} {self.start_time()}-{self.end_time()}: {self.enrollment_total()}/{self.class_capacity()}"
