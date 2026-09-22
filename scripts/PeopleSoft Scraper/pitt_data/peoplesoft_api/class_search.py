import requests

from util import perror, ask_for_continue
from request_cache_decorator import cache_request
import config


def get_classes_all(url):
	page = 0
	n_pages = 1
	data = []
	while page < n_pages:
		message = "Requesting page" if page == 0 else f"Requesting {page+1} out of {n_pages}"
		print(message)

		try:
			json_content = requests.get(f"{url}&page={page+1}")
		except requests.exceptions.RequestException as e:
			perror(f"Error downloading json from {url}: {e}")
			return

		try:
			data_json = json_content.json()
		except requests.exceptions.JSONDecodeError as e:
			perror(f"Data is not json: {e}")
			if ask_for_continue("Print response as text?"):
				print(json_content.text)
			return
		if page == 0:
			n_pages = data_json["pageCount"]

		data.extend(data_json["classes"])
		page = page + 1
	return data


@cache_request(ttl=86400, force=not config.use_cache, cache_dir=config.cache_dir)
def class_search(term, subject, catalog_nbr=None):
	url = f"https://pitcsprd.csps.pitt.edu/psc/pitcsprd/EMPLOYEE/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch?institution=UPITT&campus=PIT&term={term}&subject={subject}"
	if catalog_nbr is not None:
		url = f"{url}&catalog_nbr={catalog_nbr}"
	return get_classes_all(url)
