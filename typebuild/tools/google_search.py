from googlesearch import search
from datetime import datetime
import requests 
import tldextract
import streamlit as st
import time
import pandas as pd
import os
from bs4 import BeautifulSoup

from googlesearch import search
from datetime import datetime
import requests
import tldextract
import pandas as pd
import os
from bs4 import BeautifulSoup

class GoogleSearchSaver:
    """
    Class to perform Google search, store results, and optionally save them to a Parquet file.

    Attributes:
    - results (list): List of search results.
    - file_name (str): Name of the saved Parquet file, if saved.
    """

    def __init__(self):
        self.results = []
        self.file_name = None

    def get_google_search_results(self, search_term, sleep_interval=2, num_results=10):
        """
        Perform a Google search and store the results.

        Args:
        - search_term (str): The search term.
        - sleep_interval (int): The interval between searches. Default is 2 seconds.
        - num_results (int): Number of results to return. Default is 10.
        """
        for result in search(search_term, sleep_interval=sleep_interval, num_results=num_results, advanced=True):
            page_content = BeautifulSoup(requests.get(result.url).content).get_text()
            self.results.append({
                'url': result.url,
                'title': result.title,
                'description': result.description,
                'text_content': page_content,
                'domain': tldextract.extract(result.url).domain
            })

    def get_results_as_list(self):
        """
        Retrieve the stored search results as a list.

        Returns:
        - List of dictionaries containing search results.
        """
        return self.results

    def get_results_as_string(self):
        """
        Retrieve the stored search results as a string.

        Returns:
        - String representation of search results.
        """
        return "\n".join([str(result) for result in self.results])

    def store_to_db(self, search_term, project_folder):
        """
        Save the stored results to a Parquet file.

        Args:
        - search_term (str): The search term used.
        - project_folder (str): The project folder to save the file in.
        """
        df_results = pd.DataFrame(self.results)
        df_results['search_term'] = search_term
        df_results['search_date'] = pd.to_datetime(datetime.now())

        cleaned_search_term_for_filename = self._clean_search_term_for_filename(search_term)
        self.file_name = os.path.join(project_folder, 'data', f'google_{cleaned_search_term_for_filename}.parquet')
        df_results.to_parquet(self.file_name, index=False)

    def get_file_name(self):
        """
        Retrieve the name of the saved Parquet file.

        Returns:
        - String: Name of the saved Parquet file.
        """
        return self.file_name

    @staticmethod
    def _clean_search_term_for_filename(search_term):
        """
        Clean the search term to be used in a file name.

        Args:
        - search_term (str): The search term.

        Returns:
        - String: Cleaned search term suitable for use in a file name.
        """
        cleaned = ''.join(e for e in search_term if e.isalnum() or e in ['_'])
        return cleaned[:500]  # Limit the length to 500 characters

# Example usage
# searcher = GoogleSearchSaver()
# searcher.get_google_search_results('example search', num_results=5)
# results_list = searcher.get_results_as_list()
# results_string = searcher.get_results_as_string()
# searcher.store_to_db('example search', '/path/to/project_folder')
# file_name = searcher.get_file_name()


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
        tmp_dict['text_content'] = BeautifulSoup(requests.get(result.url).content).get_text()
        tmp_dict['domain'] = tldextract.extract(result.url).domain
        results.append(tmp_dict)
    
    df_results = pd.DataFrame(results)
    df_results['search_term'] = search_term
    df_results['search_date'] = pd.to_datetime(datetime.now())

    col_names = ['url','title','description','text_content','domain','search_term','search_date']

    col_types = ['str','str','str','str','str','str','datetime']

    col_infos = ['The url of the webpage.', 'The title of the webpage.', 'The description of the webpage.', 'The text content of the webpage.', 'The domain of the webpage.', 'The search term.', 'The date of the search.']

    df_data_model = pd.DataFrame({'column_name': col_names, 'column_type': col_types, 'column_info': col_infos})

    cleaned_search_term_for_filename = search_term.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '').replace(':', '').replace('.', '').replace(',', '').replace('?', '').replace('!', '').replace("'", '').replace('"', '').replace('-', '').replace('&', '').replace(';', '').replace('=', '').replace('+', '').replace('*', '').replace('$', '').replace('#', '').replace('@', '')
    # Limit the length of the filename to 500 characters
    if len(cleaned_search_term_for_filename) > 500:
        cleaned_search_term_for_filename = cleaned_search_term_for_filename[:500]
    file_name = os.path.join(st.session_state.project_folder, 'data', f'google_{cleaned_search_term_for_filename}.parquet')

    df_data_model['file_name'] = file_name

    # Save the data model to the project folder, append to the existing data model
    data_model_file = os.path.join(st.session_state.project_folder, 'data_model.parquet')
    all_dfs = []
    if os.path.exists(data_model_file):
        current_model = pd.read_parquet(data_model_file)
        all_dfs.append(current_model)
        all_dfs.append(df_data_model)
        df_all_col_infos = pd.concat(all_dfs)
        df_all_col_infos.to_parquet(data_model_file, index=False)
    else:
        df_data_model.to_parquet(data_model_file, index=False)

    # Save results to parquet
    df_results.to_parquet(file_name, index=False)
    st.session_state['google_file_name'] = file_name
    return None


def main():
    # Create an instance of the GoogleSearchSaver class
    searcher = GoogleSearchSaver()

    search_term = st.text_input('Enter search term')
    num_results = st.number_input('Enter number of results', min_value=1, max_value=50, value=10)

    if st.button('Get results'):
        with st.spinner('Getting results...'):
            # Perform the Google search
            searcher.get_google_search_results(search_term, num_results=num_results)

            # TODO: DELETE THIS
            st.session_state.project_folder = 'tmp'

            # Save results to a Parquet file
            searcher.store_to_db(search_term, project_folder=st.session_state.project_folder)

            # Retrieve and display the file name where results are saved
            file_name = searcher.get_file_name()
            st.success('Done.')
            st.write('Results saved to parquet file.')
            st.write(f"Data saved to {file_name}")