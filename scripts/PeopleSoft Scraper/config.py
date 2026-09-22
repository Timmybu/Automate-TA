# Configurations
shrinking_rate = 0.85
recitaiton_cutoff = 400
cmpinf_recitaiton_cutoff = 401
cutoff_75 = 445

enable_caching = True
force_fetch = False

term_of_interest = 2271
data = [ # Data we are interested in
	# (2241, "CMPINF"),
	# (2244, "CMPINF"),
	# (2251, "CMPINF"),
	# (2254, "CMPINF"),
	(2261, "CMPINF"),
	# (2264, "CMPINF"),
	(2271, "CMPINF"),
	# (2241, "CS"),
	# (2244, "CS"),
	# (2251, "CS"),
	# (2254, "CS"),
	(2261, "CS"),
	# (2264, "CS"),
	(2271, "CS"),
]

import os
use_cache = True
cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")

cs_ignore_courses = [1901, 1906, 1951]
cs_dont_ignore_courses = [1950]
ignore_components = ["IND", "THE", "DIR", "CLQ"]
# cls_data must expose .subject(), .catalog_number(), .type() -- ClassSearchResult
# satisfies this via the small adapter in gen_class_csv.py's _passes_filter().
def courses_filter(cls_data):
	subject = cls_data.subject()
	number = cls_data.catalog_number()
	component = cls_data.type()
	cmpinf = [10, 11, 401]
	cmpinf_true = (subject == "CMPINF") and (int(number) in cmpinf)
	# if subject == "CMPINF" and cmpinf_true:
	# 	print(subject+" "+number)

	is_CS_low = (subject == "CS") and (int(number) < 2900)
	dont_ignore = (subject == "CS") and (int(number) in cs_dont_ignore_courses)

	ignore_CS_ms = (subject == "CS") and (int(number) >= 2000 and int(number) < 2010)
	ignore = (subject == "CS") and (int(number) in cs_ignore_courses)
	ignore = ignore or ignore_CS_ms
	cs_true = is_CS_low and not ignore

	# if subject == "CS" and cs_true:
	# 	print(subject+" "+number)

	ignore_component = component not in ignore_components

	return (cmpinf_true or cs_true) and (ignore_component or dont_ignore)

