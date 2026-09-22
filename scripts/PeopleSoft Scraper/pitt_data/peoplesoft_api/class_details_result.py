class ClassDetailsResult:
	def __init__(self, data):
		self.data = data

	# "show_validate": "N",
	# "show_waitlist": "Y",
	# "section_info": {
	# 	"class_details": {
	# 		"institution": "UPITT",
	# 		"subject": "CS",
	def subject(self): return self.data["section_info"]["class_details"]["subject"]
	# 		"catalog_nbr": "1520",
	def catalog_number(self): return self.data["section_info"]["class_details"]["catalog_nbr"]
	# 		"status": "Open",
	# 		"class_number": 20951,
	def class_number(self): return self.data["section_info"]["class_details"]["class_number"]
	# 		"component": "LEC",
	def section_type(self): return self.data["section_info"]["class_details"]["component"]
	# 		"course_offer_nbr": 1,
	# 		"session": "Full Term Session",
	# 		"session_code": "SE3",
	# 		"class_section": "1050",
	def class_section(self): return self.data["section_info"]["class_details"]["class_section"]
	# 		"acad_org": "CSCI",
	# 		"section_descr": "CS 1520 - 1050",
	# 		"units": "3 units",
	# 		"acad_career": "UGRD",
	# 		"acad_career_descr": "Undergraduate",
	# 		"course_id": "105767",
	# 		"course_title": "PROGRAMMING LANGUAGE FOR WEB APPLICATIONS",
	# 		"course_status": "A",
	# 		"instruction_mode": "",
	# 		"grading_basis": "LG/SNC Elective Basis",
	# 		"campus": "Pittsburgh Campus",
	# 		"campus_code": "PIT",
	# 		"location": "Pittsburgh Campus",
	# 		"topic": "",
	# 		"class_components": "<table class=\"PSTEXT\">...</table>"
	# 	},
	# 	"meetings": [
	# 		{
	# 			"meets": "MoWe 6:00PM - 7:15PM",
	# 			"days": "MoWe",
	def meeting_days(self): return self.data["section_info"]["meetings"][0]["days"]
	# 			"show_days": true,
	# 			"meeting_time_start": "6:00PM",
	def start_time(self): return self.data["section_info"]["meetings"][0]["meeting_time_start"]
	# 			"meeting_time_end": "7:15PM",
	def end_time(self): return self.data["section_info"]["meetings"][0]["meeting_time_end"]
	# 			"bldg_cd": "IS",
	# 			"bldg_has_coordinates": false,
	# 			"meeting_topic": "TBA",
	# 			"instructors": [ { "name": "Brian Nixon", "email": "" } ],
	def instructors(self): return [ (instructor["name"], instructor["email"]) for instructor in self.data["section_info"]["meetings"][0]["instructors"]]
	# 			"topic": "TBA",
	# 			"show_topic": false,
	# 			"date_range": "08/24/2026 - 12/12/2026"
	# 		}
	# 	],
	# 	"enrollment_information": {
	# 		"add_consent": "",
	# 		"drop_consent": "",
	# 		"enroll_requirements": "PREQ: CS 0445; (MIN GRADE 'C' or Transfer)",
	# 		"requirement_desig": "",
	# 		"class_attributes": ""
	# 	},
	# 	"class_availability": {
	# 		"class_capacity": "56",
	def class_capacity(self): return int(self.data["section_info"]["class_availability"]["class_capacity"])
	# 		"enrollment_total": "28",
	def enrollment_total(self): return int(self.data["section_info"]["class_availability"]["enrollment_total"])
	# 		"enrollment_available": 28,
	# 		"wait_list_capacity": "20",
	# 		"wait_list_total": "0"
	# 	},
	# 	"reserve_caps": [],
	# 	"is_combined": false,
	def is_combined(self): return self.data["section_info"]["is_combined"]
	# 	# only present when is_combined is true; excludes this class itself
	# 	"combined_sections": [ { "subject": "CS", "catalog_nbr": "0007", "class_section": "1051", "class_nbr": "26796", ... } ],
	def combined_sections(self): return self.data["section_info"].get("combined_sections", [])
	# 	"notes": {
	# 		"class_notes": "",
	# 		"subject_notes": ""
	# 	},
	# 	"catalog_descr": {
	# 		"crse_catalog_description": "..."
	# 	},
	# 	"materials": {
	# 		"txb_none": "N",
	# 		"txb_status": "P",
	# 		"txb_special_instructions": "",
	# 		"textbooks_message": "Textbooks to be determined"
	# 	},
	# 	"valid_to_enroll": "T"
	# },
	# "class_enroll_info": {
	# 	"last_enrl_dt_passed": false,
	# 	"is_related": false
	# },
	# "additionalLinks": [],
	# "cfg": {
	# 	# feature-flag booleans controlling what the PeopleSoft UI shows/allows;
	# 	# not used here (e.g. show_campus, show_class_availability, can_enroll_class, ...)
	# },
	# "messages": {
	# 	"shareLink": "Copy link to share the class with friends.",
	# 	"shareSocial": "Or share on social media networks.",
	# 	"reserveInfo": "Seats in this class have been reserved for students for the specified programs, majors or groups listed below. Reserved seats are subject to change without notice.",
	# 	"noMeetingInfo": "No meeting info found"
	# }

	def __str__(self):
		return f"{self.subject()}{self.catalog_number()}-{self.class_section()} ({self.class_number()}) {self.section_type()} {self.meeting_days()} {self.start_time()}-{self.end_time()}: {self.enrollment_total()}/{self.class_capacity()}"
