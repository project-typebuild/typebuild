from googlesearch import search
from datetime import datetime
import requests 
import tldextract
import streamlit as st

def get_google_search_results(search_term, sleep_interval=2, num_results=10):

    """
    Get google search results for a search term.

    Args:
    - search_term (str): The search term.
    - sleep_interval (int): The sleep interval between each search. default 2.
    - num_results (int): The number of results to return. default 10.

    Returns:
    - None: Saves the results to a parquet file. The dataframe has the following columns:
        - url (str): The url of the webpage.
        - title (str): The title of the webpage.
        - description (str): The description of the webpage.
        - text_content (str): The text content of the webpage.
        - domain (str): The domain of the webpage.
        - search_term (str): The search term.
        - search_date (datetime): The date of the search.
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
   # remove the spaces, special characters, and convert to lowercase for the file_name
    file_name = search_term.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '').replace(':', '').replace('.', '').replace(',', '').replace('?', '').replace('!', '').replace("'", '').replace('"', '').replace('-', '').replace('&', '').replace(';', '').replace('=', '').replace('+', '').replace('*', '').replace('$', '').replace('#', '').replace('@', '')
 
    # Write a data model for the streamlit app
    data_model = f"""
    INFORMATION ABOUT THE PROJECT DATA FILE(S)
    -------------------------------------------
    This data file was created using the following search term: {search_term}

    File path to the data file: {st.session_state.project_folder}/data/{file_name}.parquet
    The data file contains the following columns:
    - url (str): The url of the webpage.
    - title (str): The title of the webpage.
    - description (str): The description of the webpage.
    - text_content (str): The text content of the webpage.
    - domain (str): The domain of the webpage.
    - search_term (str): The search term.
    - search_date (datetime): The date of the search.
    """

    # Save results to parquet
    df_results.to_parquet(f'{st.session_state.project_folder}/data/{file_name}.parquet', index=False)
    
    return None