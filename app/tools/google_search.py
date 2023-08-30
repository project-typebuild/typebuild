from googlesearch import search

def get_google_search_results(search_term, sleep_interval=5, num_results=10):

    """
    Get google search results for a search term.

    Args:
    - search_term (str): The search term.
    - sleep_interval (int): The sleep interval between each search. default 5.
    - num_results (int): The number of results to return. default 10.

    Returns:
    - results (list): A list of search results. Each search result is a dictionary with the url, title, and description.
    """
    results = []
    if num_results > 100:
        for result in search(search_term, sleep_interval=sleep_interval, num_results=num_results, advanced=True):
            tmp_dict = {}
            tmp_dict['url'] = result.url
            tmp_dict['title'] = result.title
            tmp_dict['description'] = result.description
            results.append(tmp_dict)
    else:
        for result in search(search_term, num_results=num_results, advanced=True):
            tmp_dict = {}
            tmp_dict['url'] = result.url
            tmp_dict['title'] = result.title
            tmp_dict['description'] = result.description
            results.append(tmp_dict)

    return results