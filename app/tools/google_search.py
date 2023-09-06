from googlesearch import search
from datetime import datetime
import requests 
import tldextract

def get_google_search_results(search_term, sleep_interval=2, num_results=10):

    """
    Get google search results for a search term.

    Args:
    - search_term (str): The search term.
    - sleep_interval (int): The sleep interval between each search. default 2.
    - num_results (int): The number of results to return. default 10.

    Returns:
    - results (list): A list of search results. Each search result is a dictionary with the url, title, and description.
    """
    results = []
    for result in search(search_term, sleep_interval=sleep_interval, num_results=num_results, advanced=True):
        tmp_dict = {}
        tmp_dict['url'] = result.url
        tmp_dict['title'] = result.title
        tmp_dict['description'] = result.description
        tmp_dict['text_content'] = requests.get(result.url).text
        tmp_dict['domain'] = tldextract.extract(result.url).domain
        results.append(tmp_dict)
    
    df_results = pd.DataFrame(results)
    df_results['search_term'] = search_term
    df_results['search_date'] = pd.to_datetime(datetime.now())
    

    return results