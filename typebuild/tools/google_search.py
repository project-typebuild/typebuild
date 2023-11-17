import streamlit as st
from googlesearch import search
from datetime import datetime
import requests
import tldextract
import pandas as pd
import os
from bs4 import BeautifulSoup
import requests

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


    def get_google_search_results(self, search_term, sleep_interval=2, num_results=10, timeout=10):
        """
        Perform a Google search and store the results.

        Args:
        - search_term (str): The search term.
        - sleep_interval (int): The interval between searches. Default is 2 seconds.
        - num_results (int): Number of results to return. Default is 10.
        - timeout (int): Timeout for the request in seconds. Default is 5 seconds.
        """
        for result in search(search_term, num_results=num_results, advanced=True, timeout=timeout):
            try:
                content = requests.get(result.url, timeout=timeout).content
                page_content = BeautifulSoup(content).get_text()
                self.results.append({
                    'url': result.url,
                    'title': result.title,
                    'description': result.description,
                    'text_content': page_content,
                    'domain': tldextract.extract(result.url).domain
                })
            except requests.exceptions.Timeout:
                print(f"Request to {result.url} timed out.")

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


def google_search_interface():
    # Create an instance of the GoogleSearchSaver class
    searcher = GoogleSearchSaver()

    search_term = st.text_input('Enter search term')
    num_results = st.number_input('Enter number of results', min_value=1, max_value=50, value=10)

    if st.button('Get results'):
        with st.spinner('Getting results...'):
            # Perform the Google search
            searcher.get_google_search_results(search_term, num_results=num_results)
            # Save results to a Parquet file
            st.session_state.project_folder = 'tmp'
            searcher.store_to_db(search_term, project_folder=st.session_state.project_folder)

            # Retrieve and display the file name where results are saved
            file_name = searcher.get_file_name()
            st.success('Done.')
            st.write('Results saved to parquet file.')
            st.write(f"Data saved to {file_name}")
    return None

def tool_main(search_term="", num_results=1):
    """
    This tool performs a Google search and returns the
    content of the results.  All results are concatenated and returned as one string.

    Parameters:
    - search_term (str): The query to search with.
    - num_results (int): The number of results to return.  Default is 1.
    
    Returns (str):
    - The content of the results as one string.
    """
    searcher = GoogleSearchSaver()
    searcher.get_google_search_results(search_term, num_results=num_results)
    return searcher.get_results_as_string()