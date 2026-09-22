from pitt_data.peoplesoft_api.class_search import *
from pitt_data.peoplesoft_api.class_details import *


term = "2271"
compare = ["2261"]
csvpath = "reports/class_report_2271.csv"
xlsxpath = "reports/class_report_2271.xlsx"
# subject = "CS"
# catalog_number = "0447"

# import pdb; pdb.set_trace()
# out = class_search(2271, "CS")
# out = class_search(2271, "CS", "0447")
# class_details(2271, out[0]["class_nbr"])

from generators.gen_class_csv import gen_csv
from generators.gen_class_xlsx import gen_xlsx
from ta_assignment.ta_needs_estimation import calculate_needs
gen_csv(term, compare, csvpath)
calculate_needs(csvpath, csvpath)
gen_xlsx(csvpath, xlsxpath)
