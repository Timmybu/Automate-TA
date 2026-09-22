import requests

from util import perror, ask_for_continue
from request_cache_decorator import cache_request
import config


@cache_request(ttl=86400, force=not config.use_cache, cache_dir=config.cache_dir)
def class_details(term, class_nbr):
	url = f"https://pitcsprd.csps.pitt.edu/psc/pitcsprd/EMPLOYEE/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassDetails?institution=UPITT&term={term}&class_nbr={class_nbr}"
	try:
		json_content = requests.get(url)
	except requests.exceptions.RequestException as e:
		perror(f"Error downloading json from {url}: {e}")
		return None
	try:
		return json_content.json()
	except requests.exceptions.JSONDecodeError as e:
		perror(f"Data is not json: {e}")
		if ask_for_continue("Print response as text?"):
			print(json_content.text)
		return None
